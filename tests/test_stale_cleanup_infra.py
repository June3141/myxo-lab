"""Stale resource cleanup infrastructure source-level tests.

Since we cannot run ``pulumi up`` in CI, these tests validate that the
infrastructure source code defines the expected AWS resources for stale
resource cleanup using "myxo" naming throughout.
"""

from pathlib import Path

INFRA_DIR = Path(__file__).resolve().parent.parent / "infra"


# ---------------------------------------------------------------------------
# Module existence
# ---------------------------------------------------------------------------


def test_stale_cleanup_module_exists():
    """infra/stale_cleanup.py must exist."""
    assert (INFRA_DIR / "stale_cleanup.py").is_file(), "infra/stale_cleanup.py must exist"


# ---------------------------------------------------------------------------
# Resource definitions in stale_cleanup.py
# ---------------------------------------------------------------------------


def _stale_cleanup_source() -> str:
    return (INFRA_DIR / "stale_cleanup.py").read_text()


def test_defines_lambda_function():
    """stale_cleanup.py must define a Lambda Function resource."""
    src = _stale_cleanup_source()
    assert "aws.lambda_.Function(" in src, "stale_cleanup.py must define aws.lambda_.Function"


def test_defines_eventbridge_schedule_rule():
    """stale_cleanup.py must define an EventBridge schedule rule."""
    src = _stale_cleanup_source()
    assert "cloudwatch.EventRule(" in src, "stale_cleanup.py must define cloudwatch.EventRule"


def test_defines_eventbridge_target():
    """stale_cleanup.py must define an EventBridge target."""
    src = _stale_cleanup_source()
    assert "cloudwatch.EventTarget(" in src, "stale_cleanup.py must define cloudwatch.EventTarget"


def test_defines_iam_role():
    """stale_cleanup.py must define an IAM role for the Lambda function."""
    src = _stale_cleanup_source()
    assert "iam.Role(" in src or "common.create_lambda_role(" in src, "stale_cleanup.py must define iam.Role"


def test_defines_cloudwatch_log_group():
    """stale_cleanup.py must define a CloudWatch Log Group for Lambda logs."""
    src = _stale_cleanup_source()
    has_log_group = "cloudwatch.LogGroup(" in src or "common.create_log_group(" in src
    assert has_log_group, "stale_cleanup.py must define cloudwatch.LogGroup"


def test_myxo_naming():
    """Key resources must include 'myxo' in their names."""
    src = _stale_cleanup_source()
    assert "myxo-stale-cleanup" in src, "Lambda function must use myxo-stale-cleanup name"


def test_no_pseudopod_references():
    """All resource names must use 'myxo', not 'pseudopod'."""
    src = _stale_cleanup_source()
    assert "pseudopod" not in src.lower()


def test_lambda_runtime_python313():
    """Lambda function must use python3.13 runtime."""
    src = _stale_cleanup_source()
    assert "python3.13" in src, "Lambda must use python3.13 runtime"


def test_lambda_timeout_300():
    """Lambda function must have 300s timeout."""
    src = _stale_cleanup_source()
    assert "300" in src, "Lambda must have 300s timeout"


def test_schedule_expression():
    """EventBridge rule must schedule daily at 03:00 UTC."""
    src = _stale_cleanup_source()
    assert "cron(0 3 * * ? *)" in src, "EventBridge rule must run daily at 03:00 UTC"


def test_main_imports_stale_cleanup_module():
    """__main__.py must import or reference the stale_cleanup module."""
    main_src = (INFRA_DIR / "__main__.py").read_text()
    assert "stale_cleanup" in main_src, "__main__.py must import stale_cleanup module"
