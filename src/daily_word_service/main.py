import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from daily_word_service.api import router
from daily_word_service.container import get_service
from daily_word_service.scheduler import start_scheduler
from daily_word_service.settings import get_settings


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    service = get_service()
    scheduler = None

    service.warm_up()

    if settings.enable_scheduler:
        scheduler = start_scheduler(service)

    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)


app = FastAPI(
    title="Daily Word Service",
    version="1.0.0",
    description="A REST API that fetches the daily word and generates a concise AI article.",
    lifespan=lifespan,
)
app.include_router(router)
