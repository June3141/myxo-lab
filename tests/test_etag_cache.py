"""Tests for ETagCache - conditional request support with ETag/If-None-Match."""

from __future__ import annotations

from myxo.etag_cache import ETagCache

# --- init ---


def test_etag_cache_initializes_empty():
    cache = ETagCache()
    assert cache.get_etag("https://api.github.com/repos/foo/bar") is None
    assert cache.get_cached_body("https://api.github.com/repos/foo/bar") is None


# --- get_etag / store via handle_response ---


def test_get_etag_returns_none_for_unknown_url():
    cache = ETagCache()
    assert cache.get_etag("https://api.github.com/unknown") is None


def test_get_etag_returns_stored_etag_after_200():
    cache = ETagCache()
    url = "https://api.github.com/repos/foo/bar"
    cache.handle_response(url, status_code=200, etag='"abc123"', body={"id": 1})
    assert cache.get_etag(url) == '"abc123"'


def test_get_etag_updates_on_new_200():
    cache = ETagCache()
    url = "https://api.github.com/repos/foo/bar"
    cache.handle_response(url, status_code=200, etag='"v1"', body={"v": 1})
    cache.handle_response(url, status_code=200, etag='"v2"', body={"v": 2})
    assert cache.get_etag(url) == '"v2"'


# --- build_headers ---


def test_build_headers_without_cached_etag():
    cache = ETagCache()
    headers = cache.build_headers("https://api.github.com/repos/foo/bar")
    assert "If-None-Match" not in headers


def test_build_headers_with_cached_etag():
    cache = ETagCache()
    url = "https://api.github.com/repos/foo/bar"
    cache.handle_response(url, status_code=200, etag='"abc123"', body={"id": 1})
    headers = cache.build_headers(url)
    assert headers["If-None-Match"] == '"abc123"'


def test_build_headers_merges_extra_headers():
    cache = ETagCache()
    url = "https://api.github.com/repos/foo/bar"
    cache.handle_response(url, status_code=200, etag='"abc123"', body={"id": 1})
    headers = cache.build_headers(url, extra_headers={"Authorization": "token xyz"})
    assert headers["If-None-Match"] == '"abc123"'
    assert headers["Authorization"] == "token xyz"


def test_build_headers_extra_headers_without_etag():
    cache = ETagCache()
    url = "https://api.github.com/unknown"
    headers = cache.build_headers(url, extra_headers={"Accept": "application/json"})
    assert "If-None-Match" not in headers
    assert headers["Accept"] == "application/json"


# --- handle_response ---


def test_handle_response_200_stores_body_and_etag():
    cache = ETagCache()
    url = "https://api.github.com/repos/foo/bar"
    body = {"name": "bar", "full_name": "foo/bar"}
    result = cache.handle_response(url, status_code=200, etag='"etag1"', body=body)
    assert result == body
    assert cache.get_etag(url) == '"etag1"'
    assert cache.get_cached_body(url) == body


def test_handle_response_304_returns_cached_body():
    cache = ETagCache()
    url = "https://api.github.com/repos/foo/bar"
    original_body = {"name": "bar"}
    cache.handle_response(url, status_code=200, etag='"etag1"', body=original_body)

    result = cache.handle_response(url, status_code=304, etag=None, body=None)
    assert result == original_body


def test_handle_response_304_without_prior_cache_returns_none():
    cache = ETagCache()
    url = "https://api.github.com/repos/foo/bar"
    result = cache.handle_response(url, status_code=304, etag=None, body=None)
    assert result is None


def test_handle_response_200_without_etag_stores_body_only():
    cache = ETagCache()
    url = "https://api.github.com/repos/foo/bar"
    body = {"name": "bar"}
    result = cache.handle_response(url, status_code=200, etag=None, body=body)
    assert result == body
    assert cache.get_etag(url) is None
    assert cache.get_cached_body(url) == body


def test_handle_response_200_replaces_previous_cache():
    cache = ETagCache()
    url = "https://api.github.com/repos/foo/bar"
    cache.handle_response(url, status_code=200, etag='"v1"', body={"v": 1})
    cache.handle_response(url, status_code=200, etag='"v2"', body={"v": 2})
    assert cache.get_cached_body(url) == {"v": 2}
    assert cache.get_etag(url) == '"v2"'


# --- get_cached_body ---


def test_get_cached_body_returns_none_for_unknown_url():
    cache = ETagCache()
    assert cache.get_cached_body("https://api.github.com/unknown") is None


def test_get_cached_body_returns_stored_body():
    cache = ETagCache()
    url = "https://api.github.com/repos/foo/bar"
    body = [{"id": 1}, {"id": 2}]
    cache.handle_response(url, status_code=200, etag='"etag1"', body=body)
    assert cache.get_cached_body(url) == body


# --- clear ---


def test_clear_removes_all_entries():
    cache = ETagCache()
    url1 = "https://api.github.com/repos/foo/bar"
    url2 = "https://api.github.com/repos/baz/qux"
    cache.handle_response(url1, status_code=200, etag='"e1"', body={"a": 1})
    cache.handle_response(url2, status_code=200, etag='"e2"', body={"b": 2})
    cache.clear()
    assert cache.get_etag(url1) is None
    assert cache.get_etag(url2) is None
    assert cache.get_cached_body(url1) is None
    assert cache.get_cached_body(url2) is None


# --- multiple URLs ---


def test_independent_urls_do_not_interfere():
    cache = ETagCache()
    url1 = "https://api.github.com/repos/foo/bar"
    url2 = "https://api.github.com/repos/baz/qux"
    cache.handle_response(url1, status_code=200, etag='"e1"', body={"a": 1})
    cache.handle_response(url2, status_code=200, etag='"e2"', body={"b": 2})
    assert cache.get_etag(url1) == '"e1"'
    assert cache.get_etag(url2) == '"e2"'
    assert cache.get_cached_body(url1) == {"a": 1}
    assert cache.get_cached_body(url2) == {"b": 2}
