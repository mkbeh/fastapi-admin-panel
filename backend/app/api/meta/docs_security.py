from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext

http_basic = HTTPBasic(auto_error=True)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def secure_docs(
    app: FastAPI,
    *,
    admin_username: str,
    admin_password: str,
    title: str,
    version: str = "0.1.0",
    description: Optional[str] = None,
    docs_url: str = "/docs",
    redoc_url: str = "/redoc",
    openapi_url: str = "/openapi.json",
    **not_needed,
):
    """Hides documentation behind Basic Auth"""
    admin_username = pwd_context.hash(admin_username)
    admin_password = pwd_context.hash(admin_password)

    def get_admin_user(
        credentials: HTTPBasicCredentials = Depends(http_basic),
    ) -> None:
        if pwd_context.verify(
            credentials.username, admin_username
        ) and pwd_context.verify(credentials.password, admin_password):
            return
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Basic"},
        )

    @app.get(
        path=openapi_url,
        include_in_schema=False,
        dependencies=[Depends(get_admin_user)],
    )
    async def get_open_api_endpoint() -> JSONResponse:
        return JSONResponse(
            get_openapi(
                title=title,
                version=version,
                description=description,
                routes=app.routes
            )
        )

    @app.get(
        path=docs_url,
        include_in_schema=False,
        dependencies=[Depends(get_admin_user)]
    )
    async def get_swagger_documentation() -> HTMLResponse:
        return get_swagger_ui_html(openapi_url=openapi_url, title=title)

    @app.get(
        path=redoc_url,
        include_in_schema=False,
        dependencies=[Depends(get_admin_user)]
    )
    async def get_redoc_documentation() -> HTMLResponse:
        return get_redoc_html(openapi_url=openapi_url, title=title)
