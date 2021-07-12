import pytest

from tests.utils import get_account_data
from models import Account


accounts_data = [get_account_data(exclude=['password2']) for _ in range(3)]


@pytest.mark.asyncio
@pytest.mark.parametrize('data', accounts_data)
async def test_repr(db, data):
    account = await Account.create(db, **data)
    for attr in Account.__repr_attrs__:
        assert attr in repr(account)
