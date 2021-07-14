import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from db.mixins import InspectionMixin
from core.settings import settings


Base = declarative_base()
engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)



class BaseModel(Base, InspectionMixin):
    __abstract__ = True
    pass


class User(BaseModel):
    __tablename__ = 'user'
    id = sa.Column(sa.Integer, primary_key=True)
    first_name = sa.Column(sa.String)
    last_name = sa.Column(sa.String)

    posts = sa.orm.relationship('Post', backref='user')
    posts_viewonly = sa.orm.relationship('Post', viewonly=True)

    @hybrid_property
    def surname(self):
        return self.last_name

    @surname.expression
    def surname(cls):
        return cls.last_name

    @hybrid_method
    def with_first_name(cls):
        return cls.first_name != None


class Post(BaseModel):
    __tablename__ = 'post'
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))


class Parent(BaseModel):
    __tablename__ = 'parent'
    id = sa.Column(sa.Integer, primary_key=True)


class Child(Parent):
    some_prop = sa.Column(sa.String)


class ModelWithTwoPks(BaseModel):
    __tablename__ = 'two_pks'
    pk1 = sa.Column(sa.Integer, primary_key=True)
    pk2 = sa.Column(sa.Integer, primary_key=True)


@pytest.fixture(scope="module", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)


def test_columns():
    assert set(User.columns) == {'id', 'first_name', 'last_name'}
    assert set(Post.columns) == {'id', 'body', 'user_id'}


def test_nested_columns():
    assert set(Parent.columns) == {'id'}
    assert set(Child.columns), {'id', 'some_prop'}


def test_primary_keys():
    assert set(User.primary_keys) == {'id'}
    assert set(ModelWithTwoPks.primary_keys) == {'pk1', 'pk2'}


def test_relations():
    assert set(User.relations) == {'posts', 'posts_viewonly'}
    # backref also works!
    assert set(Post.relations) == {'user'}


def test_settable_relations():
    assert set(User.settable_relations) == {'posts'}


def test_hybrid_attributes():
    assert set(User.hybrid_properties) == {'surname'}
    assert Post.hybrid_properties == []


def test_hybrid_methods():
    assert set(User.hybrid_methods) == {'with_first_name'}
    assert Post.hybrid_methods == []
