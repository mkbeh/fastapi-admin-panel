from typing import Awaitable

from faker import Faker

from db.init_data import create_initial_roles, create_initial_superuser
from db.orm.patcher import patch_sqlalchemy_crud
from db.model import Model
from db.sessions import engine

from core.security import generate_token
from extra import enums

faker = Faker()

on_startup_signals = [
    patch_sqlalchemy_crud,
    create_initial_roles,
]


async def get_token_headers() -> dict:
    for func in on_startup_signals:
        # startup initial signals
        result = func()
        if isinstance(result, Awaitable):
            await result

    superuser = await create_initial_superuser()

    token = generate_token(superuser.id)
    return dict(
        Authorization=f"Bearer {token.access_token}",
        token_type="access",
        accept="application/json",
    )


async def clear_db():
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.drop_all)
        await conn.run_sync(Model.metadata.create_all)


def get_account_data(
    role: enums.Roles = enums.Roles.customer,
    exclude: list[str] = None,
) -> dict:
    pwd = faker.password()
    data = dict(
        fullname=faker.name(),
        email=faker.company_email(),
        phone=faker.phone_number(),
        role=role,
        password=pwd,
        password2=pwd,
    )

    if exclude:
        for field in exclude:
            del data[field]

    return data
