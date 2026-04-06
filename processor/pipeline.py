import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from webhook.models import CallObject
from processor.transcript_parser import parse_transcript
from processor.scorer import score_transcript, SCORER_VERSION
from store.repository import get_or_create_call, save_transcript, save_scores
from store.s3_uploader import upload_transcript

logger = logging.getLogger(__name__)


async def process_call_ended(call: CallObject, session: AsyncSession) -> None:
    """Full pipeline: parse → store call → upload S3 → save transcript → score."""
    call_id = call.call_id

    # 1. Upsert call record
    started_at = (
        datetime.fromtimestamp(call.start_timestamp / 1000, tz=timezone.utc)
        if call.start_timestamp else None
    )
    ended_at = (
        datetime.fromtimestamp(call.end_timestamp / 1000, tz=timezone.utc)
        if call.end_timestamp else None
    )
    duration = (
        call.duration_ms // 1000 if call.duration_ms else None
    )

    await get_or_create_call(
        session,
        call_id=call_id,
        batch_call_id=call.batch_call_id,
        to_number=call.to_number or "",
        from_number=call.from_number,
        status=call.call_status,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration,
        recording_url=call.recording_url,
    )

    # 2. Parse transcript segments
    segments = parse_transcript(call)

    # 3. Upload raw payload to S3
    s3_key: str | None = None
    try:
        raw_payload = call.model_dump()
        s3_key = upload_transcript(call_id, raw_payload)
    except Exception as exc:
        logger.warning("S3 upload failed for %s (continuing): %s", call_id, exc)

    # 4. Save transcript + segments to DB
    try:
        await save_transcript(session, call_id, segments, s3_key=s3_key)
    except Exception as exc:
        logger.error("Failed to save transcript for %s: %s", call_id, exc)
        return

    # 5. Auto-score
    try:
        scores = score_transcript(segments)
        await save_scores(session, call_id, scores, scorer_version=SCORER_VERSION)
        logger.info("Scores for %s: %s", call_id, scores)
    except Exception as exc:
        logger.error("Scoring failed for %s: %s", call_id, exc)
