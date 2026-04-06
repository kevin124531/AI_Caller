from typing import Any
from pydantic import BaseModel


class TranscriptUtterance(BaseModel):
    role: str           # "agent" | "user"
    content: str
    words: list[dict[str, Any]] | None = None


class CallObject(BaseModel):
    call_id: str
    batch_call_id: str | None = None
    agent_id: str | None = None
    call_status: str | None = None
    from_number: str | None = None
    to_number: str | None = None
    start_timestamp: int | None = None
    end_timestamp: int | None = None
    duration_ms: int | None = None
    recording_url: str | None = None
    transcript: str | None = None
    transcript_object: list[TranscriptUtterance] | None = None
    transcript_with_tool_calls: list[dict[str, Any]] | None = None
    call_analysis: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    retell_llm_dynamic_variables: dict[str, Any] | None = None


class RetellWebhookPayload(BaseModel):
    event: str
    call: CallObject
