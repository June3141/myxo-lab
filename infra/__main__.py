"""Myxo Lab infrastructure definition."""

import pulumi
import pulumi_github  # noqa: F401

pulumi.export("status", "initialized")
