"""Stale resource cleanup Lambda handler tests.

Validates that the handler module exists and exposes the expected
interface for the Lambda runtime.
"""

import importlib
import sys
from pathlib import Path
from unittest.mock import patch

# Add lambda/stale_cleanup to sys.path so we can import the handler
HANDLER_DIR = Path(__file__).resolve().parent.parent / "lambda" / "stale_cleanup"


def _import_handler():
    """Import the handler module from lambda/stale_cleanup/."""
    sys.path.insert(0, str(HANDLER_DIR))
    try:
        if "handler" in sys.modules:
            del sys.modules["handler"]
        return importlib.import_module("handler")
    finally:
        sys.path.pop(0)


# ---------------------------------------------------------------------------
# Module existence
# ---------------------------------------------------------------------------


def test_handler_module_exists():
    """lambda/stale_cleanup/handler.py must exist."""
    assert (HANDLER_DIR / "handler.py").is_file(), "lambda/stale_cleanup/handler.py must exist"


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------


def test_handler_has_handle_function():
    """handler module must expose a 'handle' function."""
    mod = _import_handler()
    assert hasattr(mod, "handle"), "handler module must have a 'handle' function"
    assert callable(mod.handle), "'handle' must be callable"


# ---------------------------------------------------------------------------
# Response format
# ---------------------------------------------------------------------------


@patch("handler.boto3")
def test_handler_returns_expected_response_format(mock_boto3):
    """handle() must return a dict with 'statusCode' and 'body' keys."""
    mock_boto3.client.return_value.get_paginator.return_value.paginate.return_value = []
    mod = _import_handler()
    result = mod.handle({}, {})
    assert isinstance(result, dict), "handle() must return a dict"
    assert "statusCode" in result, "response must contain 'statusCode'"
    assert "body" in result, "response must contain 'body'"
