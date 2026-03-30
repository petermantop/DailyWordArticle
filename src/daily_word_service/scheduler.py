import logging

from apscheduler.schedulers.background import BackgroundScheduler

from daily_word_service.service import WordOfTheDayService


logger = logging.getLogger(__name__)


def start_scheduler(service: WordOfTheDayService) -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(service.refresh_article, "cron", hour=0, minute=0)
    scheduler.start()
    logger.info("Scheduler started")
    return scheduler

