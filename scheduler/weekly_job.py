import asyncio
import json
import logging
from pathlib import Path
from scheduler.csv_reader import read_contacts
from scheduler.recording_poller import poll_and_download
from retell.batch_caller import create_batch_call
from retell.models import BatchCallTask
from config.settings import settings

logger = logging.getLogger(__name__)

STATE_FILE = Path("data/state/last_batch.json")


async def run_weekly_survey() -> None:
    """Scheduled job: read contacts CSV → dispatch Retell batch call."""
    logger.info("Weekly survey job starting.")
    try:
        contacts = read_contacts(settings.contacts_csv_path)
    except Exception as exc:
        logger.error("Failed to read contacts: %s", exc)
        return

    if not contacts:
        logger.warning("No contacts found — skipping batch call.")
        return

    tasks = [
        BatchCallTask(
            to_number=c["phone"],
            retell_llm_dynamic_variables={
                "contact_name": c["name"],
                "question_category": c["metadata"].get(
                    "question_category", "Data Center Design & Operations"
                ),
            },
            metadata={
                "contact_name":      c["name"],
                "job_title":         c["metadata"].get("job_title", "digital infrastructure expert"),
                "specialisation":    c["metadata"].get("specialisation", "data center operations"),
                "question_category": c["metadata"].get(
                    "question_category", "Data Center Design & Operations"
                ),
            },
        )
        for c in contacts
    ]

    try:
        result = await create_batch_call(tasks)
        logger.info(
            "Batch call dispatched. batch_call_id=%s tasks=%s",
            result.batch_call_id,
            len(tasks),
        )
        # Save batch_call_id so download_recordings.py can also find the calls
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(
            json.dumps({"batch_call_id": result.batch_call_id, "tasks": len(tasks)})
        )

        # Launch background poller — downloads recordings automatically as calls finish
        asyncio.create_task(poll_and_download(result.batch_call_id))
        logger.info("Recording poller launched in background.")

    except Exception as exc:
        logger.error("Batch call failed: %s", exc)
