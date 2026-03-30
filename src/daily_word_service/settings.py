import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openai_model: str
    wordsmith_rss_feed: str
    cache_ttl: int
    enable_scheduler: bool


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        wordsmith_rss_feed=os.getenv(
            "WORDSMITH_RSS_FEED", "https://wordsmith.org/awad/rss1.xml"
        ),
        cache_ttl=int(os.getenv("CACHE_TTL", "86400")),
        enable_scheduler=_parse_bool(os.getenv("ENABLE_SCHEDULER"), True),
    )

