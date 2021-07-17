import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from db.mixins import SerializeMixin
from core.settings import settings
from tests.func.mixins.utils import in_tx


Base = declarative_base()
engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class BaseModel(Base, SerializeMixin):
    __abstract__ = True
    pass


class User(BaseModel):
    __tablename__ = 'user'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    password = sa.Column(sa.String)

    posts = sa.orm.relationship('Post', back_populates="user")


class Post(BaseModel):
    __tablename__ = 'post'

    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    archived = sa.Column(sa.Boolean, default=False)

    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    user = sa.orm.relationship('User')
    comments = sa.orm.relationship('Comment', back_populates="post")

    @hybrid_property
    def comments_count(self):
        return len(self.comments)


class Comment(BaseModel):
    __tablename__ = 'comment'

    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    rating = sa.Column(sa.Integer)

    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    user = sa.orm.relationship('User')
    post_id = sa.Column(sa.Integer, sa.ForeignKey('post.id'))
    post = sa.orm.relationship('Post')


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


@pytest.mark.incremental
@pytest.mark.asyncio
class TestSerialize:
    async def _create_inital_data(self, db):
        user_1 = User(name='Bill u1', id=1, password='pass1')
        db.add(user_1)
        await db.commit()

        user_2 = User(name='Alex u2', id=2, password='pass2')
        db.add(user_2)
        await db.commit()

        post_11 = Post(
            id=11,
            body='Post 11 body.',
            archived=True
        )
        post_11.user = user_1
        db.add(post_11)
        await db.commit()

        comment_11 = Comment(
            id=11,
            body='Comment 11 body',
            user=user_1,
            post=post_11,
            rating=1
        )
        db.add(comment_11)
        await db.commit()

    async def test_serialize_single(self, db):
        await self._create_inital_data(db)

        result = (
            await db.scalar(sa.select(User))
        ).as_dict(exclude=['password'])
        expected = {
            'id': 1,
            'name': 'Bill u1'
        }

        assert result == expected

    async def test_serialize_list(self, db):
        result = await db.execute(sa.select(User))
        result = [user.as_dict(exclude=['password']) for user in result.scalars().all()]

        expected = [
            {
                'id': 1,
                'name': 'Bill u1'
            },
            {
                'id': 2,
                'name': 'Alex u2'
            },
        ]

        assert expected == result

    async def test_serialize_nested(self, db):
        stmt = sa.select(Post) \
            .join(Post.comments) \
            .options(
                sa.orm.joinedload(Post.comments)
            )\
            .join(Post.user)\
            .options(
                sa.orm.joinedload(Post.user)
            )

        result = (
            await db.execute(stmt)
        ).scalars().first().as_dict(nested=True)

        expected = {
            'id': 11,
            'body': 'Post 11 body.',
            'archived': True,
            'user_id': 1,
            'user': {
                'id': 1,
                'name': 'Bill u1',
                'password': 'pass1'
            },
            'comments': [
                {
                    'id': 11,
                    'body': 'Comment 11 body',
                    'user_id': 1,
                    'post_id': 11,
                    'rating': 1,
                }
            ]
        }

        assert expected == result

    async def test_serialize_single_with_hybrid(self, db):
        stmt = sa.select(Post) \
            .join(Post.comments) \
            .options(
                sa.orm.joinedload(Post.comments)
            )\
            .join(Post.user)\
            .options(
                sa.orm.joinedload(Post.user)
            )

        result = (
            await db.execute(stmt)
        ).scalars().first().as_dict(nested=True, hybrid_attributes=True)

        expected = {
            'id': 11,
            'body': 'Post 11 body.',
            'archived': True,
            'user_id': 1,
            'comments_count': 1,
            'user': {
                'id': 1,
                'name': 'Bill u1',
                'password': 'pass1'
            },
            'comments': [
                {
                    'id': 11,
                    'body': 'Comment 11 body',
                    'user_id': 1,
                    'post_id': 11,
                    'rating': 1,
                }
            ]
        }

        assert expected == result
