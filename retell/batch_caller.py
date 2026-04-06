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
    response = await client.post(
        "/v2/batch-call",
        json=payload.model_dump(exclude_none=True),
    )
    response.raise_for_status()
    data = response.json()
    logger.info("Batch call created: %s", data)
    return BatchCallResponse(**data)
