"""ECS Cluster and Capacity Provider configuration."""

import pulumi_aws as aws
from constants import cost_tags

_COST_TAGS = cost_tags(cost_center="ai-agent")

ecs = aws.ecs

# --- ECS Cluster -------------------------------------------------------------
cluster = ecs.Cluster(
    "myxo-cluster",
    name="myxo-cluster",
    tags=_COST_TAGS,
)

# --- Fargate Spot Capacity Providers ----------------------------------------
ecs.ClusterCapacityProviders(
    "myxo-cluster-capacity-providers",
    cluster_name=cluster.name,
    capacity_providers=["FARGATE", "FARGATE_SPOT"],
    default_capacity_provider_strategies=[
        ecs.ClusterCapacityProvidersDefaultCapacityProviderStrategyArgs(
            capacity_provider="FARGATE_SPOT",
            weight=3,
            base=0,
        ),
        ecs.ClusterCapacityProvidersDefaultCapacityProviderStrategyArgs(
            capacity_provider="FARGATE",
            weight=1,
            base=1,
        ),
    ],
)
