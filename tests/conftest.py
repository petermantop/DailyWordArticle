import pytest

from daily_word_service.container import get_service
from daily_word_service.main import app


@pytest.fixture(autouse=True)
def clear_overrides():
    app.dependency_overrides = {}
    get_service.cache_clear()
    yield
    app.dependency_overrides = {}
    get_service.cache_clear()
