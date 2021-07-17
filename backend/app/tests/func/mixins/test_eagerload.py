import pytest

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from core.settings import settings
from db.mixins import EagerLoadMixin
from db.mixins.eagerload import eager_expr, JOINED, SUBQUERY
from tests.func.mixins.utils import in_tx


Base = declarative_base()
engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class BaseModel(Base, EagerLoadMixin):
    __abstract__ = True
    pass


class User(BaseModel):
    __tablename__ = "user"
    __repr_attrs__ = ["name"]
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    posts = sa.orm.relationship("Post")


class Post(BaseModel):
    __tablename__ = "post"
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"))
    archived = sa.Column(sa.Boolean, default=False)

    user = sa.orm.relationship("User")
    comments = sa.orm.relationship("Comment")


class Comment(BaseModel):
    __tablename__ = "comment"
    __repr_attrs__ = ["body"]
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"))
    post_id = sa.Column(sa.Integer, sa.ForeignKey("post.id"))
    rating = sa.Column(sa.Integer)

    user = sa.orm.relationship("User")
    post = sa.orm.relationship("Post")


@pytest.fixture(scope="function", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)


@pytest.fixture(scope="function")
async def session():
    async with in_tx(async_session) as db:
        yield db


class BaseTest:
    async def _create_initial_data(self, db):
        u1 = User(name="Bill u1")
        db.add(u1)
        await db.flush()

        u2 = User(name="Alex u2")
        db.add(u2)
        await db.flush()

        u3 = User(name="Bishop u3")
        db.add(u3)
        await db.flush()

        p11 = Post(id=11, body="1234567890123", archived=True, user=u1)
        db.add(p11)
        await db.flush()

        p12 = Post(id=12, body="1234567890", user=u1)
        db.add(p12)
        await db.flush()

        p21 = Post(id=21, body="p21 by u2", user=u2)
        db.add(p21)
        await db.flush()

        p22 = Post(id=22, body="p22 by u2", user=u2)
        db.add(p22)
        await db.flush()

        cm11 = Comment(
            id=11,
            body="cm11 to p11",
            user=u1,
            post=p11,
            rating=1,
        )
        db.add(cm11)
        await db.flush()

        cm12 = Comment(
            id=12,
            body="cm12 to p12",
            user=u2,
            post=p12,
            rating=2,
        )
        db.add(cm12)
        await db.flush()

        cm21 = Comment(
            id=21,
            body="cm21 to p21",
            user=u1,
            post=p21,
            rating=1,
        )
        db.add(cm21)
        await db.flush()

        cm22 = Comment(
            id=22,
            body="cm22 to p22",
            user=u3,
            post=p22,
            rating=3,
        )
        db.add(cm22)
        await db.flush()

        cm_empty = Comment(
            id=29,
            # no body
            # no user
            # no post
            # no rating
        )
        db.add(cm_empty)
        await db.flush()

        return u1, u2, u3, p11, p12, p21, p22, cm11, cm12, cm21, cm22, cm_empty


