"""Tests for security scanning workflow — Trivy/Checkov responsibility separation."""

from pathlib import Path

import yaml
from helpers import load_workflow

ROOT = Path(__file__).resolve().parent.parent
SECURITY_WORKFLOW = ROOT / ".github" / "workflows" / "security.yml"
CONTAINER_WORKFLOW = ROOT / ".github" / "workflows" / "container-build.yml"
CHECKOV_CONFIG = ROOT / ".checkov.yaml"
TASKFILE = ROOT / "Taskfile.yml"


# ── .checkov.yaml ──


class TestCheckovConfig:
    def test_checkov_config_exists(self):
        assert CHECKOV_CONFIG.is_file(), ".checkov.yaml must exist"

    def test_checkov_targets_infra_directory(self):
        data = yaml.safe_load(CHECKOV_CONFIG.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        directory = data.get("directory", [])
        # directory can be a list or a single string
        dirs = directory if isinstance(directory, list) else [directory]
        assert any("infra" in d for d in dirs), "Checkov must target infra/ directory"

    def test_checkov_framework_includes_python(self):
        data = yaml.safe_load(CHECKOV_CONFIG.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        framework = data.get("framework", [])
        frameworks = framework if isinstance(framework, list) else [framework]
        assert "python" in frameworks, "Checkov framework must include python"


# ── security.yml — Checkov step ──


class TestSecurityWorkflowCheckov:
    def test_has_checkov_job(self):
        data = load_workflow(SECURITY_WORKFLOW)
        jobs = data.get("jobs", {})
        checkov_jobs = [k for k in jobs if "checkov" in k]
        assert checkov_jobs, "security.yml must have a Checkov job"

    def test_checkov_job_uses_checkov_action_or_runs_checkov(self):
        data = load_workflow(SECURITY_WORKFLOW)
        jobs = data.get("jobs", {})
        checkov_jobs = {k: v for k, v in jobs.items() if "checkov" in k}
        assert checkov_jobs, "Must have a checkov job"
        for _name, job in checkov_jobs.items():
            steps = job.get("steps", [])
            has_checkov = any(
                ("bridgecrewio/checkov-action" in step.get("uses", "")) or ("checkov" in step.get("run", ""))
                for step in steps
            )
            assert has_checkov, "Checkov job must run Checkov"


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
            # Check either scanners key or scan-type key
            scanners = with_block.get("scanners", "")
            assert scanners == "vuln", f"Trivy in container-build.yml must use scanners: vuln, got: {scanners!r}"


# ── Taskfile — security:iac task ──


class TestTaskfileSecurityIac:
    def test_security_iac_task_exists(self):
        data = yaml.safe_load(TASKFILE.read_text(encoding="utf-8"))
        tasks = data.get("tasks", {})
        assert "security:iac" in tasks, "Taskfile must have security:iac task"

    def test_security_iac_runs_checkov(self):
        data = yaml.safe_load(TASKFILE.read_text(encoding="utf-8"))
        task = data["tasks"]["security:iac"]
        cmd = task.get("cmd", "")
        cmds = task.get("cmds", [])
        all_cmds = ([cmd] if cmd else []) + (cmds if isinstance(cmds, list) else [])
        has_checkov = any("checkov" in str(c) for c in all_cmds)
        assert has_checkov, "security:iac task must run checkov"
