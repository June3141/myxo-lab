"""ECR repository for Myxo container images."""

import pulumi_aws as aws
from constants import cost_tags

_COST_TAGS = cost_tags(cost_center="ai-agent")

ecr = aws.ecr

# --- ECR Repository ----------------------------------------------------------
repo = ecr.Repository(
    "myxo-base-repo",
    name="myxo-base",
    image_tag_mutability="MUTABLE",
    force_delete=False,
    image_scanning_configuration=ecr.RepositoryImageScanningConfigurationArgs(
        scan_on_push=True,
    ),
    tags=_COST_TAGS,
)
