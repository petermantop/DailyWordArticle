import logging

from openai import OpenAI

from daily_word_service.exceptions import ArticleGenerationError
from daily_word_service.schemas import Article


logger = logging.getLogger(__name__)


class OpenAIArticleGenerator:
    def __init__(self, api_key: str | None, model: str) -> None:
        self._api_key = api_key
        self._model = model

    def generate_article(self, word: str, description: str) -> Article:
        if not self._api_key:
            raise ArticleGenerationError("OPENAI_API_KEY is not configured")

        prompt = (
            "You are writing a compact article for a REST API response.\n"
            f"Word of the day: {word}\n"
            f"Reference description: {description}\n\n"
            "Return exactly two lines.\n"
            "Line 1: a title between 40 and 60 characters.\n"
            "Line 2: a body up to 300 characters that explains the meaning, "
            "usage, and one interesting detail in simple English.\n"
            "Do not include labels, markdown, or extra lines."
        )

        logger.info("Generating article with OpenAI", extra={"model": self._model})
        try:
            client = OpenAI(api_key=self._api_key)
            response = client.responses.create(
                model=self._model,
                input=prompt,
            )
        except Exception as exc:
            raise ArticleGenerationError(f"OpenAI request failed: {exc}") from exc

        content = getattr(response, "output_text", "") or ""
        article = self._parse_article(content)
        logger.info("Generated article successfully", extra={"model": self._model})
        return article

    def _parse_article(self, content: str) -> Article:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if len(lines) < 2:
            raise ArticleGenerationError("Model response did not contain header and body")

        header = lines[0][:60].strip()
        body = " ".join(lines[1:])[:300].strip()
        if not header or not body:
            raise ArticleGenerationError("Model response was empty after parsing")

        return Article(header=header, body=body)

