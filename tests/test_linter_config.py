"""Tests for linter configuration files and pre-commit hooks."""

import re
from pathlib import Path

import pytest
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


# ── pre-commit hooks (exact match) ──

EXACT_HOOK_IDS = ["yamllint", "actionlint", "shellcheck", "typos"]


@pytest.mark.parametrize("hook_id", EXACT_HOOK_IDS)
def test_precommit_has_hook(hook_id: str):
    ids = _hook_ids(_load_precommit())
    assert hook_id in ids


def test_precommit_has_hadolint():
    ids = _hook_ids(_load_precommit())
    has_hadolint = "hadolint" in ids or "hadolint-docker" in ids
    assert has_hadolint


def test_precommit_has_markdownlint():
    ids = _hook_ids(_load_precommit())
    has_mdlint = any("markdownlint" in i for i in ids)
    assert has_mdlint


# ── config files ──

CONFIG_FILES = [
    pytest.param(YAMLLINT_PATH, id="yamllint"),
    pytest.param(TYPOS_PATH, id="typos"),
    pytest.param(MARKDOWNLINT_PATH, id="markdownlint"),
    pytest.param(HADOLINT_PATH, id="hadolint"),
]


@pytest.mark.parametrize("config_path", CONFIG_FILES)
def test_config_file_exists(config_path: Path):
    assert config_path.is_file()


# ── CI workflows ──


def test_typos_workflow_exists():
    assert (WORKFLOWS_DIR / "typos.yml").is_file()


def test_typos_workflow_sha_pinned():
    content = (WORKFLOWS_DIR / "typos.yml").read_text()
    assert re.search(r"crate-ci/typos@[0-9a-f]{40}", content)
