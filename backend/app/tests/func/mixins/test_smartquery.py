import pytest
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from core.settings import settings

from db.mixins import SmartQueryMixin
from db.mixins.smartquery import smart_query
from db.mixins.eagerload import JOINED, SUBQUERY

from tests.func.mixins.utils import in_tx


Base = declarative_base()
engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class BaseModel(Base, SmartQueryMixin):
    __abstract__ = True
    pass


class User(BaseModel):
    __tablename__ = "user"
    __repr_attrs__ = ["name"]
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)

    # to smart query relationship, it should be explicitly set,
    # not to be a backref
    posts = sa.orm.relationship("Post", back_populates="user")
    comments = sa.orm.relationship("Comment", back_populates="user")
    # below relationship will just return query (without executing)
    # this query can be customized
    # see http://docs.sqlalchemy.org/en/latest/orm/collections.html#dynamic-relationship
    #
    # we will use this relationship for demonstrating real-life example
    #  of how smart_query() function works (see 3.2.2)
    # this will return query
    comments_ = sa.orm.relationship("Comment", lazy="dynamic", back_populates="user")


class Post(BaseModel):
    __tablename__ = "post"
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"))
    archived = sa.Column(sa.Boolean, default=False)

    # to smart query relationship, it should be explicitly set,
    # not to be a backref
    user = sa.orm.relationship("User")
    comments = sa.orm.relationship("Comment", back_populates="post")

    @hybrid_property
    def public(self):
        return not self.archived

    @public.expression
    def public(cls):
        return ~cls.archived

    @hybrid_method
    def is_commented_by_user(cls, user, mapper=None):
        # in real apps, Comment class can be obtained from relation
        #  to avoid cyclic imports like so:
        #     Comment = cls.comments.property.argument()
        mapper = mapper or cls
        # from sqlalchemy import exists
        # return exists().where((Comment.post_id == mapper.id) & \
        #                       (Comment.user_id == user.id))
        return mapper.comments.any(Comment.user_id == user.id)

    @hybrid_method
    def is_public(cls, value, mapper=None):
        # in real apps, Comment class can be obtained from relation
        #  to avoid cyclic imports like so:
        #     Comment = cls.comments.property.argument()
        mapper = mapper or cls
        return mapper.public == value


