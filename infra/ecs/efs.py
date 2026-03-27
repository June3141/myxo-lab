"""EFS file system and access point for Nix store cache."""

import pulumi_aws as aws
from constants import cost_tags

_COST_TAGS = cost_tags(cost_center="ai-agent")

# --- EFS: Nix store cache ----------------------------------------------------
nix_cache_fs = aws.efs.FileSystem(
    "myxo-nix-cache",
    encrypted=True,
    performance_mode="generalPurpose",
    tags={"Name": "myxo-nix-cache", **_COST_TAGS},
)

nix_cache_ap = aws.efs.AccessPoint(
    "myxo-nix-cache-ap",
    file_system_id=nix_cache_fs.id,
    posix_user=aws.efs.AccessPointPosixUserArgs(uid=1000, gid=1000),
    root_directory=aws.efs.AccessPointRootDirectoryArgs(
        path="/nix-store",
        creation_info=aws.efs.AccessPointRootDirectoryCreationInfoArgs(
            owner_uid=1000,
            owner_gid=1000,
            permissions="755",
        ),
    ),
    tags={"Name": "myxo-nix-cache-ap", **_COST_TAGS},
)

# TODO(#137): Add EFS Mount Target once VPC/subnet resources are available.
# aws.efs.MountTarget("myxo-nix-cache-mt", ...)
