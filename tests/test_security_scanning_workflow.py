"""Tests for security scanning workflow — Trivy/Checkov responsibility separation."""

from pathlib import Path

from helpers import load_workflow

ROOT = Path(__file__).resolve().parent.parent
SECURITY_WORKFLOW = ROOT / ".github" / "workflows" / "security.yml"
CONTAINER_WORKFLOW = ROOT / ".github" / "workflows" / "container-build.yml"


# ── security.yml — NO Trivy IaC ──


class TestSecurityWorkflowNoTrivyIac:
    def test_no_trivy_iac_job(self):
        data = load_workflow(SECURITY_WORKFLOW)
        jobs = data.get("jobs", {})
        trivy_iac_jobs = [k for k in jobs if "trivy" in k.lower() and "iac" in k.lower()]
        assert not trivy_iac_jobs, "security.yml must NOT have a Trivy IaC job"

    def test_no_trivy_config_scan_type(self):
        """No Trivy step with scan-type: config should exist in security.yml."""
        data = load_workflow(SECURITY_WORKFLOW)
        for job in data.get("jobs", {}).values():
            for step in job.get("steps", []):
                with_block = step.get("with", {})
                if "aquasecurity/trivy-action" in step.get("uses", ""):
                    assert with_block.get("scan-type") != "config", (
                        "security.yml must not have Trivy with scan-type: config"
                    )


# ── container-build.yml — Trivy vuln only ──


class TestContainerBuildTrivyVulnOnly:
    def test_trivy_uses_scanners_vuln(self):
        """container-build.yml Trivy step must explicitly use --scanners vuln."""
        data = load_workflow(CONTAINER_WORKFLOW)
        trivy_steps = []
        for job in data.get("jobs", {}).values():
            for step in job.get("steps", []):
                if "aquasecurity/trivy-action" in step.get("uses", ""):
                    trivy_steps.append(step)
        assert trivy_steps, "container-build.yml must have a Trivy step"
        for step in trivy_steps:
            with_block = step.get("with", {})
            scanners = with_block.get("scanners", "")
            assert scanners == "vuln", f"Trivy in container-build.yml must use scanners: vuln, got: {scanners!r}"
