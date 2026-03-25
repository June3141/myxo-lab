"""Tests for linter configuration files and pre-commit hooks."""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PRECOMMIT_PATH = ROOT / ".pre-commit-config.yaml"
YAMLLINT_PATH = ROOT / ".yamllint.yaml"
TYPOS_PATH = ROOT / "_typos.toml"
MARKDOWNLINT_PATH = ROOT / ".markdownlint.yaml"
HADOLINT_PATH = ROOT / ".hadolint.yaml"
WORKFLOWS_DIR = ROOT / ".github" / "workflows"


def _load_precommit() -> dict:
    data = yaml.safe_load(PRECOMMIT_PATH.read_text())
    assert isinstance(data, dict)
    return data


def _hook_ids(data: dict) -> list[str]:
    ids = []
    for repo in data.get("repos", []):
        for hook in repo.get("hooks", []):
            ids.append(hook["id"])
    return ids


# ── pre-commit hooks ──


def test_precommit_has_yamllint():
    ids = _hook_ids(_load_precommit())
    assert "yamllint" in ids


def test_precommit_has_actionlint():
    ids = _hook_ids(_load_precommit())
    assert "actionlint" in ids


def test_precommit_has_shellcheck():
    ids = _hook_ids(_load_precommit())
    assert "shellcheck" in ids


def test_precommit_has_hadolint():
    ids = _hook_ids(_load_precommit())
    has_hadolint = "hadolint" in ids or "hadolint-docker" in ids
    assert has_hadolint


def test_precommit_has_typos():
    ids = _hook_ids(_load_precommit())
    assert "typos" in ids


def test_precommit_has_markdownlint():
    ids = _hook_ids(_load_precommit())
    has_mdlint = any("markdownlint" in i for i in ids)
    assert has_mdlint


# ── config files ──


def test_yamllint_config_exists():
    assert YAMLLINT_PATH.is_file()


def test_typos_config_exists():
    assert TYPOS_PATH.is_file()


def test_markdownlint_config_exists():
    assert MARKDOWNLINT_PATH.is_file()


def test_hadolint_config_exists():
    assert HADOLINT_PATH.is_file()


# ── CI workflows ──


def test_typos_workflow_exists():
    assert (WORKFLOWS_DIR / "typos.yml").is_file()


def test_typos_workflow_sha_pinned():
    content = (WORKFLOWS_DIR / "typos.yml").read_text()
    assert re.search(r"crate-ci/typos@[0-9a-f]{40}", content)
