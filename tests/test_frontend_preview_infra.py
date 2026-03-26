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


# ---------------------------------------------------------------------------
# S3 + CloudFront hardening tests (#241)
# ---------------------------------------------------------------------------


def test_bucket_policy_uses_json_dumps():
    """Bucket policy must be built with json.dumps, not f-string."""
    src = _frontend_preview_source()
    assert "import json" in src or "from json import" in src, "frontend_preview.py must import json"
    assert "json.dumps(" in src, "Bucket policy must use json.dumps instead of f-string"


def test_bucket_name_includes_stack():
    """S3 bucket name must include pulumi.get_stack() to avoid collisions."""
    src = _frontend_preview_source()
    assert "pulumi.get_stack()" in src, "Bucket name must include pulumi.get_stack() for collision avoidance"


def test_bucket_force_destroy():
    """S3 bucket must set force_destroy=True for easy cleanup."""
    src = _frontend_preview_source()
    assert "force_destroy=True" in src, "S3 bucket must have force_destroy=True"


def test_bucket_default_encryption():
    """S3 bucket must have default encryption (SSE-S3) configured."""
    src = _frontend_preview_source()
    assert "BucketServerSideEncryptionConfigurationV2(" in src or ("ServerSideEncryptionConfiguration(" in src), (
        "S3 bucket must have default encryption configured"
    )
    assert "aws:s3" in src or "AES256" in src, "S3 bucket encryption must use SSE-S3 (AES256)"


def test_cloudfront_price_class_100():
    """CloudFront distribution must use PriceClass_100 for cost savings."""
    src = _frontend_preview_source()
    assert "PriceClass_100" in src, "CloudFront distribution must set price_class to PriceClass_100"


def test_bucket_public_access_block_defined():
    """BucketPublicAccessBlock must block all public access."""
    src = _frontend_preview_source()
    assert "BucketPublicAccessBlock(" in src, "frontend_preview.py must define BucketPublicAccessBlock"
    assert "block_public_acls=True" in src, "Must block public ACLs"
    assert "block_public_policy=True" in src, "Must block public policy"
    assert "ignore_public_acls=True" in src, "Must ignore public ACLs"
    assert "restrict_public_buckets=True" in src, "Must restrict public buckets"


def test_origin_access_control_defined():
    """OriginAccessControl must be defined with correct settings."""
    src = _frontend_preview_source()
    assert "OriginAccessControl(" in src, "frontend_preview.py must define OriginAccessControl"
    assert 'signing_behavior="always"' in src, "OAC must sign always"
    assert 'signing_protocol="sigv4"' in src, "OAC must use sigv4"


def test_export_keys_strict():
    """Export keys must follow strict naming conventions."""
    src = _frontend_preview_source()
    # Must export bucket_name and cdn_domain with exact keys
    assert '"frontend_preview_bucket_name"' in src or "'frontend_preview_bucket_name'" in src, (
        "Must export 'frontend_preview_bucket_name'"
    )
    assert '"frontend_preview_cdn_domain"' in src or "'frontend_preview_cdn_domain'" in src, (
        "Must export 'frontend_preview_cdn_domain'"
    )
