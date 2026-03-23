"""Tests for myxo verify command."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from myxo.cli import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helper: create a minimal .myxo/ directory with config.yaml
# ---------------------------------------------------------------------------

def _create_myxo_dir(base: Path) -> Path:
    """Create a minimal .myxo/ directory with a config that specifies a repo."""
    myxo = base / ".myxo"
    myxo.mkdir()
    (myxo / "config.yaml").write_text(
        'version: "0.1"\n'
        "github:\n"
        "  repo: owner/repo\n"
        "  labels:\n"
        '    - name: "bug"\n'
        '      color: "d73a4a"\n'
        '    - name: "enhancement"\n'
        '      color: "a2eeef"\n'
        "  branch_protection:\n"
        "    branch: main\n"
        "    required_reviews: 1\n"
        "    dismiss_stale_reviews: true\n"
        "  secrets:\n"
        "    - DEPLOY_KEY\n"
        "    - API_TOKEN\n"
    )
    return myxo


# ---------------------------------------------------------------------------
# 1. .myxo/ が無い場合はエラー終了
# ---------------------------------------------------------------------------

def test_verify_fails_without_myxo_dir(tmp_path: Path, monkeypatch):
    """verify should fail with exit code 1 when .myxo/ does not exist."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["verify"])
    assert result.exit_code == 1
    assert ".myxo" in result.stdout.lower()


# ---------------------------------------------------------------------------
# 2. --fix オプションが受け付けられる
# ---------------------------------------------------------------------------

def test_verify_accepts_fix_option(tmp_path: Path, monkeypatch):
    """verify --fix should be accepted as a valid option."""
    monkeypatch.chdir(tmp_path)
    _create_myxo_dir(tmp_path)

    with patch("myxo.cli._run_verify", return_value=0):
        result = runner.invoke(app, ["verify", "--fix"])
    # Should NOT fail with "no such option" error
    assert "no such option" not in result.stdout.lower()


# ---------------------------------------------------------------------------
# 3. 全チェック OK → exit code 0
# ---------------------------------------------------------------------------

def test_verify_all_ok_exit_code_zero(tmp_path: Path, monkeypatch):
    """verify should exit 0 when all checks pass."""
    monkeypatch.chdir(tmp_path)
    _create_myxo_dir(tmp_path)

    mock_verifier = AsyncMock()
    mock_verifier.check_labels.return_value = [
        _make_result("label: bug", "ok", "exists"),
        _make_result("label: enhancement", "ok", "exists"),
    ]
    mock_verifier.check_branch_protection.return_value = [
        _make_result("branch_protection: main", "ok", "configured"),
    ]
    mock_verifier.check_secrets.return_value = [
        _make_result("secret: DEPLOY_KEY", "ok", "configured"),
        _make_result("secret: API_TOKEN", "ok", "configured"),
    ]

    with patch("myxo.cli._create_verifier", return_value=mock_verifier):
        result = runner.invoke(app, ["verify"])

    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# 4. NG あり → exit code 1
# ---------------------------------------------------------------------------

def test_verify_with_failures_exit_code_one(tmp_path: Path, monkeypatch):
    """verify should exit 1 when any check fails."""
    monkeypatch.chdir(tmp_path)
    _create_myxo_dir(tmp_path)

    mock_verifier = AsyncMock()
    mock_verifier.check_labels.return_value = [
        _make_result("label: bug", "ok", "exists"),
        _make_result("label: enhancement", "fail", "missing"),
    ]
    mock_verifier.check_branch_protection.return_value = [
        _make_result("branch_protection: main", "ok", "configured"),
    ]
    mock_verifier.check_secrets.return_value = [
        _make_result("secret: DEPLOY_KEY", "fail", "not found"),
    ]

    with patch("myxo.cli._create_verifier", return_value=mock_verifier):
        result = runner.invoke(app, ["verify"])

    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# 5. 結果テーブルに各チェック項目が表示される
# ---------------------------------------------------------------------------

def test_verify_output_shows_check_results(tmp_path: Path, monkeypatch):
    """verify should display check results including name and status."""
    monkeypatch.chdir(tmp_path)
    _create_myxo_dir(tmp_path)

    mock_verifier = AsyncMock()
    mock_verifier.check_labels.return_value = [
        _make_result("label: bug", "ok", "exists"),
        _make_result("label: enhancement", "fail", "missing"),
    ]
    mock_verifier.check_branch_protection.return_value = [
        _make_result("branch_protection: main", "warn", "reviews < 2"),
    ]
    mock_verifier.check_secrets.return_value = [
        _make_result("secret: DEPLOY_KEY", "ok", "configured"),
    ]

    with patch("myxo.cli._create_verifier", return_value=mock_verifier):
        result = runner.invoke(app, ["verify"])

    output = result.stdout.lower()
    assert "bug" in output
    assert "enhancement" in output
    assert "branch_protection" in output
    assert "deploy_key" in output


# ---------------------------------------------------------------------------
# 6. --fix が呼ばれたとき fix メソッドが実行される
# ---------------------------------------------------------------------------

def test_verify_fix_calls_fix_methods(tmp_path: Path, monkeypatch):
    """verify --fix should call fix methods when failures exist."""
    monkeypatch.chdir(tmp_path)
    _create_myxo_dir(tmp_path)

    mock_verifier = AsyncMock()
    mock_verifier.check_labels.return_value = [
        _make_result("label: bug", "fail", "missing"),
    ]
    mock_verifier.check_branch_protection.return_value = []
    mock_verifier.check_secrets.return_value = []
    mock_verifier.fix_labels.return_value = None

    with patch("myxo.cli._create_verifier", return_value=mock_verifier):
        result = runner.invoke(app, ["verify", "--fix"])

    mock_verifier.fix_labels.assert_called_once()


