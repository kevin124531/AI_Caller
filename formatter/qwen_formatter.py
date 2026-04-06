"""
Convert stored transcripts into Qwen / LLaMA-Factory compatible JSONL.

Output format: ShareGPT (multi-turn conversations list).
Each call becomes one training record:
  system  → survey agent system prompt
  human   → respondent utterances
  gpt     → agent utterances
"""
from agent.system_prompt import get_system_prompt
from formatter.schemas import ShareGPTMessage, ShareGPTRecord
from store.models import Transcript

ROLE_MAP = {"agent": "gpt", "user": "human"}


def transcript_to_sharegpt(transcript: Transcript, call_metadata: dict | None = None) -> ShareGPTRecord:
    """Convert a Transcript ORM object (with loaded segments) to a ShareGPT record."""
    meta = call_metadata or {}
    contact_name = meta.get("contact_name", "there")
    survey_topic = meta.get("survey_topic", "your recent experience")
    week_label = meta.get("week_label", "recently")

    system_prompt = get_system_prompt(
        contact_name=contact_name,
        survey_topic=survey_topic,
        week_label=week_label,
    )

    messages: list[ShareGPTMessage] = [
        ShareGPTMessage(from_="system", value=system_prompt)
    ]

    for seg in transcript.segments:
        role = ROLE_MAP.get(seg.role, "human")
        messages.append(ShareGPTMessage(from_=role, value=seg.content))

    return ShareGPTRecord(conversations=messages, call_id=transcript.call_id)


def transcripts_to_jsonl_lines(
    transcripts: list[Transcript],
    call_metadata_map: dict[str, dict] | None = None,
) -> list[str]:
    """Convert a list of transcripts to JSONL strings (one per line)."""
    import json

    meta_map = call_metadata_map or {}
    lines = []
    for t in transcripts:
        try:
            record = transcript_to_sharegpt(t, meta_map.get(t.call_id))
            lines.append(json.dumps(record.to_jsonl_dict(), ensure_ascii=False))
        except Exception as exc:
            import logging
            logging.getLogger(__name__).error("Failed to format transcript %s: %s", t.call_id, exc)
    return lines
