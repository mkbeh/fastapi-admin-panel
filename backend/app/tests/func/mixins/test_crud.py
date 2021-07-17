import pytest
import sqlalchemy as sa
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from db.mixins import CRUDMixin, SmartQueryMixin
from core.settings import settings

from tests.utils import faker
from tests.func.mixins.utils import in_tx


Base = declarative_base()
engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(scope="module", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)


@pytest.fixture(scope="class")
async def db():
    async with in_tx(async_session) as db:
        yield db


class BaseModel(Base, CRUDMixin, SmartQueryMixin):
    __abstract__ = True
    pass


class User(BaseModel):
    __tablename__ = 'user'
    __repr_attrs__ = ['name']
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    posts = sa.orm.relationship('Post', backref='user')
    posts_viewonly = sa.orm.relationship('Post', viewonly=True)


class Post(BaseModel):
    __tablename__ = 'post'
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    archived = sa.Column(sa.Boolean, default=False)

    # user = backref from User.post
    comments = sa.orm.relationship('Comment', backref='post')

    @hybrid_property
    def public(self):
        return not self.archived

    @public.setter
    def public(self, public):
        self.archived = not public


class Comment(BaseModel):
    __tablename__ = 'comment'
    __repr_attrs__ = ['body']
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    post_id = sa.Column(sa.Integer, sa.ForeignKey('post.id'))

    user = sa.orm.relationship('User', backref='comments')
    # post = backref from Post.comments


users_data = [{'name': faker.name()} for _ in range(3)]


@pytest.mark.incremental
@pytest.mark.asyncio
class TestTimestamps:
    def test_settable_attributes(self):
        assert set(User.settable_attributes) == {
            'id', 'name',  # normal columns,
            'posts', 'comments'  # relations
        }
        assert 'posts_viewonly' not in set(User.settable_attributes)
        assert set(Post.settable_attributes) == {
            'id', 'body', 'user_id', 'archived',    # normal columns
            'user', 'comments',  # relations
            'public'  # hybrid attributes
        }
        assert set(Comment.settable_attributes) == {
            'id', 'body', 'post_id', 'user_id',  # normal columns
            'user', 'post'  # hybrid attributes
        }

    async def test_fill_and_save(self, db):
        u1 = User()
        u1.fill(name=faker.name())
        await u1.save(db)

        assert u1 == await db.scalar(sa.select(User))

        p11 = Post()
        p11.fill(body=faker.name(), user=u1, public=False)
        await p11.save(db)

        assert p11 == await db.scalar(sa.select(Post))
        assert p11.archived is True

    async def test_create(self, db):
        u1 = await User.create(db, name=faker.name())
        assert u1 == await db.scalar(sa.select(User).filter_by(name=u1.name))

        p11 = await Post.create(db, body=faker.name(), user=u1, public=False)
        assert p11 == await db.scalar(sa.select(Post).filter_by(body=p11.body))
        assert p11.archived is True

    @pytest.mark.parametrize('data', users_data)
    async def test_update(self, db, data):
        user = await User.create(db, **data)
        user = await db.get(User, user.id)

        new_user = await user.update(db, name=faker.name())

        assert user.name == new_user.name


    async def test_fill_wrong_attribute(self, db):
        user = await User.create(db, name=faker.name())

        with pytest.raises(KeyError):
            user.fill(INCORRECT_ATTRUBUTE='nomatter')

        with pytest.raises(KeyError):
            await user.update(db, INCORRECT_ATTRUBUTE='nomatter')

        with pytest.raises(KeyError):
            await User.create(db, INCORRECT_ATTRUBUTE='nomatter')

    async def test_find(self, db):
        user = await User.create(db, name=faker.name())
        assert user == await User.find(db, id=user.id)

        with pytest.raises(NoResultFound):
            await User.find(db, id=100_000_000)

        assert await User.find_or_none(db, id=100_000_000) is None

    async def test_exists(self, db):
        """Test CRUD exists (require SmartQueryMixin)."""
        user = await User.create(db, name=faker.name())
        assert await User.exists(db, id=user.id, name=user.name) is True
        assert await User.exists(db, id=user.id, name='nomatter') is False

    async def test_get_or_create(self, db):
        name = faker.name()
        user, is_created = await User.get_or_create(db, name=name)
        assert is_created is True
        user, is_created = await User.get_or_create(db, name=name)
        assert is_created is False

    async def test_update_or_create(self, db):
        user, is_created = await User.update_or_create(db, name=faker.name())
        assert is_created is True

        user, is_created = await User.update_or_create(db, id=user.id)
        assert is_created is False
