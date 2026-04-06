import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from retell.client import close_retell_client
from scheduler.cron_runner import start_scheduler, stop_scheduler
from store.database import create_all_tables
from webhook.router import router as webhook_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_all_tables()
    start_scheduler()
    logger.info("AI Caller app started.")
    yield
    stop_scheduler()
    await close_retell_client()
    logger.info("AI Caller app shut down.")


app = FastAPI(title="AI Caller", version="1.0.0", lifespan=lifespan)
app.include_router(webhook_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
