class ServiceError(Exception):
    """Base exception for service errors."""


class UpstreamFetchError(ServiceError):
    """Raised when the RSS feed cannot be fetched or parsed."""


class ArticleGenerationError(ServiceError):
    """Raised when article generation fails."""

