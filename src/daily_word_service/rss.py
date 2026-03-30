import logging
from xml.etree import ElementTree

import requests

from daily_word_service.exceptions import UpstreamFetchError


logger = logging.getLogger(__name__)


class WordsmithRssClient:
    def __init__(self, feed_url: str, timeout_seconds: int = 10) -> None:
        self._feed_url = feed_url
        self._timeout_seconds = timeout_seconds

    def fetch_word_of_the_day(self) -> tuple[str, str]:
        logger.info("Fetching word of the day feed", extra={"feed_url": self._feed_url})
        try:
            response = requests.get(self._feed_url, timeout=self._timeout_seconds)
            response.raise_for_status()
            root = ElementTree.fromstring(response.content)
            item = root.find("./channel/item")
            if item is None:
                raise UpstreamFetchError("RSS feed did not contain an item entry")
            title = item.findtext("title")
            description = item.findtext("description")
            if not title or not description:
                raise UpstreamFetchError("RSS item is missing title or description")
            return title.strip(), description.strip()
        except requests.RequestException as exc:
            raise UpstreamFetchError(f"Failed to fetch RSS feed: {exc}") from exc
        except ElementTree.ParseError as exc:
            raise UpstreamFetchError(f"Failed to parse RSS feed: {exc}") from exc

