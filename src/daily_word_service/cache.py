from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from cachetools import TTLCache

from daily_word_service.schemas import Article

ARTICLE_CACHE_KEY = "article"


@dataclass
class CacheSnapshot:
    article: Article | None
    last_refresh_at: datetime | None
    last_error: str | None


class ArticleCache(Protocol):
    def get_article(self) -> Article | None:
        ...

    def set_article(self, article: Article) -> None:
        ...

    def mark_error(self, error: str) -> None:
        ...

    def snapshot(self) -> CacheSnapshot:
        ...


class InMemoryArticleCache:
    def __init__(self, ttl_seconds: int) -> None:
        self._cache: TTLCache[str, Article] = TTLCache(maxsize=1, ttl=ttl_seconds)
        self._last_refresh_at: datetime | None = None
        self._last_error: str | None = None

    def get_article(self) -> Article | None:
        return self._cache.get(ARTICLE_CACHE_KEY)

    def set_article(self, article: Article) -> None:
        self._cache[ARTICLE_CACHE_KEY] = article
        self._last_refresh_at = datetime.now(timezone.utc)
        self._last_error = None

    def mark_error(self, error: str) -> None:
        self._last_error = error

    def snapshot(self) -> CacheSnapshot:
        return CacheSnapshot(
            article=self._cache.get(ARTICLE_CACHE_KEY),
            last_refresh_at=self._last_refresh_at,
            last_error=self._last_error,
        )
