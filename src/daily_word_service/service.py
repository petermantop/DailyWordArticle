import logging
from datetime import timezone

from daily_word_service.cache import ArticleCache
from daily_word_service.exceptions import ArticleGenerationError, ServiceError
from daily_word_service.genai import OpenAIArticleGenerator
from daily_word_service.rss import WordsmithRssClient
from daily_word_service.schemas import Article, HealthResponse


logger = logging.getLogger(__name__)


class WordOfTheDayService:
    def __init__(
        self,
        rss_client: WordsmithRssClient,
        article_generator: OpenAIArticleGenerator,
        cache: ArticleCache,
        scheduler_enabled: bool,
    ) -> None:
        self._rss_client = rss_client
        self._article_generator = article_generator
        self._cache = cache
        self._scheduler_enabled = scheduler_enabled

    def get_article(self) -> Article:
        cached_article = self._cache.get_article()
        if cached_article is not None:
            logger.info("Serving cached article")
            return cached_article

        logger.info("Cache miss; generating article")
        return self.refresh_article()

    def refresh_article(self) -> Article:
        try:
            word, description = self._rss_client.fetch_word_of_the_day()
            article = self._article_generator.generate_article(word, description)
            self._cache.set_article(article)
            logger.info("Article refreshed successfully")
            return article
        except ServiceError as exc:
            self._cache.mark_error(str(exc))
            logger.exception("Article refresh failed")
            raise
        except Exception as exc:
            self._cache.mark_error(str(exc))
            logger.exception("Unexpected article refresh failure")
            raise ArticleGenerationError(f"Unexpected refresh failure: {exc}") from exc

    def warm_up(self) -> None:
        try:
            self.refresh_article()
        except ServiceError:
            logger.warning("Startup warm-up failed; service will start in degraded mode")

    def health(self) -> HealthResponse:
        snapshot = self._cache.snapshot()
        status = "ok" if snapshot.article is not None and snapshot.last_error is None else "degraded"
        last_refresh_at = None
        if snapshot.last_refresh_at is not None:
            last_refresh_at = snapshot.last_refresh_at.astimezone(timezone.utc).isoformat()
        return HealthResponse(
            status=status,
            cache_ready=snapshot.article is not None,
            scheduler_enabled=self._scheduler_enabled,
            last_refresh_at=last_refresh_at,
            last_error=snapshot.last_error,
        )

