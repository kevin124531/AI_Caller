import logging
from retell.client import get_retell_client
from retell.models import BatchCallRequest, BatchCallResponse, BatchCallTask
from config.settings import settings

logger = logging.getLogger(__name__)


async def create_batch_call(tasks: list[BatchCallTask]) -> BatchCallResponse:
    """POST /v2/batch-call — dispatch a batch of outbound survey calls."""
    payload = BatchCallRequest(
        from_number=settings.retell_from_number,
        tasks=tasks,
    )
    client = get_retell_client()
    request_body = payload.model_dump(exclude_none=True)
    logger.info("Sending batch call request: %s", request_body)
    response = await client.post(
        "/create-batch-call",
        json=request_body,
    )
    if response.status_code != 201:
        logger.error(
            "Batch call failed. Status: %s  Body: %s",
            response.status_code,
            response.text,
        )
    response.raise_for_status()
    data = response.json()
    logger.info("Batch call created: %s", data)
    return BatchCallResponse(**data)
