"""S3 + CloudFront frontend preview environment infrastructure tests.

Validates that the frontend preview Pulumi module defines the expected
resources for PR-specific static frontend hosting (#72).
"""

from pathlib import Path

INFRA_DIR = Path(__file__).resolve().parent.parent / "infra"


def test_frontend_preview_module_exists():
    """infra/frontend_preview.py must exist."""
    assert (INFRA_DIR / "frontend_preview.py").is_file(), "infra/frontend_preview.py must exist"


# ---------------------------------------------------------------------------
# Resource definitions in frontend_preview.py
# ---------------------------------------------------------------------------


def _frontend_preview_source() -> str:
    return (INFRA_DIR / "frontend_preview.py").read_text()


def test_frontend_preview_imports_pulumi_aws():
    """frontend_preview.py must import pulumi_aws."""
    src = _frontend_preview_source()
    assert "pulumi_aws" in src, "frontend_preview.py must import pulumi_aws"


def test_defines_s3_bucket():
    """frontend_preview.py must define an S3 Bucket resource."""
    src = _frontend_preview_source()
    assert "aws.s3.BucketV2(" in src or "s3.BucketV2(" in src, "frontend_preview.py must define an S3 BucketV2"


def test_defines_cloudfront_distribution():
    """frontend_preview.py must define a CloudFront Distribution resource."""
    src = _frontend_preview_source()
    assert "cloudfront.Distribution(" in src or "aws.cloudfront.Distribution(" in src, (
        "frontend_preview.py must define a CloudFront Distribution"
    )


def test_parameterized_by_pr_number():
    """FrontendPreviewEnvironment must accept a PR number parameter."""
    src = _frontend_preview_source()
    assert "pr_number" in src, "FrontendPreviewEnvironment must be parameterized by pr_number"


def test_exports_cloudfront_domain():
    """frontend_preview.py must export the CloudFront domain name."""
    src = _frontend_preview_source()
    assert "pulumi.export(" in src, "frontend_preview.py must export a value"
    assert "domain" in src.lower(), "frontend_preview.py must export a CloudFront domain"


def test_main_imports_frontend_preview_module():
    """__main__.py must import the frontend_preview module."""
    main_src = (INFRA_DIR / "__main__.py").read_text()
    assert "frontend_preview" in main_src, "__main__.py must import the frontend_preview module"
