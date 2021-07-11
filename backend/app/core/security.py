import string
import secrets
from typing import Optional
from datetime import timedelta, datetime

import itsdangerous.exc
from jose import jwt
from pydantic import ValidationError
from itsdangerous import URLSafeTimedSerializer
from passlib.context import CryptContext

import errors
import schemas
from extra import enums
from core.settings import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

signer = URLSafeTimedSerializer(settings.AUTH_SECRET_KEY)

alphabet = string.ascii_letters + string.digits


def generate_password(length: int = 20) -> str:
    return "".join(secrets.choice(alphabet) for _ in range(length))


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def generate_token(account_id: int) -> schemas.AuthToken:
    sub = str(account_id)
    now = datetime.utcnow()

    return schemas.AuthToken(
        access_token=encode_token(
            sub=sub,
            purpose=enums.TokenPurpose.access,
            exp=now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        ),
        refresh_token=encode_token(
            sub=sub,
            purpose=enums.TokenPurpose.refresh,
            exp=now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
        ),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def encode_token(**params):
    return jwt.encode(params, settings.AUTH_SECRET_KEY, algorithm=jwt.ALGORITHMS.HS256)


def decode_token(token: str, purpose: enums.TokenPurpose) -> schemas.AuthTokenPayload:
    try:
        payload = jwt.decode(
            token, settings.AUTH_SECRET_KEY, algorithms=[jwt.ALGORITHMS.HS256]
        )
        if payload["purpose"] != purpose:
            raise errors.BadToken
        return schemas.AuthTokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise errors.TokenExpired
    except (jwt.JWTError, ValidationError):
        raise errors.BadToken


def generate_confirmation_code(**params) -> str:
    return signer.dumps(params)


def verify_confirmation_code(code: str, *fields: str) -> Optional[dict]:
    try:
        data = signer.loads(code, max_age=settings.EMAIL_CODE_EXPIRE_MINUTES * 60)
        if set(data.keys()) == set(fields):
            return data
    except itsdangerous.exc.SignatureExpired:
        # code is too old
        raise errors.BadConfirmationCode
    except itsdangerous.exc.BadSignature:
        # someone tampered the code
        raise errors.BadConfirmationCode
