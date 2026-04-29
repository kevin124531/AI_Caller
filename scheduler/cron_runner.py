import logging
from datetime import datetime, timezone as dt_timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config.settings import settings

logger = logging.getLogger(__name__)

_local_tz = datetime.now(dt_timezone.utc).astimezone().tzinfo
scheduler = AsyncIOScheduler(timezone=_local_tz)

# Standard cron day numbers (0=Sun) → APScheduler names
_DOW_MAP = {
    "0": "sun", "7": "sun",
    "1": "mon", "2": "tue", "3": "wed",
    "4": "thu", "5": "fri", "6": "sat",
    "*": "*",
}


def start_scheduler() -> None:
    from scheduler.weekly_job import run_weekly_survey

    minute, hour, day, month, dow = settings.scheduler_cron.split()
    trigger = CronTrigger(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=_DOW_MAP.get(dow, dow),
        timezone=_local_tz,
    )
    scheduler.add_job(run_weekly_survey, trigger, id="weekly_survey", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started. Cron: %s", settings.scheduler_cron)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")