# ---------------------------------------------------------------------------
# 7. GitHubVerifier の CheckResult dataclass
# ---------------------------------------------------------------------------

def test_check_result_dataclass():
    """CheckResult should have name, status, and message fields."""
    from myxo.verifier import CheckResult

    cr = CheckResult(name="test", status="ok", message="all good")
    assert cr.name == "test"
    assert cr.status == "ok"
    assert cr.message == "all good"


def test_check_result_status_literal():
    """CheckResult status should accept ok, fail, warn."""
    from myxo.verifier import CheckResult

    for status in ("ok", "fail", "warn"):
        cr = CheckResult(name="x", status=status, message="m")
        assert cr.status == status


# ---------------------------------------------------------------------------
# 8. GitHubVerifier.check_labels — API モック
# ---------------------------------------------------------------------------

def test_verifier_check_labels_all_present(tmp_path: Path):
    """check_labels should return ok for labels that exist on GitHub."""
    from myxo.verifier import CheckResult, GitHubVerifier

    verifier = GitHubVerifier(token="fake-token")

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"name": "bug", "color": "d73a4a"},
        {"name": "enhancement", "color": "a2eeef"},
        {"name": "documentation", "color": "0075ca"},
    ]

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        import asyncio
        results = asyncio.run(
            verifier.check_labels("owner/repo", [
                {"name": "bug", "color": "d73a4a"},
                {"name": "enhancement", "color": "a2eeef"},
            ])
        )

    assert len(results) == 2
    assert all(r.status == "ok" for r in results)


def test_verifier_check_labels_missing(tmp_path: Path):
    """check_labels should return fail for labels that do not exist."""
    from myxo.verifier import CheckResult, GitHubVerifier

    verifier = GitHubVerifier(token="fake-token")

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"name": "bug", "color": "d73a4a"},
    ]

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        import asyncio
        results = asyncio.run(
            verifier.check_labels("owner/repo", [
                {"name": "bug", "color": "d73a4a"},
                {"name": "enhancement", "color": "a2eeef"},
            ])
        )

    assert len(results) == 2
    ok_results = [r for r in results if r.status == "ok"]
    fail_results = [r for r in results if r.status == "fail"]
    assert len(ok_results) == 1
    assert len(fail_results) == 1
    assert fail_results[0].name == "label: enhancement"


# ---------------------------------------------------------------------------
# 9. GitHubVerifier.check_branch_protection — API モック
# ---------------------------------------------------------------------------

def test_verifier_check_branch_protection_ok():
    """check_branch_protection should return ok when protection matches config."""
    from myxo.verifier import GitHubVerifier

    verifier = GitHubVerifier(token="fake-token")

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "required_pull_request_reviews": {
            "required_approving_review_count": 1,
            "dismiss_stale_reviews": True,
        },
    }

    config = {
        "branch": "main",
        "required_reviews": 1,
        "dismiss_stale_reviews": True,
    }

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        import asyncio
        results = asyncio.run(
            verifier.check_branch_protection("owner/repo", config)
        )

    assert any(r.status == "ok" for r in results)


def test_verifier_check_branch_protection_not_configured():
    """check_branch_protection should return fail when no protection exists."""
    from myxo.verifier import GitHubVerifier

    verifier = GitHubVerifier(token="fake-token")

    mock_response = AsyncMock()
    mock_response.status_code = 404

    config = {
        "branch": "main",
        "required_reviews": 1,
        "dismiss_stale_reviews": True,
    }

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        import asyncio
        results = asyncio.run(
            verifier.check_branch_protection("owner/repo", config)
        )

    assert any(r.status == "fail" for r in results)


# ---------------------------------------------------------------------------
# 10. GitHubVerifier.check_secrets — API モック
# ---------------------------------------------------------------------------

def test_verifier_check_secrets_all_present():
    """check_secrets should return ok for all secrets that exist."""
    from myxo.verifier import GitHubVerifier

    verifier = GitHubVerifier(token="fake-token")

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "secrets": [
            {"name": "DEPLOY_KEY"},
            {"name": "API_TOKEN"},
        ],
    }

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        import asyncio
        results = asyncio.run(
            verifier.check_secrets("owner/repo", ["DEPLOY_KEY", "API_TOKEN"])
        )

    assert len(results) == 2
    assert all(r.status == "ok" for r in results)


def test_verifier_check_secrets_missing():
    """check_secrets should return fail for missing secrets."""
    from myxo.verifier import GitHubVerifier

    verifier = GitHubVerifier(token="fake-token")

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "secrets": [
            {"name": "DEPLOY_KEY"},
        ],
    }

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        import asyncio
        results = asyncio.run(
            verifier.check_secrets("owner/repo", ["DEPLOY_KEY", "API_TOKEN"])
        )

    ok_results = [r for r in results if r.status == "ok"]
    fail_results = [r for r in results if r.status == "fail"]
    assert len(ok_results) == 1
    assert len(fail_results) == 1
    assert fail_results[0].name == "secret: API_TOKEN"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_result(name: str, status: str, message: str):
    """Create a mock CheckResult-like object."""
    from unittest.mock import MagicMock

    r = MagicMock()
    r.name = name
    r.status = status
    r.message = message
    return r
