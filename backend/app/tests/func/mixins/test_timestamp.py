import time
from datetime import datetime

import pytest
from sqlalchemy import select

from models import Account
from db.mixins import TimestampsMixin
from tests.utils import faker


@pytest.mark.incremental
@pytest.mark.asyncio
class TestTimestamps:
    def test_timestamp_must_be_abstract(self):
        """Test whether TimestampsMixin is abstract."""
        assert hasattr(
            TimestampsMixin, "__abstract__"
        ), "TimestampsMixin must have attribute __abstract__"
        assert TimestampsMixin.__abstract__ is True, "__abstract__ must be True"

    async def test_timestamp_has_datetime_columns(self, db):
        """Test whether TimestampsMixin has attrs created_at and updated_at."""
        account = await select(Account).first(db)

        assert hasattr(
            Account, "created_at"
        ), "Timestamp doesn't have created_at attribute."
        assert isinstance(
            account.created_at, datetime
        ), "created_at column should be datetime"

        assert hasattr(
            Account, "updated_at"
        ), "Timestamp doesn't have updated_at attribute."
        assert isinstance(
            account.updated_at, datetime
        ), "updated_at column should be datetime"

    async def test_updated_at_column_must_change_value(self, db):
        """Test whether updated_at value is most recently after update."""
        await db.commit()

        account = await select(Account).first(db)
        dt_1 = account.updated_at
        time.sleep(0.3)
        await account.update(db, fullname=faker.name())

        dt_2 = account.updated_at

        assert dt_1 < dt_2, "dt_1 should be older than dt_2"
