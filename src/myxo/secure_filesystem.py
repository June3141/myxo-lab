"""SecureFilesystemMCP — file access allowlist for AI agent infrastructure."""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import PurePosixPath


class SecureFilesystemMCP:
    """Guard that restricts file access to an explicit allowlist.

    *Blocked* patterns always take priority over *allowed* patterns, so
    sensitive files (secrets, keys, env files, ...) are never accessible
    even when they happen to sit inside an allowed directory tree.
    """

    def __init__(
        self,
        allowed_patterns: list[str],
        blocked_patterns: list[str],
    ) -> None:
        self.allowed_patterns = allowed_patterns
        self.blocked_patterns = blocked_patterns

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(path: str) -> str:
        """Normalize backslashes to forward slashes for cross-platform support."""
        return path.replace("\\", "/")

    def _matches_any(self, path: str, patterns: list[str]) -> bool:
        """Return True if *path* matches at least one of *patterns*.

        Matching is performed against both the full path string and every
        individual component (filename, parent directories) so that
        patterns like ``*.pem`` catch ``src/certs/server.pem`` and
        patterns like ``secrets/**`` catch ``secrets/api_key.txt``.
        """
        path = self._normalize(path)
        pure = PurePosixPath(path)
        for pattern in patterns:
            # Match the full path
            if fnmatch(path, pattern):
                return True
            # Match just the filename (handles e.g. "*.pem", ".env*")
            if fnmatch(pure.name, pattern):
                return True
            # Match each ancestor + remaining tail so directory patterns
            # like "secrets/**" work for "secrets/api_key.txt"
            parts = pure.parts
            for i in range(len(parts)):
                sub = str(PurePosixPath(*parts[i:]))
                if fnmatch(sub, pattern):
                    return True
        return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_access(self, path: str) -> bool:
        """Return ``True`` if *path* is accessible, ``False`` otherwise."""
        path = self._normalize(path)
        if self._matches_any(path, self.blocked_patterns):
            return False
        return self._matches_any(path, self.allowed_patterns)

    def validate_access(self, path: str) -> None:
        """Raise :class:`PermissionError` if *path* is not accessible."""
        if not self.check_access(path):
            raise PermissionError(
                f"Access denied: '{path}' is not in the allowed file list"
            )
