import logging
from sqlalchemy.ext.asyncio import AsyncSession
from webhook.models import RetellWebhookPayload
from processor.pipeline import process_call_ended

logger = logging.getLogger(__name__)


async def handle_event(payload: RetellWebhookPayload, session: AsyncSession) -> None:
    event = payload.event
    call_id = payload.call.call_id

    if event == "call_ended":
        logger.info("call_ended received for call_id=%s", call_id)
        await process_call_ended(payload.call, session)

    elif event == "call_started":
        logger.info("call_started for call_id=%s", call_id)

    elif event == "call_analyzed":
        logger.info("call_analyzed for call_id=%s analysis=%s", call_id, payload.call.call_analysis)

    else:
        logger.warning("Unknown event type: %s for call_id=%s", event, call_id)
