"""
Batch export: query unexported transcripts → format → write JSONL → mark exported.
Run via: python scripts/run_export.py
Or add as a second APScheduler job.
"""
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from store.database import AsyncSessionLocal
from store.models import Transcript
from store.repository import mark_exported
from formatter.qwen_formatter import transcripts_to_jsonl_lines

logger = logging.getLogger(__name__)

EXPORT_DIR = Path("data/exports")


async def export_training_data(output_path: Path | None = None) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    if output_path is None:
        ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = EXPORT_DIR / f"training_{ts}.jsonl"

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Transcript)
            .where(Transcript.exported_for_training == False)  # noqa: E712
            .options(selectinload(Transcript.segments))
        )
        transcripts = list(result.scalars().all())

        if not transcripts:
            logger.info("No unexported transcripts found.")
            return output_path

        lines = transcripts_to_jsonl_lines(transcripts)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        logger.info("Exported %d records to %s", len(lines), output_path)

        for t in transcripts:
            await mark_exported(session, t.id)
        await session.commit()

    return output_path


if __name__ == "__main__":
    asyncio.run(export_training_data())
