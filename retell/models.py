from typing import Any
from pydantic import BaseModel


class BatchCallTask(BaseModel):
    to_number: str
    retell_llm_dynamic_variables: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class BatchCallRequest(BaseModel):
    from_number: str
    tasks: list[BatchCallTask]
    trigger_timestamp: int | None = None  # Unix ms — omit for immediate


class BatchCallResponse(BaseModel):
    batch_call_id: str
    tasks_count: int | None = None
    status: str | None = None
