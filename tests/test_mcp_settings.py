"""Tests for MCP Tool Search settings in .claude/settings.json."""

import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).parent.parent / ".claude" / "settings.json"


def test_settings_json_exists():
    assert SETTINGS_FILE.is_file(), ".claude/settings.json must exist"


def test_settings_json_is_valid_json():
    content = SETTINGS_FILE.read_text()
    parsed = json.loads(content)
    assert isinstance(parsed, dict)


def test_enable_mcp_tool_search_is_true():
    content = SETTINGS_FILE.read_text()
    settings = json.loads(content)
    assert settings.get("enableMcpToolSearch") is True, "enableMcpToolSearch must be true"
