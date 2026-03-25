"""PR cleanup Lambda handler tests.

Validates that the handler module exists, has the expected entry point,
and returns the correct response format.
"""

import importlib
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Module existence
# ---------------------------------------------------------------------------


def test_handler_module_exists():
    """lambda/pr_cleanup/handler.py must exist."""
    handler_path = Path(__file__).resolve().parent.parent / "lambda" / "pr_cleanup" / "handler.py"
    assert handler_path.is_file(), "lambda/pr_cleanup/handler.py must exist"


# ---------------------------------------------------------------------------
# Handler function
# ---------------------------------------------------------------------------


def _load_handler():
    """Import the handler module dynamically."""
    handler_dir = str(Path(__file__).resolve().parent.parent / "lambda" / "pr_cleanup")
    original_path = sys.path.copy()
    try:
        if handler_dir not in sys.path:
            sys.path.insert(0, handler_dir)
        if "handler" in sys.modules:
            return importlib.reload(sys.modules["handler"])
        return importlib.import_module("handler")
    finally:
        sys.path[:] = original_path


def test_handler_has_handle_function():
    """handler module must expose a 'handle' function."""
    mod = _load_handler()
    assert hasattr(mod, "handle"), "handler module must have a 'handle' function"
    assert callable(mod.handle)


def test_handler_returns_status_code():
    """handle() must return a dict with 'statusCode'."""
    mod = _load_handler()
    event = {
        "detail": {
            "action": "closed",
            "pull_request": {"number": 42},
        }
    }
    result = mod.handle(event, None)
    assert isinstance(result, dict)
    assert "statusCode" in result


def test_handler_returns_200_on_valid_event():
    """handle() must return 200 for a valid PR close event."""
    mod = _load_handler()
    event = {
        "detail": {
            "action": "closed",
            "pull_request": {"number": 99},
        }
    }
    result = mod.handle(event, None)
    assert result["statusCode"] == 200


def test_handler_body_contains_pr_number():
    """Response body must reference the PR number."""
    mod = _load_handler()
    event = {
        "detail": {
            "action": "closed",
            "pull_request": {"number": 7},
        }
    }
    result = mod.handle(event, None)
    body = json.loads(result["body"]) if isinstance(result["body"], str) else result["body"]
    assert body["pr_number"] == 7
