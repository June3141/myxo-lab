"""Tests for standardized resource tagging strategy (#250).

Verifies:
- Required tags are defined in constants.py
- cost_tags() includes ManagedBy tag
- preview_tags() helper exists for ephemeral resources
- Preview modules (preview.py, frontend_preview.py) use cost tags from constants
- Cleanup modules reference the correct AutoDelete tag key from constants
"""

import ast
from pathlib import Path

INFRA_DIR = Path(__file__).resolve().parent.parent / "infra"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _read_source(filename: str) -> str:
    return (INFRA_DIR / filename).read_text(encoding="utf-8")


def _parse_module(filename: str) -> ast.Module:
    return ast.parse(_read_source(filename))


def _get_dict_keys(node: ast.Dict) -> list[str]:
    """Extract string keys from an ast.Dict node."""
    return [k.value for k in node.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)]


def _find_assignment_dict(tree: ast.Module, name: str) -> ast.Dict | None:
    """Find a top-level assignment like `NAME = {...}` and return the Dict node.

    Handles both plain assignment (ast.Assign) and annotated assignment (ast.AnnAssign).
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name and isinstance(node.value, ast.Dict):
                    return node.value
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
            and node.value is not None
            and isinstance(node.value, ast.Dict)
        ):
            return node.value
    return None


def _find_function_def(tree: ast.Module, name: str) -> ast.FunctionDef | None:
    """Find a top-level function definition by name."""
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _find_all_list(tree: ast.Module) -> list[str]:
    """Extract entries from __all__ = [...]."""
    # __all__ is a List, not a Dict — walk the tree directly
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__" and isinstance(node.value, ast.List):
                    return [
                        elt.value
                        for elt in node.value.elts
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                    ]
    return []


def _find_keyword_call(src: str, func_name: str, keyword: str) -> bool:
    """Check if a function/constructor call includes a specific keyword argument."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_str = ast.unparse(node.func)
            if func_name in func_str:
                for kw in node.keywords:
                    if kw.arg == keyword:
                        return True
    return False


# ===========================================================================
# 1. constants.py — required tag keys & helper functions (ast-based)
# ===========================================================================


class TestConstantsRequiredTags:
    """COST_TAGS and cost_tags() must include all mandatory keys."""

    def test_cost_tags_dict_has_project(self):
        tree = _parse_module("constants.py")
        cost_dict = _find_assignment_dict(tree, "COST_TAGS")
        assert cost_dict is not None, "COST_TAGS dict must exist"
        assert "Project" in _get_dict_keys(cost_dict)

    def test_cost_tags_dict_has_environment(self):
        tree = _parse_module("constants.py")
        cost_dict = _find_assignment_dict(tree, "COST_TAGS")
        assert cost_dict is not None
        assert "Environment" in _get_dict_keys(cost_dict)

    def test_cost_tags_dict_has_managed_by(self):
        """ManagedBy tag must be in COST_TAGS base dict."""
        tree = _parse_module("constants.py")
        cost_dict = _find_assignment_dict(tree, "COST_TAGS")
        assert cost_dict is not None
        assert "ManagedBy" in _get_dict_keys(cost_dict)

    def test_cost_tags_function_adds_cost_center(self):
        tree = _parse_module("constants.py")
        func = _find_function_def(tree, "cost_tags")
        assert func is not None, "cost_tags() function must exist"
        func_src = ast.unparse(func)
        assert "CostCenter" in func_src

    def test_preview_tags_function_exists(self):
        """preview_tags() helper must be defined for ephemeral resources."""
        tree = _parse_module("constants.py")
        func = _find_function_def(tree, "preview_tags")
        assert func is not None, "preview_tags() function must be defined"

    def test_preview_tags_in_all(self):
        """preview_tags must be exported in __all__."""
        tree = _parse_module("constants.py")
        all_entries = _find_all_list(tree)
        assert "preview_tags" in all_entries

    def test_preview_tags_includes_auto_delete(self):
        """preview_tags() must add AutoDelete tag."""
        tree = _parse_module("constants.py")
        func = _find_function_def(tree, "preview_tags")
        assert func is not None
        func_src = ast.unparse(func)
        assert "AutoDelete" in func_src

    def test_preview_tags_includes_pr(self):
        """preview_tags() must add PR tag."""
        tree = _parse_module("constants.py")
        func = _find_function_def(tree, "preview_tags")
        assert func is not None
        func_src = ast.unparse(func)
        assert "'PR'" in func_src or '"PR"' in func_src


# ===========================================================================
# 2. preview.py — must use tags from constants
# ===========================================================================


class TestPreviewTags:
    """preview.py must import and use tag helpers from constants."""

    def test_imports_from_constants(self):
        src = _read_source("preview.py")
        assert "from constants import" in src
        assert "preview_tags" in src

    def test_security_group_uses_preview_tags(self):
        """SG tags must include cost tags, not just Name/PR."""
        src = _read_source("preview.py")
        assert "preview_tags(" in src

    def test_service_has_tags(self):
        """ECS Service must have tags= keyword argument."""
        src = _read_source("preview.py")
        assert _find_keyword_call(src, "Service", "tags"), "preview.py ECS Service must have tags= argument"


# ===========================================================================
# 3. frontend_preview.py — must use tags from constants
# ===========================================================================


class TestFrontendPreviewTags:
    """frontend_preview.py must import and use tag helpers from constants."""

    def test_imports_from_constants(self):
        src = _read_source("frontend_preview.py")
        assert "from constants import" in src
        assert "preview_tags" in src

    def test_bucket_uses_preview_tags(self):
        src = _read_source("frontend_preview.py")
        assert "preview_tags(" in src

    def test_distribution_has_tags(self):
        """CloudFront Distribution tags must include cost tags."""
        src = _read_source("frontend_preview.py")
        assert _find_keyword_call(src, "Distribution", "tags"), (
            "frontend_preview.py Distribution must have tags= argument"
        )


# ===========================================================================
# 4. cleanup.py — must use cost_tags from constants
# ===========================================================================


class TestCleanupTags:
    """cleanup.py must import cost_tags and tag its resources."""

    def test_imports_cost_tags(self):
        src = _read_source("cleanup.py")
        assert "cost_tags" in src
        assert "from constants import" in src

    def test_lambda_has_tags(self):
        src = _read_source("cleanup.py")
        assert _find_keyword_call(src, "Function", "tags"), "cleanup.py Lambda Function must have tags= argument"


# ===========================================================================
# 5. stale_cleanup.py — must use cost_tags from constants
# ===========================================================================


class TestStaleCleanupTags:
    """stale_cleanup.py must import cost_tags and tag its resources."""

    def test_imports_cost_tags(self):
        src = _read_source("stale_cleanup.py")
        assert "cost_tags" in src
        assert "from constants import" in src

    def test_lambda_has_tags(self):
        src = _read_source("stale_cleanup.py")
        assert _find_keyword_call(src, "Function", "tags"), "stale_cleanup.py Lambda Function must have tags= argument"
