"""ETagCache - conditional request support with ETag/If-None-Match."""

from __future__ import annotations

from typing import Any


class ETagCache:
    """Cache that stores ETags and response bodies for conditional requests.

    Supports building ``If-None-Match`` headers and handling 304 responses
    to avoid counting against GitHub API rate limits.
    """

    def __init__(self) -> None:
        """Initialize an empty ETag cache."""
        self._etags: dict[str, str] = {}
        self._bodies: dict[str, Any] = {}

    def get_etag(self, url: str) -> str | None:
        """Return the stored ETag for *url*, or ``None`` if not cached."""
        return self._etags.get(url)

    def build_headers(self, url: str, extra_headers: dict[str, str] | None = None) -> dict[str, str]:
        """Build request headers, adding ``If-None-Match`` when an ETag is cached.

        Parameters
        ----------
        url:
            The request URL to look up a cached ETag for.
        extra_headers:
            Optional additional headers to merge into the result.
        """
        headers: dict[str, str] = {}
        if extra_headers:
            headers.update(extra_headers)
        etag = self.get_etag(url)
        if etag is not None:
            headers["If-None-Match"] = etag
        return headers

    def handle_response(
        self,
        url: str,
        status_code: int,
        etag: str | None,
        body: Any,
    ) -> Any:
        """Process an HTTP response, updating the cache as needed.

        * **200** -- stores the *etag* (if present) and *body*, returns *body*.
        * **304** -- returns the previously cached body (or ``None``).
        * Other status codes -- returns *body* as-is without caching.
        """
        if status_code == 304:
            return self._bodies.get(url)

        if status_code == 200:
            if etag is not None:
                self._etags[url] = etag
            else:
                self._etags.pop(url, None)
            self._bodies[url] = body

        return body

    def get_cached_body(self, url: str) -> Any | None:
        """Return the cached response body for *url*, or ``None``."""
        return self._bodies.get(url)

    def clear(self) -> None:
        """Remove all cached ETags and bodies."""
        self._etags.clear()
        self._bodies.clear()
