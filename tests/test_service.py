import pytest

from daily_word_service.cache import InMemoryArticleCache
from daily_word_service.exceptions import ArticleGenerationError
from daily_word_service.genai import OpenAIArticleGenerator
from daily_word_service.schemas import Article
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
        header: str = "A useful daily word to learn now",
        body: str = "A simple definition, usage example, and interesting detail.",
    ) -> None:
        self.header = header
        self.body = body
        self.calls = 0

    def generate_article(self, word: str, description: str) -> Article:
        self.calls += 1
        return Article(header=self.header, body=self.body)


def test_service_generates_and_caches_article():
    rss = FakeRssClient()
    generator = FakeGenerator()
    service = WordOfTheDayService(
        rss_client=rss,
        article_generator=generator,
        cache=InMemoryArticleCache(ttl_seconds=60),
        scheduler_enabled=False,
    )

    first = service.get_article()
    second = service.get_article()

    assert first == second
    assert rss.calls == 1
    assert generator.calls == 1


def test_service_records_error_in_health_state():
    class FailingGenerator:
        def generate_article(self, word: str, description: str) -> Article:
            raise ArticleGenerationError("generation failed")

    service = WordOfTheDayService(
        rss_client=FakeRssClient(),
        article_generator=FailingGenerator(),
        cache=InMemoryArticleCache(ttl_seconds=60),
        scheduler_enabled=False,
    )

    with pytest.raises(ArticleGenerationError):
        service.refresh_article()

    health = service.health()
    assert health.status == "degraded"
    assert health.last_error == "generation failed"


def test_warm_up_does_not_raise_on_failure():
    class FailingGenerator:
        def generate_article(self, word: str, description: str) -> Article:
            raise ArticleGenerationError("generation failed")

    service = WordOfTheDayService(
        rss_client=FakeRssClient(),
        article_generator=FailingGenerator(),
        cache=InMemoryArticleCache(ttl_seconds=60),
        scheduler_enabled=False,
    )

    service.warm_up()

    health = service.health()
    assert health.status == "degraded"
    assert health.cache_ready is False


def test_openai_parser_rejects_malformed_output():
    generator = OpenAIArticleGenerator(api_key="test-key", model="gpt-4o-mini")

    with pytest.raises(ArticleGenerationError):
        generator._parse_article("single line only")


def test_openai_parser_normalizes_extra_lines():
    generator = OpenAIArticleGenerator(api_key="test-key", model="gpt-4o-mini")

    article = generator._parse_article(
        "A useful title for the word of the day\n"
        "Definition with usage.\n"
        "Interesting detail included."
    )

    assert article.header == "A useful title for the word of the day"
    assert article.body == "Definition with usage. Interesting detail included."
