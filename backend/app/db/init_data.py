from datetime import datetime

import models
from core.settings import settings
from extra import enums

from .sessions import in_transaction


async def create_initial_roles():
    async with in_transaction() as db:
        for role in enums.Roles:
            await models.Role.get_or_create(db, guid=role.name, name=role.value)


async def create_initial_superuser():
    async with in_transaction() as db:
        auth_data = await models.AuthorizationData\
            .where(
                login=settings.FIRST_SUPERUSER_LOGIN,
                registration_type=enums.RegistrationTypes.forms,
            )\
            .with_joined('account')\
            .one_or_none(db)

        if auth_data:
            if not auth_data.is_confirmed:
                await auth_data.update(db, confirmed_at=datetime.utcnow())
            account = auth_data.account
        else:
            account = await models.Account.create(
                db=db,
                skip_confirmation=True,
                role=enums.Roles.admin,
                email=settings.FIRST_SUPERUSER_LOGIN,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                phone="78887777777",
            )
        return account
