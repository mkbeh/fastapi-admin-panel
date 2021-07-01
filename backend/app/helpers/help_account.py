from sqlalchemy.ext.asyncio import AsyncSession
from models import Account, AuthorizationData


async def is_email_exists(db: AsyncSession, email: str):
    is_email = await Account.exists(email=email).scalar(db)
    is_login = await AuthorizationData.exists(login=email).scalar(db)
    return any((is_email, is_login))
