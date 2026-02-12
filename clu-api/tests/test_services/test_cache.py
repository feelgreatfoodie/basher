from unittest.mock import patch, MagicMock

from app.services.cache import (
    get_cached_extraction,
    set_cached_extraction,
    get_cached_synthesis,
    set_cached_synthesis,
    hash_extractions,
    _content_hash,
)


def test_content_hash_stable():
    """Same content always produces same hash."""
    h1 = _content_hash("hello world")
    h2 = _content_hash("hello world")
    assert h1 == h2


def test_content_hash_different():
    h1 = _content_hash("hello")
    h2 = _content_hash("world")
    assert h1 != h2


def test_hash_extractions_stable():
    data = [{"source": {"name": "a.txt"}}]
    h1 = hash_extractions(data)
    h2 = hash_extractions(data)
    assert h1 == h2


@patch("app.services.cache._get_client")
def test_get_cached_extraction_miss(mock_get_client):
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mock_get_client.return_value = mock_redis

    result = get_cached_extraction("some content", "sonnet")
    assert result is None


@patch("app.services.cache._get_client")
def test_get_cached_extraction_hit(mock_get_client):
    mock_redis = MagicMock()
    mock_redis.get.return_value = '{"source": {"name": "test.txt"}}'
    mock_get_client.return_value = mock_redis

    result = get_cached_extraction("some content", "sonnet")
    assert result is not None
    assert result["source"]["name"] == "test.txt"


@patch("app.services.cache._get_client")
def test_set_cached_extraction(mock_get_client):
    mock_redis = MagicMock()
    mock_get_client.return_value = mock_redis

    set_cached_extraction("content", "sonnet", {"source": {}}, ttl=3600)
    mock_redis.setex.assert_called_once()


@patch("app.services.cache._get_client")
def test_cache_redis_failure_non_fatal(mock_get_client):
    """Redis failures should not raise — just return None."""
    mock_redis = MagicMock()
    mock_redis.get.side_effect = Exception("Connection refused")
    mock_get_client.return_value = mock_redis

    result = get_cached_extraction("content", "sonnet")
    assert result is None


@patch("app.services.cache._get_client")
def test_get_cached_synthesis_miss(mock_get_client):
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mock_get_client.return_value = mock_redis

    result = get_cached_synthesis("some-hash")
    assert result is None


@patch("app.services.cache._get_client")
def test_set_cached_synthesis(mock_get_client):
    mock_redis = MagicMock()
    mock_get_client.return_value = mock_redis

    set_cached_synthesis("some-hash", {"summary": {}})
    mock_redis.setex.assert_called_once()
