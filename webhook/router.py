import hashlib
import hmac
import logging
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from config.settings import settings
from store.database import get_session
from webhook.models import RetellWebhookPayload
from webhook.event_handler import handle_event

router = APIRouter(prefix="/webhook", tags=["webhook"])
logger = logging.getLogger(__name__)


def _verify_signature(body: bytes, signature: str | None) -> bool:
    if not settings.retell_webhook_secret:
        return True  # Skip verification if no secret configured
    if not signature:
        return False
    expected = hmac.HMAC(
        settings.retell_webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/retell")
async def retell_webhook(
    request: Request,
    x_retell_signature: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
):
    body = await request.body()
    if not _verify_signature(body, x_retell_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = RetellWebhookPayload.model_validate_json(body)
    await handle_event(payload, session)
    await session.commit()
    return {"status": "ok"}
