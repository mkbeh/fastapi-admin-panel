from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql import Select

from extra.types import Paths


JOINED = "joined"
SUBQUERY = "subquery"


def eager_expr(schema: dict) -> list:
    flat_schema = _flatten_schema(schema)
    return _eager_expr_from_flat_schema(flat_schema)


def _flatten_schema(schema: dict) -> dict:
    def _flatten(schema: dict, parent_path: str, result: dict) -> None:
        for path, value in schema.items():
            # for supporting schemas like Product.user: {...},
            # we transform, say, Product.user to 'user' string
            if isinstance(path, InstrumentedAttribute):
                path = path.key

            if isinstance(value, tuple):
                join_method, inner_schema = value[0], value[1]
            elif isinstance(value, dict):
                join_method, inner_schema = JOINED, value
            else:
                join_method, inner_schema = value, None

            full_path = parent_path + "." + path if parent_path else path
            result[full_path] = join_method

            if inner_schema:
                _flatten(inner_schema, full_path, result)

    result = {}
    _flatten(schema, "", result)
    return result


def _eager_expr_from_flat_schema(flat_schema: dict) -> list:
    result = []
    for path, join_method in flat_schema.items():
        if join_method == JOINED:
            result.append(joinedload(path))
        elif join_method == SUBQUERY:
            result.append(subqueryload(path))
        else:
            raise ValueError("Bad join method `{}` in `{}`".format(join_method, path))
    return result


class EagerLoadMixin:
    __abstract__ = True

    @classmethod
    def with_(cls, schema: dict) -> Select:
        """
        Query class and eager load schema at once.

        Example:
            schema = {
                'user': JOINED, # joinedload user
                'comments': (SUBQUERY, {  # load comments in separate query
                    'user': JOINED  # but, in this separate query, join user
                })
            }
            # the same schema using class properties:
            schema = {
                Post.user: JOINED,
                Post.comments: (SUBQUERY, {
                    Comment.user: JOINED
                })
            }
            await User.with_(schema).first(db)
        """
        return select(cls).options(*eager_expr(schema or {}))

    @classmethod
    def with_joined(cls, *paths: Paths) -> Select:
        """
        Eagerload for simple cases where we need to just
         joined load some relations
        In strings syntax, you can split relations with dot
         due to this SQLAlchemy feature: https://goo.gl/yM2DLX

        Example 1:
            await Comment.with_joined('user', 'post', 'post.comments').first(db)
        Example 2:
            await Comment.with_joined(Comment.user, Comment.post).first(db)
        """
        options = [joinedload(path) for path in paths]
        return select(cls).options(*options)

    @classmethod
    def with_subquery(cls, *paths: Paths) -> Select:
        """
        Eagerload for simple cases where we need to just
         joined load some relations
        In strings syntax, you can split relations with dot
         (it's SQLAlchemy feature)

        Example 1:
            await User.with_subquery('posts', 'posts.comments').all(db)
        Example 2:
            await User.with_subquery(User.posts, User.comments).all(db)
        """
        options = [selectinload(path) for path in paths]
        return select(cls).options(*options)
