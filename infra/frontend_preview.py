"""S3 + CloudFront frontend preview environment for PR-specific deployments (#72).

Creates an S3 bucket and CloudFront distribution per pull request, allowing
frontend preview before merge.  Uses Origin Access Control (OAC) for secure
S3 access.
"""

import json

import pulumi
import pulumi_aws as aws

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
config = pulumi.Config("frontend_preview")
pr_number = config.get_int("pr_number") or 0


# ---------------------------------------------------------------------------
# FrontendPreviewEnvironment
# ---------------------------------------------------------------------------
class FrontendPreviewEnvironment:
    """PR-specific S3 + CloudFront frontend preview.

    Parameters
    ----------
    pr_number:
        Pull-request number used to name and tag resources.
    """

    def __init__(self, pr_number: int) -> None:
        stack = pulumi.get_stack()
        name = f"myxo-fe-preview-{stack}-pr-{pr_number}"

        # --- S3 Bucket --------------------------------------------------------
        self.bucket = aws.s3.BucketV2(
            f"{name}-bucket",
            bucket=name,
            force_destroy=True,
            tags={"Name": name, "PR": str(pr_number)},
        )

        # --- S3 Default Encryption (SSE-S3) -----------------------------------
        aws.s3.BucketServerSideEncryptionConfigurationV2(
            f"{name}-encryption",
            bucket=self.bucket.id,
            rules=[
                aws.s3.BucketServerSideEncryptionConfigurationV2RuleArgs(
                    apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationV2RuleApplyServerSideEncryptionByDefaultArgs(
                        sse_algorithm="AES256",
                    ),
                ),
            ],
        )

        # Block all public access — CloudFront uses OAC
        aws.s3.BucketPublicAccessBlock(
            f"{name}-public-access-block",
            bucket=self.bucket.id,
            block_public_acls=True,
            block_public_policy=True,
            ignore_public_acls=True,
            restrict_public_buckets=True,
        )

        # --- Origin Access Control (OAC) -------------------------------------
        self.oac = aws.cloudfront.OriginAccessControl(
            f"{name}-oac",
            name=name,
            origin_access_control_origin_type="s3",
            signing_behavior="always",
            signing_protocol="sigv4",
        )

        # --- CloudFront Distribution -----------------------------------------
        self.distribution = aws.cloudfront.Distribution(
            f"{name}-cdn",
            enabled=True,
            default_root_object="index.html",
            origins=[
                aws.cloudfront.DistributionOriginArgs(
                    domain_name=self.bucket.bucket_regional_domain_name,
                    origin_id=f"s3-{name}",
                    origin_access_control_id=self.oac.id,
                ),
            ],
            default_cache_behavior=aws.cloudfront.DistributionDefaultCacheBehaviorArgs(
                allowed_methods=["GET", "HEAD"],
                cached_methods=["GET", "HEAD"],
                target_origin_id=f"s3-{name}",
                viewer_protocol_policy="redirect-to-https",
                forwarded_values=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesArgs(
                    query_string=False,
                    cookies=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesCookiesArgs(
                        forward="none",
                    ),
                ),
            ),
            restrictions=aws.cloudfront.DistributionRestrictionsArgs(
                geo_restriction=aws.cloudfront.DistributionRestrictionsGeoRestrictionArgs(
                    restriction_type="none",
                ),
            ),
            viewer_certificate=aws.cloudfront.DistributionViewerCertificateArgs(
                cloudfront_default_certificate=True,
            ),
            price_class="PriceClass_100",
            comment=f"Frontend preview for PR #{pr_number}",
            tags={"Name": name, "PR": str(pr_number)},
        )

        # --- S3 Bucket Policy (allow CloudFront OAC) -------------------------
        aws.s3.BucketPolicy(
            f"{name}-bucket-policy",
            bucket=self.bucket.id,
            policy=pulumi.Output.all(self.bucket.arn, self.distribution.arn).apply(
                lambda args: json.dumps(
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Sid": "AllowCloudFrontServicePrincipal",
                                "Effect": "Allow",
                                "Principal": {"Service": "cloudfront.amazonaws.com"},
                                "Action": "s3:GetObject",
                                "Resource": f"{args[0]}/*",
                                "Condition": {
                                    "StringEquals": {
                                        "AWS:SourceArn": args[1],
                                    }
                                },
                            }
                        ],
                    }
                )
            ),
        )

        self.domain_name = self.distribution.domain_name


# ---------------------------------------------------------------------------
# Instantiate only when a PR number is provided via config
# ---------------------------------------------------------------------------
if pr_number:
    preview = FrontendPreviewEnvironment(pr_number)

    pulumi.export("frontend_preview_bucket_name", preview.bucket.bucket)
    pulumi.export("frontend_preview_cdn_domain", preview.domain_name)
