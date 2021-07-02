import httpx
from aiogoogle import Aiogoogle

from core.settings import settings


class Sessions:
    def __init__(self):
        self.vk_session = None
        self.facebook_session = None
        self.google_session = None

    async def startup(self):
        self.vk_session = httpx.Client()
        self.facebook_session = httpx.Client()
        self.google_session = Aiogoogle(client_creds=dict(
            client_id=settings.OAUTH_GOOGLE_CLIENT_ID,
            client_secret=settings.OAUTH_GOOGLE_CLIENT_SECRET,
            scopes=['email'],
            redirect_uri=settings.OAUTH_GOOGLE_REDIRECT_URI,
        ))

    async def cleanup(self):
        await self.vk_session.close()
        await self.facebook_session.close()
        await self.google_session.active_session.close()


sessions = Sessions()
