from fastapi import APIRouter

from api.endpoints.general import accounts, auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix='/auth', tags=['Auth'])
api_router.include_router(accounts.router, prefix='/accounts', tags=['accounts'])
