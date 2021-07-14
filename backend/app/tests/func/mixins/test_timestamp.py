import time
from datetime import datetime

import pytest
import sqlalchemy as sa
from sqlalchemy import select, insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from db.mixins import TimestampsMixin
from core.settings import settings
from tests.utils import faker
from tests.func.mixins.utils import in_tx


Base = declarative_base()
engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class BaseModel(Base, TimestampsMixin):
    """Model to use as base."""

    __abstract__ = True

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)


class User(BaseModel):
    """User model exemple."""

    __tablename__ = 'test_user'

    __mapper_args__ = {"eager_defaults": True}


@pytest.fixture(scope="class", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
        await conn.execute(
            insert(User).values(dict(name='Jonh'))
        )

    yield

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)


@pytest.mark.incremental
@pytest.mark.asyncio
class TestTimestamps:
    def test_timestamp_must_be_abstract(self):
        """Test whether TimestampsMixin is abstract."""
        assert hasattr(
            TimestampsMixin, "__abstract__"
        ), "TimestampsMixin must have attribute __abstract__"
        assert TimestampsMixin.__abstract__ is True, "__abstract__ must be True"

    async def test_timestamp_has_datetime_columns(self):
        """Test whether TimestampsMixin has attrs created_at and updated_at."""
        async with in_tx(async_session) as tx:
            user = await tx.scalar(select(User))

            assert hasattr(
                User, "created_at"
            ), "Timestamp doesn't have created_at attribute."
            assert isinstance(
                user.created_at, datetime
            ), "created_at column should be datetime"

            assert hasattr(
                User, "updated_at"
            ), "Timestamp doesn't have updated_at attribute."
            assert isinstance(
                user.updated_at, datetime
            ), "updated_at column should be datetime"

    async def test_updated_at_column_must_change_value(self):
        """Test whether updated_at value is most recently after update."""
        async with in_tx(async_session) as tx:
            user = await tx.scalar(select(User))

            dt_1 = user.updated_at
            time.sleep(0.3)

            user.name = faker.name()
            tx.add(user)
            await tx.commit()

            dt_2 = user.updated_at

        assert dt_1 < dt_2, "dt_1 should be older than dt_2"
