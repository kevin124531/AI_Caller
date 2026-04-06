import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from store.models import Call, Score, Transcript, TranscriptSegment

logger = logging.getLogger(__name__)


async def get_or_create_call(session: AsyncSession, call_id: str, **kwargs) -> Call:
    result = await session.execute(select(Call).where(Call.call_id == call_id))
    call = result.scalar_one_or_none()
    if call is None:
        call = Call(call_id=call_id, **kwargs)
        session.add(call)
        await session.flush()
    return call


async def save_transcript(
    session: AsyncSession,
    call_id: str,
    segments: list[dict],
    s3_key: str | None = None,
) -> Transcript:
    transcript = Transcript(call_id=call_id, s3_key=s3_key)
    session.add(transcript)
    await session.flush()

    for seg in segments:
        session.add(
            TranscriptSegment(
                transcript_id=transcript.id,
                role=seg.get("role", "unknown"),
                content=seg.get("content", ""),
                start_ms=seg.get("start_ms"),
                end_ms=seg.get("end_ms"),
            )
        )
    await session.flush()
    return transcript


async def save_scores(
    session: AsyncSession,
    call_id: str,
    scores: dict[str, float],
    scorer_version: str = "v1",
) -> None:
    for dimension, value in scores.items():
        session.add(
            Score(
                call_id=call_id,
                dimension=dimension,
                value=value,
                scorer_version=scorer_version,
            )
        )
    await session.flush()


async def get_unexported_transcripts(session: AsyncSession) -> list[Transcript]:
    result = await session.execute(
        select(Transcript)
        .where(Transcript.exported_for_training == False)  # noqa: E712
    )
    return list(result.scalars().all())


async def mark_exported(session: AsyncSession, transcript_id: int) -> None:
    result = await session.execute(
        select(Transcript).where(Transcript.id == transcript_id)
    )
    transcript = result.scalar_one_or_none()
    if transcript:
        transcript.exported_for_training = True
        await session.flush()
