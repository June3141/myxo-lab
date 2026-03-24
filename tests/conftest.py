"""Shared pytest configuration and fixtures."""

import pytest

# Marker names used for test sizing
SIZE_MARKERS = {"small", "medium", "large"}


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-apply ``@pytest.mark.small`` to tests that have no size marker.

    This ensures every test is categorized, so ``-m small`` collects all
    unmarked (i.e. fast unit) tests without requiring explicit decoration.
    """
    for item in items:
        existing = {m.name for m in item.iter_markers()}
        if not existing & SIZE_MARKERS:
            item.add_marker(pytest.mark.small)
