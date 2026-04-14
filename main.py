"""
AI Caller — iMasonsGPT knowledge extraction scheduler.

Run with:
    python main.py

The scheduler fires weekly (SCHEDULER_CRON in .env) and dispatches
batch calls to all contacts in the CSV via Retell AI.

After calls complete, run:
    python scripts/download_recordings.py
"""
import asyncio
import logging
from retell.client import close_retell_client
from scheduler.cron_runner import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    start_scheduler()
    logger.info("AI Caller started. Press Ctrl+C to stop.")
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        stop_scheduler()
        await close_retell_client()
        logger.info("AI Caller stopped.")


if __name__ == "__main__":
    asyncio.run(main())
