import logging
from scheduler.csv_reader import read_contacts
from retell.batch_caller import create_batch_call
from retell.models import BatchCallTask
from config.settings import settings

logger = logging.getLogger(__name__)


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
                "survey_topic": "your recent experience with our service",
                "week_label": "this week",
                **c.get("metadata", {}),
            },
            metadata={"contact_name": c["name"]},
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
    except Exception as exc:
        logger.error("Batch call failed: %s", exc)
