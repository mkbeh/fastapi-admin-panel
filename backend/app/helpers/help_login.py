import errors
from models import Account
from core.security import verify_password


async def authenticate(*, email: str, password: str) -> int:
    account = None
    if not verify_password(password, account.hashed_password):
        raise errors.LoginError
    return account.id
