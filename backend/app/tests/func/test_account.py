import pytest
from sqlalchemy import select

from models import Account, Role
from tests.utils import get_account_data, faker
from core.security import generate_confirmation_code
from extra.enums import Roles


async def _test_token(token, async_client):
    response = await async_client.get('/auth/user_is_auth', headers=dict(
        Authorization=f'Bearer {token["access_token"]}'
    ))
    assert response.status_code == 200


@pytest.mark.incremental
@pytest.mark.asyncio
class TestAccount:
    data = get_account_data()

    async def test_create_account(self, async_client):
        resp = await async_client.post('/accounts', json=get_account_data())
        assert resp.status_code == 200
        assert resp.json()['id']

    async def test_get_me(self, async_client):
        resp = await async_client.get('/accounts/me')
        assert resp.status_code == 200

    async def test_read_acccount_by_id(self, async_client, db):
        account = await select(Account).scalar(db)

        resp = await async_client.get(f'/accounts/{account.id}')
        assert resp.status_code == 200
        assert resp.json()['id'] == account.id

    async def test_update_account(self, async_client, db):
        account = await select(Account).scalar(db)
        new_data = get_account_data()

        resp = await async_client.put(f'/accounts/{account.id}', json=new_data)
        assert resp.status_code == 200
        assert resp.json()['email'] == new_data['email']
        assert resp.json()['phone'] == new_data['phone']

    async def test_read_accounts(self, async_client):
        resp = await async_client.get('/accounts/')
        assert resp.status_code == 200

    async def test_account_registration(self, async_client):
        resp = await async_client.post('/accounts/registration', json=TestAccount.data)
        assert resp.status_code == 200
        assert resp.json()['result'] is True

    async def test_confirm_account(self, async_client, db):
        account = await select(Account).filter_by(
            email=TestAccount.data['email']
        ).one(db)

        resp = await async_client.post(
            '/webhooks/confirm/account',
            json=dict(
                code=generate_confirmation_code(account_id=account.id)
            )
        )
        assert resp.status_code == 200
        token = resp.json()
        await _test_token(token, async_client)

    async def test_login(self, async_client):
        resp = await async_client.post('/auth/access-token', json=dict(
            login=TestAccount.data['email'],
            password=TestAccount.data['password']
        ))
        assert resp.status_code == 200
        TestAccount.token = resp.json()
        await _test_token(TestAccount.token, async_client)

    async def test_refresh(self, async_client):
        resp = await async_client.post('/auth/refresh-token', headers=dict(
            Authorization=f'Bearer {TestAccount.token["access_token"]}'
        ), json=dict(
            refresh_token=TestAccount.token['refresh_token']
        ))
        assert resp.status_code == 200
        token = resp.json()
        await _test_token(token, async_client)

    async def send_change_password_email(self, async_client):
        resp = await async_client.post('/accounts/change_password', json=dict(
            login=TestAccount.data['email']
        ))
        assert resp.status_code == 200

    async def test_change_password(self, async_client, db):
        account = await select(Account).filter_by(
            email=TestAccount.data['email']
        ).one(db)
        TestAccount.data.update(password=faker.password(length=12))
        resp = await async_client.post('/webhooks/change_password', json=dict(
            code=generate_confirmation_code(account_id=account.id),
            new_password=TestAccount.data['password'],
        ), headers=dict(
            Authorization=f'Bearer {TestAccount.token["access_token"]}'
        ))

        assert resp.status_code == 200
        await self.test_login(async_client)

    async def test_delete_account(self, async_client, db):
        account = await select(Account).filter(
            Account.roles.any(Role.name == Roles.customer),
        ).scalar(db)

        resp = await async_client.delete(f'/accounts/{account.id}')
        assert resp.status_code == 200
        assert resp.json()['result'] is True
