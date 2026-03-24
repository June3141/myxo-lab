"""Cleanup Lambda infrastructure source-level tests.

Since we cannot run ``pulumi up`` in CI, these tests validate that the
infrastructure source code defines the expected AWS resources for PR
cleanup using "myxo" naming throughout.
"""

from pathlib import Path

INFRA_DIR = Path(__file__).resolve().parent.parent / "infra"


# ---------------------------------------------------------------------------
# Module existence
# ---------------------------------------------------------------------------


def test_cleanup_module_exists():
    """infra/cleanup.py must exist."""
    assert (INFRA_DIR / "cleanup.py").is_file(), "infra/cleanup.py must exist"


# ---------------------------------------------------------------------------
# Resource definitions in cleanup.py
# ---------------------------------------------------------------------------


def _cleanup_source() -> str:
    return (INFRA_DIR / "cleanup.py").read_text()


def test_defines_lambda_function():
    """cleanup.py must define a Lambda Function resource."""
    src = _cleanup_source()
    assert "aws.lambda_.Function(" in src or "lambda_.Function(" in src, (
        "cleanup.py must define a Lambda Function"
    )


def test_defines_iam_role():
    """cleanup.py must define an IAM Role for Lambda execution."""
    src = _cleanup_source()
    assert "iam.Role(" in src, "cleanup.py must define iam.Role"


def test_defines_cloudwatch_log_group():
    """cleanup.py must define a CloudWatch Log Group for Lambda logs."""
    src = _cleanup_source()
    assert "cloudwatch.LogGroup(" in src, "cleanup.py must define cloudwatch.LogGroup"


def test_defines_eventbridge_rule():
    """cleanup.py must define an EventBridge Rule for PR close events."""
    src = _cleanup_source()
    assert "cloudwatch.EventRule(" in src or "EventRule(" in src, (
        "cleanup.py must define an EventBridge Rule"
    )


def test_no_pseudopod_references():
    """All resource names must use 'myxo', not 'pseudopod'."""
    src = _cleanup_source()
    assert "pseudopod" not in src.lower()


def test_myxo_naming():
    """Key resources must include 'myxo' in their names."""
    src = _cleanup_source()
    assert "myxo-pr-cleanup" in src


def test_lambda_runtime_python313():
    """Lambda must use python3.13 runtime."""
    src = _cleanup_source()
    assert "python3.13" in src


def test_lambda_timeout():
    """Lambda must have a timeout of 60 seconds."""
    src = _cleanup_source()
    assert "timeout=60" in src


def test_lambda_handler():
    """Lambda handler must be set to handler.handle."""
    src = _cleanup_source()
    assert "handler.handle" in src


# ---------------------------------------------------------------------------
# Integration with __main__.py
# ---------------------------------------------------------------------------


def test_main_imports_cleanup_module():
    """__main__.py must import or reference the cleanup module."""
    main_src = (INFRA_DIR / "__main__.py").read_text()
    assert "cleanup" in main_src, "__main__.py must import cleanup module"
