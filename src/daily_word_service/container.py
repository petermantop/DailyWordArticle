from functools import lru_cache

from daily_word_service.cache import InMemoryArticleCache
from daily_word_service.genai import OpenAIArticleGenerator
from daily_word_service.rss import WordsmithRssClient
from daily_word_service.service import WordOfTheDayService
from daily_word_service.settings import get_settings


@lru_cache(maxsize=1)
def get_service() -> WordOfTheDayService:
    settings = get_settings()
    cache = InMemoryArticleCache(ttl_seconds=settings.cache_ttl)
    rss_client = WordsmithRssClient(feed_url=settings.wordsmith_rss_feed)
    generator = OpenAIArticleGenerator(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
    )
    return WordOfTheDayService(
        rss_client=rss_client,
        article_generator=generator,
        cache=cache,
        scheduler_enabled=settings.enable_scheduler,
    )

