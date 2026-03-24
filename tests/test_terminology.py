"""Tests for 4-layer model terminology in project documentation.

Verifies that the metaphor terms follow the 4-layer model:
- Person layer: Researcher, Fellow (was Protocol-as-agent)
- Device layer: Microscope (was Assay), Recorder (was Report/Scribe)
- Artifact layer: Hypothesis, Protocol (document), Experiment, etc.
- Environment layer: Petri, Publication, LabNote, etc.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


# --- Deprecated term detection ---


class TestDeprecatedAgentNames:
    """Ensure deprecated agent names are no longer used."""

    @pytest.mark.small
    def test_readme_no_assay_as_agent(self):
        """Assay (agent) should be renamed to Microscope in README."""
        content = (ROOT / "README.md").read_text()
        # "Assay" should not appear as a role/agent name
        assert "**Assay**" not in content
        assert "Assay" not in content

    @pytest.mark.small
    def test_readme_no_report_as_agent(self):
        """Report (agent) should be renamed to Recorder in README."""
        content = (ROOT / "README.md").read_text()
        # "Report" as an agent role should not appear
        assert "**Report**" not in content

    @pytest.mark.small
    def test_readme_no_scribe_as_agent(self):
        """Scribe should not appear anywhere in README."""
        content = (ROOT / "README.md").read_text()
        assert "Scribe" not in content

    @pytest.mark.small
    def test_skill_docs_no_assay_as_agent(self):
        """Assay agent name should not appear in skill docs."""
        skills_dir = ROOT / ".claude" / "skills"
        for md_file in skills_dir.rglob("*.md"):
            content = md_file.read_text()
            # "Assay" as agent reference should be replaced with Microscope
            assert "Assay" not in content, (
                f"Found deprecated 'Assay' in {md_file.relative_to(ROOT)}"
            )


# --- New term presence ---


class TestNewAgentNames:
    """Ensure the new 4-layer model agent names are present."""

    @pytest.mark.small
    def test_readme_has_microscope_role(self):
        """Microscope should appear as a role in README."""
        content = (ROOT / "README.md").read_text()
        assert "**Microscope**" in content

    @pytest.mark.small
    def test_readme_has_recorder_role(self):
        """Recorder should appear as a role in README."""
        content = (ROOT / "README.md").read_text()
        assert "**Recorder**" in content

    @pytest.mark.small
    def test_readme_has_fellow_role(self):
        """Fellow should appear as a role in README."""
        content = (ROOT / "README.md").read_text()
        assert "**Fellow**" in content

    @pytest.mark.small
    def test_readme_protocol_still_exists_as_artifact(self):
        """Protocol should still exist as an artifact/document concept."""
        content = (ROOT / "README.md").read_text()
        assert "Protocol" in content


# --- 4-Layer model ---


class TestFourLayerModel:
    """Ensure the 4-layer model is documented in README."""

    @pytest.mark.small
    def test_readme_has_person_layer(self):
        content = (ROOT / "README.md").read_text()
        assert "Person" in content

    @pytest.mark.small
    def test_readme_has_device_layer(self):
        content = (ROOT / "README.md").read_text()
        assert "Device" in content

    @pytest.mark.small
    def test_readme_has_artifact_layer(self):
        content = (ROOT / "README.md").read_text()
        assert "Artifact" in content

    @pytest.mark.small
    def test_readme_has_environment_layer(self):
        content = (ROOT / "README.md").read_text()
        # "Environment" already in the section header
        assert "Environment" in content


# --- Mermaid diagram ---


class TestMermaidDiagram:
    """Ensure Mermaid diagram uses new terminology."""

    @pytest.mark.small
    def test_mermaid_uses_fellow_not_protocol(self):
        """In the execution flow, the director agent should be Fellow."""
        content = (ROOT / "README.md").read_text()
        assert "Fellow" in content
        # The old Protocol agent label in Mermaid should be gone
        assert '🧪 Protocol' not in content

    @pytest.mark.small
    def test_mermaid_uses_microscope_not_assay(self):
        """In the execution flow, the reviewer agent should be Microscope."""
        content = (ROOT / "README.md").read_text()
        assert "Microscope" in content
        assert '🔬 Assay' not in content


# --- Skill docs updated ---


class TestSkillDocsUpdated:
    """Ensure skill docs use new terminology."""

    @pytest.mark.small
    def test_pr_rules_uses_fellow(self):
        content = (
            ROOT / ".claude" / "skills" / "pr-rules" / "SKILL.md"
        ).read_text()
        assert "Fellow" in content

    @pytest.mark.small
    def test_pr_rules_uses_microscope(self):
        content = (
            ROOT / ".claude" / "skills" / "pr-rules" / "SKILL.md"
        ).read_text()
        assert "Microscope" in content

    @pytest.mark.small
    def test_commit_rules_uses_fellow(self):
        content = (
            ROOT / ".claude" / "skills" / "commit-rules" / "SKILL.md"
        ).read_text()
        assert "Fellow" in content
