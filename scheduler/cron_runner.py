import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config.settings import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    from scheduler.weekly_job import run_weekly_survey

    minute, hour, day, month, day_of_week = settings.scheduler_cron.split()
    trigger = CronTrigger(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
    )
    scheduler.add_job(run_weekly_survey, trigger, id="weekly_survey", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started. Cron: %s", settings.scheduler_cron)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")
