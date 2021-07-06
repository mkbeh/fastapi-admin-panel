from typing import Dict, Awaitable

from faker import Faker

from db.init_data import create_initial_roles, create_initial_superuser
from db.orm.patcher import patch_sqlalchemy_crud

from core.security import generate_token
from extra import enums

faker = Faker()

on_startup_signals = [
    patch_sqlalchemy_crud,
    create_initial_roles,
    create_initial_superuser,
]


async def get_token_headers() -> Dict:
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


def get_account_data(role: enums.Roles = enums.Roles.customer) -> Dict:
    pwd = faker.password()
    return dict(
        fullname=faker.name(),
        email=faker.company_email(),
        phone=faker.phone_number(),
        role=role,
        password=pwd,
        password2=pwd,
    )
