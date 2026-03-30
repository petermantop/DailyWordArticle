from fastapi.testclient import TestClient

from daily_word_service.cache import InMemoryArticleCache
from daily_word_service.container import get_service
from daily_word_service.exceptions import (
    ArticleGenerationError,
    InvalidOpenAICredentialsError,
    UpstreamFetchError,
)
from daily_word_service.main import app
from daily_word_service.schemas import Article, HealthStatus
from daily_word_service.service import WordOfTheDayService


class FakeRssClient:
    def __init__(self, word: str = "ephemeral", description: str = "short-lived") -> None:
        self.word = word
        self.description = description
        self.calls = 0

    def fetch_word_of_the_day(self) -> tuple[str, str]:
        self.calls += 1
        return self.word, self.description


class FakeGenerator:
    def __init__(
        self,
        header: str = "A daily word worth knowing today",
        body: str = "A concise definition with usage and an interesting detail.",
    ) -> None:
        self.header = header
        self.body = body
        self.calls = 0

    def generate_article(self, word: str, description: str) -> Article:
        self.calls += 1
        return Article(header=self.header, body=self.body)


def build_service() -> tuple[WordOfTheDayService, FakeRssClient, FakeGenerator]:
    rss = FakeRssClient()
    generator = FakeGenerator()
    service = WordOfTheDayService(
        rss_client=rss,
        article_generator=generator,
        cache=InMemoryArticleCache(ttl_seconds=60),
        scheduler_enabled=False,
    )
    return service, rss, generator


def test_get_word_of_the_day_uses_cache_after_first_request():
    service, rss, generator = build_service()
    app.dependency_overrides[get_service] = lambda: service
    client = TestClient(app)

    first_response = client.get("/word-of-the-day")
    second_response = client.get("/word-of-the-day")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["header"] == "A daily word worth knowing today"
    assert rss.calls == 1
    assert generator.calls == 1


def test_refresh_endpoint_regenerates_article():
    service, rss, generator = build_service()
    app.dependency_overrides[get_service] = lambda: service
    client = TestClient(app)

    first_response = client.get("/word-of-the-day")
    refresh_response = client.post("/word-of-the-day/refresh")

    assert first_response.status_code == 200
    assert refresh_response.status_code == 200
    assert rss.calls == 2
    assert generator.calls == 2


def test_health_endpoint_reports_cache_state():
    service, _, _ = build_service()
    app.dependency_overrides[get_service] = lambda: service
    client = TestClient(app)

    degraded = client.get("/health")
    client.get("/word-of-the-day")
    healthy = client.get("/health")

    assert degraded.status_code == 200
    assert degraded.json()["status"] == HealthStatus.DEGRADED
    assert healthy.json()["cache_ready"] is True
    assert healthy.json()["status"] == HealthStatus.OK


def test_word_of_the_day_returns_503_when_generation_fails():
    class FailingGenerator:
        def generate_article(self, word: str, description: str) -> Article:
            raise ArticleGenerationError("generation failed")

    service = WordOfTheDayService(
        rss_client=FakeRssClient(),
        article_generator=FailingGenerator(),
        cache=InMemoryArticleCache(ttl_seconds=60),
        scheduler_enabled=False,
    )
    app.dependency_overrides[get_service] = lambda: service
    client = TestClient(app)

    response = client.get("/word-of-the-day")

    assert response.status_code == 503
    assert response.json()["detail"] == "generation failed"


def test_word_of_the_day_returns_generic_503_when_openai_credentials_are_invalid():
    class InvalidCredentialsGenerator:
        def generate_article(self, word: str, description: str) -> Article:
            raise InvalidOpenAICredentialsError(
                "OpenAI authentication failed: invalid API key"
            )

    service = WordOfTheDayService(
        rss_client=FakeRssClient(),
        article_generator=InvalidCredentialsGenerator(),
        cache=InMemoryArticleCache(ttl_seconds=60),
        scheduler_enabled=False,
    )
    app.dependency_overrides[get_service] = lambda: service
    client = TestClient(app)

    response = client.get("/word-of-the-day")

    assert response.status_code == 503
    assert response.json()["detail"] == "Article generation service is currently unavailable"


def test_word_of_the_day_returns_503_when_rss_fails():
    class FailingRssClient:
        def fetch_word_of_the_day(self) -> tuple[str, str]:
            raise UpstreamFetchError("rss failed")

    service = WordOfTheDayService(
        rss_client=FailingRssClient(),
        article_generator=FakeGenerator(),
        cache=InMemoryArticleCache(ttl_seconds=60),
        scheduler_enabled=False,
    )
    app.dependency_overrides[get_service] = lambda: service
    client = TestClient(app)

    response = client.get("/word-of-the-day")

    assert response.status_code == 503
    assert response.json()["detail"] == "rss failed"
