import logging
from typing import Optional, Any

import httpx
import jinja2

from pydantic import EmailStr

from core.settings import settings
from schemas.base import BaseModel


template_dirs = [
    "services/mailing/templates",
    "src/services/mailing/templates",
]
template_loader = jinja2.FileSystemLoader(template_dirs)
template_env = jinja2.Environment(loader=template_loader, autoescape=True)

logger = logging.getLogger("service(mailing)")


class BaseMessage:
    template_name: Optional[str] = None

    class validation(BaseModel):
        email: EmailStr
        subject: str = settings.COMPANY_NAME

    def __init__(self, **kwargs):
        self.schema = self.validation(**kwargs)

    def get_template(self) -> jinja2.Template:
        """Reimplement it in subclass if needed"""
        if self.template_name:
            return template_env.get_template(self.template_name)

    def get_subject(self) -> str:
        """Reimplement it in subclass if needed"""
        return self.schema.subject

    def get_context(self) -> dict:
        """Reimplement it in subclass if needed"""
        return self.schema.dict()

    def get_payload(self) -> dict:
        """Reimplement it in subclass if needed"""
        return {
            "type": "text/html",
            "value": self.get_template().render(**self.get_context()),
        }

    async def send(self) -> Optional[Any]:
        """ Send email through sendgrid
            curl --request POST \
            --url https://api.sendgrid.com/v3/mail/send \
            --header 'Authorization: Bearer <<YOUR_API_KEY>>' \
            --header 'Content-Type: application/json' \
            --data '{
            "personalizations":[
                {"to":[
                {"email":"john.doe@example.com","name":"John Doe"}
                ],
            "subject":"Hello, World!"}
            ],
            "content": [{"type": "text/plain", "value": "Heya!"}],
            "from":{"email":"sam.smith@example.com","name":"Sam Smith"},
            "reply_to":{"email":"sam.smith@example.com","name":"Sam Smith"}}' """
        to_email = self.schema.email
        subject = self.get_subject()
        context = self.get_context()

        if settings.EMAIL_SEND_MODE:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url="https://api.sendgrid.com/v3/mail/send",
                    headers={
                        "Authorization": f"Bearer {settings.SEND_GRID_KEY}"
                    },
                    json={
                        "personalizations": [
                            {
                                "to": [
                                    {
                                        "email": to_email,
                                        "name": to_email,
                                    }
                                ],
                                "subject": subject,
                            }
                        ],
                        "content": [self.get_payload()],
                        "from": {
                            "email": settings.COMPANY_EMAIL,
                            "name": settings.COMPANY_NAME,
                        },
                    },
                )
                if response.status_code not in range(200, 300):
                    raise Exception(f"Send mail is failed: {response.text}")
            logger.info("Email to %s, response: %s", to_email, response)
        else:
            response = None
            logger.info(
                "Dropping email sending to %s, context: %s", to_email, context
            )

        return response
