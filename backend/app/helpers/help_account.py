from sqlalchemy.ext.asyncio import AsyncSession
from models import Account, AuthorizationData


async def is_email_exists(db: AsyncSession, email: str) -> bool:
    is_email = await Account.exists(db, email=email)
    is_login = await AuthorizationData.exists(db, login=email)
    return any((is_email, is_login))
