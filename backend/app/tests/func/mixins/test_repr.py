import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from db.mixins import ReprMixin
from core.settings import settings
from tests.utils import faker
from tests.func.mixins.utils import in_tx


Base = declarative_base()
engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class BaseModel(Base, ReprMixin):
    """Model to use as base."""

    __abstract__ = True

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)


class User(BaseModel):
    """User model exemple."""

    __tablename__ = 'test_user'
    __repr_attrs__ = ['name']

    __mapper_args__ = {"eager_defaults": True}


@pytest.fixture(scope="module", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)


users_data = [{'name': faker.name()} for _ in range(3)]


@pytest.mark.asyncio
@pytest.mark.parametrize('data', users_data)
async def test_repr(data):
    async with in_tx(async_session) as db:
        user = User(**data)
        db.add(user)
        await db.commit()

        for attr in User.__repr_attrs__:
            val = getattr(user, attr)
            assert val[:User.__repr_max_length__] in repr(user)
