"""Tests for standardized resource tagging strategy (#250).

Verifies:
- Required tags are defined in constants.py
- cost_tags() includes ManagedBy tag
- preview_tags() helper exists for ephemeral resources
- Preview modules (preview.py, frontend_preview.py) use cost tags from constants
- Cleanup modules reference the correct AutoDelete tag key from constants
"""

from pathlib import Path

INFRA_DIR = Path(__file__).resolve().parent.parent / "infra"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _read_source(filename: str) -> str:
    return (INFRA_DIR / filename).read_text()


# ===========================================================================
# 1. constants.py — required tag keys & helper functions
# ===========================================================================


class TestConstantsRequiredTags:
    """COST_TAGS and cost_tags() must include all mandatory keys."""

    def test_cost_tags_dict_has_project(self):
        src = _read_source("constants.py")
        assert '"Project"' in src

    def test_cost_tags_dict_has_environment(self):
        src = _read_source("constants.py")
        assert '"Environment"' in src

    def test_cost_tags_dict_has_managed_by(self):
        """ManagedBy tag must be in COST_TAGS base dict."""
        src = _read_source("constants.py")
        assert '"ManagedBy"' in src

    def test_cost_tags_function_adds_cost_center(self):
        src = _read_source("constants.py")
        assert '"CostCenter"' in src

    def test_preview_tags_function_exists(self):
        """preview_tags() helper must be defined for ephemeral resources."""
        src = _read_source("constants.py")
        assert "def preview_tags(" in src

    def test_preview_tags_in_all(self):
        """preview_tags must be exported in __all__."""
        src = _read_source("constants.py")
        assert '"preview_tags"' in src or "'preview_tags'" in src

    def test_preview_tags_includes_auto_delete(self):
        """preview_tags() must add AutoDelete tag."""
        src = _read_source("constants.py")
        assert '"AutoDelete"' in src

    def test_preview_tags_includes_pr(self):
        """preview_tags() must add PR tag."""
        src = _read_source("constants.py")
        assert '"PR"' in src


# ===========================================================================
# 2. preview.py — must use tags from constants
# ===========================================================================


class TestPreviewTags:
    """preview.py must import and use tag helpers from constants."""

    def test_imports_from_constants(self):
        src = _read_source("preview.py")
        assert "from constants import" in src
        assert "preview_tags" in src

    def test_security_group_uses_preview_tags(self):
        """SG tags must include cost tags, not just Name/PR."""
        src = _read_source("preview.py")
        assert "preview_tags(" in src

    def test_service_has_tags(self):
        """ECS Service tags must include cost tags (via _tags variable)."""
        src = _read_source("preview.py")
        # Service should use tags derived from preview_tags
        assert "tags=_tags" in src or "tags={" in src


# ===========================================================================
# 3. frontend_preview.py — must use tags from constants
# ===========================================================================


class TestFrontendPreviewTags:
    """frontend_preview.py must import and use tag helpers from constants."""

    def test_imports_from_constants(self):
        src = _read_source("frontend_preview.py")
        assert "from constants import" in src
        assert "preview_tags" in src

    def test_bucket_uses_preview_tags(self):
        src = _read_source("frontend_preview.py")
        assert "preview_tags(" in src

    def test_distribution_has_tags(self):
        """CloudFront Distribution tags must include cost tags."""
        src = _read_source("frontend_preview.py")
        # Both bucket and distribution should use _tags derived from preview_tags
        assert src.count("**_tags") >= 2


# ===========================================================================
# 4. cleanup.py — must use cost_tags from constants
# ===========================================================================


class TestCleanupTags:
    """cleanup.py must import cost_tags and tag its resources."""

    def test_imports_cost_tags(self):
        src = _read_source("cleanup.py")
        assert "cost_tags" in src
        assert "from constants import" in src

    def test_lambda_has_tags(self):
        src = _read_source("cleanup.py")
        # Lambda function should have tags= argument
        assert "tags=" in src


# ===========================================================================
# 5. stale_cleanup.py — must use cost_tags from constants
# ===========================================================================


class TestStaleCleanupTags:
    """stale_cleanup.py must import cost_tags and tag its resources."""

    def test_imports_cost_tags(self):
        src = _read_source("stale_cleanup.py")
        assert "cost_tags" in src
        assert "from constants import" in src

    def test_lambda_has_tags(self):
        src = _read_source("stale_cleanup.py")
        lines = src.split("\n")
        # Find the Lambda Function resource and check it has tags
        in_lambda = False
        has_tags = False
        for line in lines:
            if "aws.lambda_.Function(" in line:
                in_lambda = True
            if in_lambda and "tags=" in line:
                has_tags = True
                break
            if in_lambda and line.strip() == ")":
                break
        assert has_tags, "stale_cleanup Lambda must have tags= argument"
