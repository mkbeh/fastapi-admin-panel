"""Demonstrates how to use AllFeaturesMixin with patched SQLAlchemy."""

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from db.mixins import AllFeaturesMixin
from core.settings import settings

from tests.func.mixins.utils import in_tx


Base = declarative_base()
engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class BaseModel(Base, AllFeaturesMixin):
    __abstract__ = True
    pass


class User(BaseModel):
    __tablename__ = 'user'
    __repr_attrs__ = ['name']

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)


class Post(BaseModel):
    __tablename__ = 'post'
    __repr_attrs__ = ['body', 'user']

    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    rating = sa.Column(sa.Integer)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))

    # we use this relation in smart_query, so it should be explicitly set
    # (not just a backref from User class)
    user = sa.orm.relationship('User', backref='posts') # but for eagerload
                                                        # backref is OK
    comments = sa.orm.relationship('Comment')


class Comment(BaseModel):
    __tablename__ = 'comment'

    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    post_id = sa.Column(sa.Integer, sa.ForeignKey('post.id'))
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))

    post = sa.orm.relationship('Post')
    user = sa.orm.relationship('User')


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
class TestORM:

    async def test_all(self, db):
        bob = await User.create(db, name='bob')
        bill = await User.create(db, name='Bill')
        comment1 = await Comment.create(db, body='cool!', user=bob)
        comment2 = await Comment.create(db, body='cool2!!!!', user=bill)
        post1 = await Post.create(
            db=db,
            body='Post 1',
            user=bob,
            rating=3,
            comments=[comment2]
        )
        post2 = await Post.create(
            db=db,
            body='long-long-long-long-long body',
            rating=2,
            user=bill,
            comments=[comment1]
        )

        # filter using operators like 'in' and 'contains' and relations like 'user'
        # will output this beauty: <Post #1 body:'Post1' user:'Bill'>
        result = await Post.where(
            rating__in=[2, 3, 4],
            user___name__like='%Bi%'
        ).first(db)

        assert result == post2
        assert result.user == bill

        # joinedload post and user
        result = await Comment\
            .sort('-id')\
            .with_joined('user', 'post', 'post.comments')\
            .first(db)

        assert result == comment2
        assert result.user == bill
        assert result.post == post1
        assert result.post.comments == [comment2]

        # subqueryload posts and their comments
        result = await User.with_subquery('posts', 'posts.comments').first(db)

        assert result == bob
        assert result.posts == [post1]
        assert result.posts[0].comments == [comment2]

        # sort by rating DESC, user name ASC
        result = await Post.sort('-rating', 'user___name').all(db)

        assert result == [post1, post2]