class Comment(BaseModel):
    __tablename__ = "comment"
    __repr_attrs__ = ["body"]
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"))
    post_id = sa.Column(sa.Integer, sa.ForeignKey("post.id"))
    rating = sa.Column(sa.Integer)
    created_at = sa.Column(sa.DateTime)

    # to smart query relationship, it should be explicitly set,
    # not to be a backref
    user = sa.orm.relationship("User", back_populates="comments")
    post = sa.orm.relationship("Post", back_populates="comments")


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
            created_at=datetime(2014, 1, 1),
        )
        db.add(cm11)
        await db.flush()

        cm12 = Comment(
            id=12,
            body="cm12 to p12",
            user=u2,
            post=p12,
            rating=2,
            created_at=datetime(2015, 10, 20),
        )
        db.add(cm12)
        await db.flush()

        cm21 = Comment(
            id=21,
            body="cm21 to p21",
            user=u1,
            post=p21,
            rating=1,
            created_at=datetime(2015, 11, 21),
        )
        db.add(cm21)
        await db.flush()

        cm22 = Comment(
            id=22,
            body="cm22 to p22",
            user=u3,
            post=p22,
            rating=3,
            created_at=datetime(2016, 11, 20),
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
class TestFilterExpr(BaseTest):
    def test_filterable_attributes(self):
        assert set(User.filterable_attributes) == {
            # normal columns
            "id",
            "name",
            # relations
            "posts",
            "comments",
            "comments_",
        }
        assert "posts_viewonly" not in set(User.filterable_attributes)
        assert set(Post.filterable_attributes) == {
            # normal columns
            "id",
            "body",
            "user_id",
            "archived",
            # relations
            "user",
            "comments",
            # hybrid attributes
            "public",
            # hybrid methods
            "is_public",
            "is_commented_by_user",
        }
        assert set(Comment.filterable_attributes) == {
            # normal columns
            "id",
            "body",
            "post_id",
            "user_id",
            "rating",
            "created_at",
            # hybrid attributes
            "user",
            "post",
        }

    async def test_incorrect_expr(self, session):
        with pytest.raises(KeyError):
            stmt = sa.select(Post).filter(*Post.filter_expr(INCORRECT_ATTR="nomatter"))
            _ = (await session.execute(stmt)).scalars().all()

    async def test_columns(self, session):
        (
            u1,
            u2,
            u3,
            p11,
            p12,
            p21,
            p22,
            cm11,
            cm12,
            cm21,
            cm22,
            cm_empty,
        ) = await self._create_initial_data(session)

        # users having posts which are commented by user 2
        stmt = sa.select(Post).filter(*Post.filter_expr(user=u1))
        posts = (await session.execute(stmt)).scalars().all()

        assert set(posts) == {p11, p12}

        stmt = sa.select(Post).filter(*Post.filter_expr(user=u1, archived=False))
        posts = (await session.execute(stmt)).scalars().all()

        assert set(posts) == {p12}

    async def test_hybrid_properties(self, session):
        (
            u1,
            u2,
            u3,
            p11,
            p12,
            p21,
            p22,
            cm11,
            cm12,
            cm21,
            cm22,
            cm_empty,
        ) = await self._create_initial_data(session)

        stmt = sa.select(Post).filter(*Post.filter_expr(public=True))
        public_posts = (await session.execute(stmt)).scalars().all()
        stmt = sa.select(Post).filter(*Post.filter_expr(archived=False))
        non_archived_posts = (await session.execute(stmt)).scalars().all()

        assert public_posts == non_archived_posts

        stmt = sa.select(Post).filter(*Post.filter_expr(public=True))
        public_posts = (await session.execute(stmt)).scalars().all()

        assert set(public_posts) == {p12, p21, p22}

        stmt = sa.select(Post).filter(*Post.filter_expr(archived=False))
        non_archived_posts = (await session.execute(stmt)).scalars().all()

        assert set(non_archived_posts) == {p12, p21, p22}

    async def test_hybrid_methods(self, session):
        (
            u1,
            u2,
            u3,
            p11,
            p12,
            p21,
            p22,
            cm11,
            cm12,
            cm21,
            cm22,
            cm_empty,
        ) = await self._create_initial_data(session)

        # posts which are commented by user 1
        stmt = sa.select(Post).filter(*Post.filter_expr(is_commented_by_user=u1))
        posts = (await session.execute(stmt)).scalars().all()

        assert set(posts) == {p11, p21}

        # posts which are commented by user 2
        stmt = sa.select(Post).filter(*Post.filter_expr(is_commented_by_user=u2))
        posts = (await session.execute(stmt)).scalars().all()

        assert set(posts) == {p12}

    async def test_combinations(self, session):
        (
            u1,
            u2,
            u3,
            p11,
            p12,
            p21,
            p22,
            cm11,
            cm12,
            cm21,
            cm22,
            cm_empty,
        ) = await self._create_initial_data(session)

        # non-public posts commented by user 1
        stmt = sa.select(Post).filter(
            *Post.filter_expr(public=False, is_commented_by_user=u1)
        )
        posts = (await session.execute(stmt)).scalars().all()

        assert set(posts) == {p11}

    async def test_operators(self, session):
        (
            u1,
            u2,
            u3,
            p11,
            p12,
            p21,
            p22,
            cm11,
            cm12,
            cm21,
            cm22,
            cm_empty,
        ) = await self._create_initial_data(session)

        async def test(filters, expected_result):
            stmt = sa.select(Comment).filter(*Comment.filter_expr(**filters))
            result = (await session.execute(stmt)).scalars().all()

            assert set(result) == expected_result

        # test incorrect attribute
        with pytest.raises(KeyError):
            await test(dict(rating__INCORRECT_OPERATOR="nomatter"), {"nomatter"})

        # not
        await test(dict(id__not=11), {cm12, cm21, cm22, cm_empty})

        # rating == None
        await test(dict(rating=None), {cm_empty})
        await test(dict(rating__isnull=2), {cm_empty})

        # rating == 2
        await test(dict(rating=2), {cm12})  # when no operator, 'exact' is assumed
        await test(dict(rating__exact=2), {cm12})

        # rating != 2
        await test(dict(rating__ne=2), {cm11, cm21, cm22})

        # rating > 2
        await test(dict(rating__gt=2), {cm22})
        # rating >= 2
        await test(dict(rating__ge=2), {cm12, cm22})
        # rating < 2
        await test(dict(rating__lt=2), {cm11, cm21})
        # rating <= 2
        await test(dict(rating__le=2), {cm11, cm12, cm21})

        # rating in [1,3]
        await test(dict(rating__in=[1, 3]), {cm11, cm21, cm22})  # list
        await test(dict(rating__in=(1, 3)), {cm11, cm21, cm22})  # tuple
        await test(dict(rating__in={1, 3}), {cm11, cm21, cm22})  # set

        # rating not in [1,3]
        await test(dict(rating__notin=[1, 3]), {cm12})  # list
        await test(dict(rating__notin=(1, 3)), {cm12})  # tuple
        await test(dict(rating__notin={1, 3}), {cm12})  # set

        # rating between 2 and 3
        await test(dict(rating__between=[2, 3]), {cm12, cm22})  # list
        await test(dict(rating__between=(2, 3)), {cm12, cm22})  # set

        # likes
        await test(dict(body__like="cm12 to p12"), {cm12})
        await test(dict(body__like="%cm12%"), {cm12})
        await test(dict(body__ilike="%CM12%"), {cm12})
        await test(dict(body__startswith="cm1"), {cm11, cm12})
        await test(dict(body__istartswith="CM1"), {cm11, cm12})
        await test(dict(body__endswith="to p12"), {cm12})
        await test(dict(body__iendswith="TO P12"), {cm12})

        # dates
        # year
        await test(dict(created_at__year=2014), {cm11})
        await test(dict(created_at__year=2015), {cm12, cm21})
        # month
        await test(dict(created_at__month=1), {cm11})
        await test(dict(created_at__month=11), {cm21, cm22})
        # day
        await test(dict(created_at__day=1), {cm11})
        await test(dict(created_at__day=20), {cm12, cm22})
        # whole date
        await test(
            dict(created_at__year=2014, created_at__month=1, created_at__day=1),
            expected_result={cm11},
        )
        await test(dict(created_at=datetime(2014, 1, 1)), {cm11})

        # date comparisons
        await test(dict(created_at__year_ge=2014), {cm11, cm12, cm21, cm22})
        await test(dict(created_at__year_gt=2014), {cm12, cm21, cm22})
        await test(dict(created_at__year_le=2015), {cm11, cm12, cm21})
        await test(dict(created_at__month_lt=10), {cm11})


@pytest.mark.incremental
@pytest.mark.asyncio
@pytest.mark.usefixtures("setup_db", "session")
class TestOrderExpr(BaseTest):
    async def test_incorrect_expr(self):
        with pytest.raises(KeyError):
            _ = sa.select(Post).filter(*Post.order_expr("INCORRECT_ATTR"))

        with pytest.raises(KeyError):
            _ = sa.select(Post).filter(*Post.order_expr("*body"))

    async def test_asc(self, session):
        (
            u1,
            u2,
            u3,
            p11,
            p12,
            p21,
            p22,
            cm11,
            cm12,
            cm21,
            cm22,
            cm_empty,
        ) = await self._create_initial_data(session)

        stmt = sa.select(Comment).order_by(*Comment.order_expr("rating"))
        comments = (await session.execute(stmt)).scalars().all()

        assert comments[-1] == cm_empty
        # cm11 and cm21 have equal ratings, so they can occur in any order
        assert set(comments[0:2]) == {cm11, cm21}
        assert comments[2:4] == [cm12, cm22]

    async def test_desc(self, session):
        (
            u1,
            u2,
            u3,
            p11,
            p12,
            p21,
            p22,
            cm11,
            cm12,
            cm21,
            cm22,
            cm_empty,
        ) = await self._create_initial_data(session)

        stmt = sa.select(Comment).order_by(*Comment.order_expr("-rating"))
        comments = (await session.execute(stmt)).scalars().all()

        assert comments[1:3] == [cm22, cm12]
        # cm11 and cm21 have equal ratings, so they can occur in any order
        assert set(comments[3:]) == {cm11, cm21}
        assert comments[0] == cm_empty

    async def test_hybrid_properties(self, session):
        (
            u1,
            u2,
            u3,
            p11,
            p12,
            p21,
            p22,
            cm11,
            cm12,
            cm21,
            cm22,
            cm_empty,
        ) = await self._create_initial_data(session)

        stmt = sa.select(Post).order_by(*Post.order_expr("public"))
        posts = (await session.execute(stmt)).scalars().all()

        assert posts[0] == p11

        stmt = sa.select(Post).order_by(*Post.order_expr("-public"))
        posts = (await session.execute(stmt)).scalars().all()

        assert posts[-1] == p11

    async def test_combinations(self, session):
        (
            u1,
            u2,
            u3,
            p11,
            p12,
            p21,
            p22,
            cm11,
            cm12,
            cm21,
            cm22,
            cm_empty,
        ) = await self._create_initial_data(session)

        """ test various combinations """

        # 1. rating ASC, created_at ASC
        stmt = sa.select(Comment).order_by(*Comment.order_expr("rating", "created_at"))
        comments = (await session.execute(stmt)).scalars().all()

        assert comments == [cm11, cm21, cm12, cm22, cm_empty]

        # 2. rating ASC, created_at DESC
        stmt = sa.select(Comment).order_by(*Comment.order_expr("rating", "-created_at"))
        comments = (await session.execute(stmt)).scalars().all()

        assert comments == [cm21, cm11, cm12, cm22, cm_empty]

        # 3. rating DESC, created_at ASC
        stmt = sa.select(Comment).order_by(*Comment.order_expr("-rating", "created_at"))
        comments = (await session.execute(stmt)).scalars().all()

        assert comments == [cm_empty, cm22, cm12, cm11, cm21]

        # 4. rating DESC, created_at DESC
        stmt = sa.select(Comment).order_by(
            *Comment.order_expr("-rating", "-created_at")
        )
        comments = (await session.execute(stmt)).scalars().all()

        assert comments == [cm_empty, cm22, cm12, cm21, cm11]


@pytest.mark.incremental
@pytest.mark.asyncio
@pytest.mark.usefixtures("setup_db", "session")
class TestSmartQueryFilters(BaseTest):
    async def test_incorrect_expr(self):
        with pytest.raises(KeyError):
            _ = User.where(INCORRECT_ATTR="nomatter")

    async def test_is_a_shortcut_to_filter_expr_in_simple_cases(self, session):
        """test when have no joins, where() is a shortcut for filter_expr"""
        stmt = sa.select(Comment).filter(
            *Comment.filter_expr(rating__gt=2, body__startswith="cm1")
        )
        comments_filters_expr = (await session.execute(stmt)).scalars().all()

        stmt = Comment.where(rating__gt=2, body__startswith="cm1")
        comments_where = (await session.execute(stmt)).scalars().all()

        assert comments_filters_expr == comments_where

    async def test_is_a_shortcut_to_smart_query(self, session):
        """test that where() is just a shortcut for smart_query()"""
        comments_where = (
            (await session.execute(Comment.where(rating__gt=2))).scalars().all()
        )

        comments_smart_query = (
            (await session.execute(Comment.smart_query(filters=dict(rating__gt=2))))
            .scalars()
            .all()
        )

        assert comments_where == comments_smart_query

    async def test_incorrect_relation_name(self):
        with pytest.raises(KeyError):
            _ = User.where(INCORRECT_RELATION="nomatter").all()

        with pytest.raises(KeyError):
            _ = User.where(post___INCORRECT_RELATION="nomatter").all()

    async def test_relations(self, session):
        (
            u1,
            u2,
            u3,
            p11,
            p12,
            p21,
            p22,
            cm11,
            cm12,
            cm21,
            cm22,
            cm_empty,
        ) = await self._create_initial_data(session)

        # users having posts which are commented by user 2
        comments = (
            (await session.execute(User.where(posts___comments___user_id=u2.id)))
            .unique()
            .scalars()
            .all()
        )
        assert set(comments) == {u1}

        # comments where user name starts with 'Bi'
        comments = (
            (await session.execute(Comment.where(user___name__startswith="Bi")))
            .unique()
            .scalars()
            .all()
        )
        assert set(comments) == {cm11, cm21, cm22}

        # comments on posts where author name starts with 'Bi'
        # !! ATTENTION !!
        # about Comment.post:
        #  although we have Post.comments relationship,
        #   it's important to **add relationship Comment.post** too,
        #   not just use backref !!!
        comments = (
            (await session.execute(Comment.where(post___user___name__startswith="Bi")))
            .unique()
            .scalars()
            .all()
        )

        assert set(comments) == {cm11, cm12}

    async def test_combinations(self, session):
        (
            u1,
            u2,
            u3,
            p11,
            p12,
            p21,
            p22,
            cm11,
            cm12,
            cm21,
            cm22,
            cm_empty,
        ) = await self._create_initial_data(session)

        # non-public posts commented by user 1
        comments = (
            (await session.execute(Post.where(public=False, is_commented_by_user=u1)))
            .unique()
            .scalars()
            .all()
        )

        assert set(comments) == {p11}


@pytest.mark.incremental
@pytest.mark.asyncio
@pytest.mark.usefixtures("setup_db", "session")
class TestSmartQuerySort(BaseTest):
    def test_incorrect_expr(self):
        with pytest.raises(KeyError):
            _ = Post.sort("INCORRECT_ATTR")

        with pytest.raises(KeyError):
            _ = Post.sort("*body")

    async def test_is_a_shortcut_to_order_expr_in_simple_cases(self, session):
        """when have no joins, sort() is a shortcut for order_expr"""
        comments_order_expr = (
            (
                await session.execute(
                    sa.select(Comment).order_by(*Comment.order_expr("rating"))
                )
            )
            .unique()
            .scalars()
            .all()
        )
        comments_sort = (
            (await session.execute(Comment.sort("rating"))).unique().scalars().all()
        )

        assert comments_order_expr == comments_sort

        comments_order_expr = (
            (
                await session.execute(
                    sa.select(Comment).order_by(
                        *Comment.order_expr("rating", "created_at")
                    )
                )
            )
            .unique()
            .scalars()
            .all()
        )
        comments_sort = (
            (await session.execute(Comment.sort("rating", "created_at")))
            .unique()
            .scalars()
            .all()
        )

        assert comments_order_expr == comments_sort

        # hybrid properties
        posts_order_expr = (
            (
                await session.execute(
                    sa.select(Post).order_by(*Post.order_expr("public"))
                )
            )
            .unique()
            .scalars()
            .all()
        )
        posts_sort = (
            (await session.execute(Post.sort("public"))).unique().scalars().all()
        )

        assert posts_order_expr == posts_sort

    async def test_is_a_shortcut_to_smart_query(self, session):
        """test that sort() is just a shortcut for smart_query()"""
        comments_sort = (
            (await session.execute(Comment.sort("rating"))).unique().scalars().all()
        )
        comments_smart_query = (
            (await session.execute(Comment.smart_query(sort_attrs=["rating"])))
            .unique()
            .scalars()
            .all()
        )

        assert comments_sort == comments_smart_query

    def test_incorrect_relation_name(self):
        with pytest.raises(KeyError):
            _ = User.sort("INCORRECT_RELATION")

        with pytest.raises(KeyError):
            _ = User.sort("post___INCORRECT_RELATION")

    async def test_relations(self, session):
        """test that sort() is just a shortcut for smart_query()"""
        (
            u1,
            u2,
            u3,
            p11,
            p12,
            p21,
            p22,
            cm11,
            cm12,
            cm21,
            cm22,
            cm_empty,
        ) = await self._create_initial_data(session)

        comments = (
            (await session.execute(Comment.sort("user___name")))
            .unique()
            .scalars()
            .all()
        )

        assert comments[:2], [cm_empty, cm12]
        assert set(comments[1:3]) == {cm11, cm21}
        assert comments[3] == cm22

        comments = (
            (await session.execute(Comment.sort("user___name", "-created_at")))
            .unique()
            .scalars()
            .all()
        )

        assert comments == [cm12, cm21, cm11, cm22, cm_empty]

        # hybrid_property
        comments = (
            (
                await session.execute(
                    Comment.sort("-post___public", "post___user___name")
                )
            )
            .unique()
            .scalars()
            .all()
        )

        # posts by same user
        assert set(comments[1:3]) == {cm21, cm22}
        assert comments[2:], [cm12, cm11, cm_empty]


@pytest.mark.incremental
@pytest.mark.asyncio
@pytest.mark.usefixtures("setup_db", "session")
class TestFullSmartQuery(BaseTest):
    async def test_schema_with_strings(self, session):
        (
            u1,
            u2,
            u3,
            p11,
            p12,
            p21,
            p22,
            cm11,
            cm12,
            cm21,
            cm22,
            cm_empty,
        ) = await self._create_initial_data(session)

        # standalone function
        stmt = smart_query(
            Comment,
            filters={"post___public": True, "user__isnull": False},
            sort_attrs=["user___name", "-created_at"],
            schema={"post": {"user": JOINED}},
        )
        comments = (await session.execute(stmt)).unique().scalars().all()

        assert comments == [cm12, cm21, cm22]

        # class method
        stmt = Comment.smart_query(
            filters={"post___public": True, "user__isnull": False},
            sort_attrs=["user___name", "-created_at"],
            schema={"post": {"user": JOINED}},
        )
        comments = (await session.execute(stmt)).unique().scalars().all()

        assert comments == [cm12, cm21, cm22]

    async def test_schema_with_class_properties(self, session):
        (
            u1,
            u2,
            u3,
            p11,
            p12,
            p21,
            p22,
            cm11,
            cm12,
            cm21,
            cm22,
            cm_empty,
        ) = await self._create_initial_data(session)

        # standalone function
        stmt = smart_query(
            Comment,
            filters={"post___public": True, "user__isnull": False},
            sort_attrs=["user___name", "-created_at"],
            schema={Comment.post: {Post.user: JOINED}},
        )
        comments = (await session.execute(stmt)).unique().scalars().all()

        assert comments == [cm12, cm21, cm22]

        # class method
        stmt = Comment.smart_query(
            filters={"post___public": True, "user__isnull": False},
            sort_attrs=["user___name", "-created_at"],
            schema={Comment.post: {Post.user: JOINED}},
        )
        comments = (await session.execute(stmt)).unique().scalars().all()

        assert comments == [cm12, cm21, cm22]


@pytest.mark.incremental
@pytest.mark.asyncio
@pytest.mark.usefixtures("setup_db", "session")
class TestSmartQueryAutoEagerLoad(BaseTest):
    """
    Smart_query does auto-joins for filtering/sorting,
    so there's a sense to tell sqlalchemy that we alreeady joined that relation
    So we test that relations are set to be joinedload
     if they were used in smart_query()
    """

    async def _create_initial_data(self, session):
        result = await super()._create_initial_data(session)

        self.query_count = 0

        @sa.event.listens_for(engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            self.query_count += 1

        return result

    async def test_sort(self, session):
        (
            u1,
            u2,
            u3,
            p11,
            p12,
            p21,
            p22,
            cm11,
            cm12,
            cm21,
            cm22,
            cm_empty,
        ) = await self._create_initial_data(session)

        self.query_count = 0

        comments = (
            (
                await session.execute(
                    Comment.sort("-post___public", "post___user___name")
                )
            )
            .unique()
            .scalars()
            .all()
        )

        assert self.query_count == 1

        _ = comments[0].post
        # no additional query needed: we used 'post' relation in smart_query()
        assert self.query_count == 1

        _ = comments[1].post.user
        # no additional query needed: we used 'post' relation in smart_query()
        assert self.query_count == 1

    async def test_where(self, session):
        (
            u1,
            u2,
            u3,
            p11,
            p12,
            p21,
            p22,
            cm11,
            cm12,
            cm21,
            cm22,
            cm_empty,
        ) = await self._create_initial_data(session)

        self.query_count = 0

        comments = (
            (
                await session.execute(
                    Comment.where(post___public=True, post___user___name__like="Bi%")
                )
            )
            .unique()
            .scalars()
            .all()
        )

        assert self.query_count == 1

        _ = comments[0].post
        # no additional query needed: we used 'post' relation in smart_query()
        assert self.query_count == 1

        _ = comments[0].post.user
        # no additional query needed: we used 'post' relation in smart_query()
        assert self.query_count == 1

    async def test_explicitly_set_in_schema_joinedload(self, session):
        """
        here we explicitly set in schema that we additionally want to load
         post___comments
        """
        (
            u1,
            u2,
            u3,
            p11,
            p12,
            p21,
            p22,
            cm11,
            cm12,
            cm21,
            cm22,
            cm_empty,
        ) = await self._create_initial_data(session)

        self.query_count = 0

        stmt = Comment.smart_query(
            filters=dict(post___public=True, post___user___name__like="Bi%"),
            schema={"post": {"comments": JOINED}},
        )
        comments = (await session.execute(stmt)).unique().scalars().all()

        assert self.query_count == 1

        _ = comments[0].post
        # no additional query needed: we used 'post' relation in smart_query()
        assert self.query_count == 1

        _ = comments[0].post.user
        # no additional query needed: we used 'post' relation in smart_query()
        assert self.query_count == 1

    async def test_explicitly_set_in_schema_subqueryload(self, session):
        """
        here we explicitly set in schema that we additionally want to load
         post___comments
        """
        (
            u1,
            u2,
            u3,
            p11,
            p12,
            p21,
            p22,
            cm11,
            cm12,
            cm21,
            cm22,
            cm_empty,
        ) = await self._create_initial_data(session)

        self.query_count = 0

        stmt = Comment.smart_query(
            filters=dict(post___public=True, post___user___name__like="Bi%"),
            schema={"post": {"comments": SUBQUERY}},
        )
        comments = (await session.execute(stmt)).unique().scalars().all()

        assert self.query_count == 2

        _ = comments[0].post
        # no additional query needed: we used 'post' relation in smart_query()
        assert self.query_count == 2

        _ = comments[0].post.user
        # no additional query needed: we used 'post' relation in smart_query()
        assert self.query_count == 2

        # we didn't use post___comments,
        # BUT we explicitly set it in schema!
        # so additional query is NOT needed
        _ = comments[0].post.comments
        assert self.query_count == 2

    async def test_override_eagerload_method_in_schema(self, session):
        """
        here we use 'post' relation in filters,
        but we want to load 'post' relation in SEPARATE QUERY (subqueryload)
        so we set load method in schema
        """
        (
            u1,
            u2,
            u3,
            p11,
            p12,
            p21,
            p22,
            cm11,
            cm12,
            cm21,
            cm22,
            cm_empty,
        ) = await self._create_initial_data(session)

        self.query_count = 0

        stmt = Comment.smart_query(
            filters=dict(post___public=True, post___user___name__like="Bi%"),
            schema={"post": SUBQUERY},
        )
        comments = (await session.execute(stmt)).unique().scalars().all()

        assert self.query_count == 2

        _ = comments[0].post
        # no additional query needed: we used 'post' relation in smart_query()
        assert self.query_count == 2

        # Test nested schemas
        self.query_count = 0

        stmt = Comment.smart_query(
            filters=dict(post___public=True, post___user___name__like="Bi%"),
            schema={
                "post": (
                    SUBQUERY,
                    {  # This should load in a separate query
                        "user": SUBQUERY  # This should also load in a separate query
                    },
                )
            },
        )
        comments = (await session.execute(stmt)).unique().scalars().all()

        assert self.query_count == 3

        _ = comments[0].post
        # no additional query needed: we used 'post' relation in smart_query()
        assert self.query_count == 3