@pytest.mark.incremental
@pytest.mark.asyncio
@pytest.mark.usefixtures("setup_db", "session")
class TestEagerExpr(BaseTest):
    async def _test_ok(self, session, schema):
        assert self.query_count == 0

        stmt = sa.select(User).options(*eager_expr(schema)).filter_by(id=1)
        user = (await session.execute(stmt)).scalar_one()

        assert self.query_count == 2

        # now, to get relationships, NO additional query is needed
        post = user.posts[0]
        _ = post.comments[0]

        assert self.query_count == 2

    async def _create_initial_data(self, session):
        result = await super()._create_initial_data(session)

        self.query_count = 0

        @sa.event.listens_for(engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            self.query_count += 1

        return result

    async def test_ok_strings(self, session):
        await self._create_initial_data(session)

        schema = {User.posts: (SUBQUERY, {Post.comments: JOINED})}
        await self._test_ok(session, schema)

    async def test_ok_class_properties(self, session):
        await self._create_initial_data(session)

        schema = {"posts": (SUBQUERY, {"comments": JOINED})}
        await self._test_ok(session, schema)

    async def test_bad_join_method(self, session):
        # None
        schema = {"posts": None}

        with pytest.raises(ValueError):
            sa.select(User).options(*eager_expr(schema))

        # strings
        schema = {
            "posts": ("WRONG JOIN METHOD", {Post.comments: "OTHER WRONG JOIN METHOD"})
        }
        with pytest.raises(ValueError):
            sa.select(User).options(*eager_expr(schema))

        # class properties
        schema = {
            User.posts: (
                "WRONG JOIN METHOD",
                {Post.comments: "OTHER WRONG JOIN METHOD"},
            )
        }
        with pytest.raises(ValueError):
            sa.select(User).options(*eager_expr(schema))


@pytest.mark.incremental
@pytest.mark.asyncio
@pytest.mark.usefixtures("setup_db", "session")
class TestOrmWithJoinedStrings(BaseTest):
    async def _create_initial_data(self, session):
        result = await super()._create_initial_data(session)

        self.query_count = 0

        @sa.event.listens_for(engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            self.query_count += 1

        return result

    async def test(self, session):
        await self._create_initial_data(session)
        assert self.query_count == 0
        # take post with user and comments (including comment author)
        # NOTE: you can separate relations with dot.
        # Its due to SQLAlchemy: https://goo.gl/yM2DLX
        stmt = Post.with_joined("user", "comments", "comments.user")
        post = await session.scalar(stmt)

        assert self.query_count == 1

        # now, to get relationship, NO additional query is needed
        _ = post.user
        _ = post.comments[0]
        _ = post.comments[0].user

        assert self.query_count == 1


@pytest.mark.incremental
@pytest.mark.asyncio
@pytest.mark.usefixtures("setup_db", "session")
class TestOrmWithJoinedClassProperties(BaseTest):
    async def _create_initial_data(self, session):
        result = await super()._create_initial_data(session)

        self.query_count = 0

        @sa.event.listens_for(engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            self.query_count += 1

        return result

    async def test(self, session):
        await self._create_initial_data(session)
        assert self.query_count == 0

        stmt = Post.with_joined(Post.comments, Post.user)
        post = await session.scalar(stmt)

        # now, to get relationship, NO additional query is needed
        _ = post.comments[0]
        _ = post.user

        assert self.query_count == 1


@pytest.mark.incremental
@pytest.mark.asyncio
@pytest.mark.usefixtures("setup_db", "session")
class TestOrmWithSubquery(BaseTest):
    async def _create_initial_data(self, session):
        result = await super()._create_initial_data(session)

        self.query_count = 0

        @sa.event.listens_for(engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            self.query_count += 1

        return result

    async def test(self, session):
        await self._create_initial_data(session)
        assert self.query_count == 0

        # take post with user and comments (including comment author)
        # NOTE: you can separate relations with dot.
        # Its due to SQLAlchemy: https://goo.gl/yM2DLX

        stmt = Post.with_subquery("user", "comments", "comments.user")
        post = await session.scalar(stmt)

        # 3 queries were executed:
        #   1 - on posts
        #   2 - on user (eagerload subquery)
        #   3 - on comments (eagerload subquery)
        #   4 - on comments authors (eagerload subquery)

        assert self.query_count == 4

        # now, to get relationship, NO additional query is needed
        _ = post.user
        _ = post.comments[0]
        _ = post.comments[0].user

        assert self.query_count == 4


@pytest.mark.incremental
@pytest.mark.asyncio
@pytest.mark.usefixtures("setup_db", "session")
class TestOrmWithSubqueryClassProperties(BaseTest):
    async def _create_initial_data(self, session):
        result = await super()._create_initial_data(session)

        self.query_count = 0

        @sa.event.listens_for(engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            self.query_count += 1

        return result

    async def test(self, session):
        await self._create_initial_data(session)
        assert self.query_count == 0

        stmt = Post.with_subquery(Post.comments, Post.user)
        post = await session.scalar(stmt)
        # 3 queries were executed:
        #   1 - on posts
        #   2 - on comments (eagerload subquery)
        #   3 - on user (eagerload subquery)

        assert self.query_count == 3

        # now, to get relationship, NO additional query is needed
        _ = post.comments[0]
        _ = post.user

        assert self.query_count == 3


@pytest.mark.incremental
@pytest.mark.asyncio
@pytest.mark.usefixtures("setup_db", "session")
class TestOrmWithDict(BaseTest):

    async def _test_joinedload(self, schema, session):
        assert self.query_count == 0

        stmt = Post.with_(schema)
        post = await session.scalar(stmt)

        assert self.query_count == 1

        # now, to get relationship, NO additional query is needed
        _ = post.comments[0]

        assert self.query_count == 1

    async def _create_initial_data(self, session):
        result = await super()._create_initial_data(session)

        self.query_count = 0

        @sa.event.listens_for(engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            self.query_count += 1

        return result

    async def test_joinedload_strings(self, session):
        await self._create_initial_data(session)
        assert self.query_count == 0

        schema = {'comments': JOINED}
        await self._test_joinedload(schema, session)

    async def test_joinedload_class_properties(self, session):
        await self._create_initial_data(session)
        assert self.query_count == 0

        schema = {Post.comments: JOINED}
        await self._test_joinedload(schema, session)

    async def _test_subqueryload(self, schema, session):
        assert self.query_count == 0

        stmt = Post.with_(schema)
        post = await session.scalar(stmt)

        assert self.query_count == 2

        # to get relationship, NO additional query is needed
        _ = post.comments[0]

        assert self.query_count == 2

    async def test_subqueryload_strings(self, session):
        await self._create_initial_data(session)
        assert self.query_count == 0

        schema = {'comments': SUBQUERY}
        await self._test_subqueryload(schema, session)

    async def test_subqueryload_class_properties(self, session):
        await self._create_initial_data(session)
        assert self.query_count == 0

        schema = {Post.comments: SUBQUERY}
        await self._test_subqueryload(schema, session)

    async def _test_combined_load(self, schema, session):
        assert self.query_count == 0

        stmt = User.with_(schema)
        user = await session.scalar(stmt)

        assert self.query_count == 2

        # now, to get relationships, NO additional query is needed
        post = user.posts[0]
        _ = post.comments[0]

        assert self.query_count == 2

    async def test_combined_load_strings(self, session):
        await self._create_initial_data(session)
        assert self.query_count == 0

        schema = {
            User.posts: (SUBQUERY, {
                Post.comments: JOINED
            })
        }

        await self._test_combined_load(schema, session)

    async def test_combined_load_class_properties(self, session):
        await self._create_initial_data(session)
        assert self.query_count == 0

        schema = {
            'posts': (SUBQUERY, {
                'comments': JOINED
            })
        }
        await self._test_combined_load(schema, session)
