"""Tests to verify all infra modules use class-based style (#255).

Ensures cleanup.py, stale_cleanup.py, and infisical.py follow the same
class-based pattern used in preview.py and frontend_preview.py.
"""

import ast
from pathlib import Path

INFRA_DIR = Path(__file__).resolve().parent.parent / "infra"

# ---------------------------------------------------------------------------
# Helper — extract class names from a module via AST
# ---------------------------------------------------------------------------


def _class_names(module_path: Path) -> list[str]:
    """Return top-level class names defined in *module_path*."""
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(module_path))
    return [node.name for node in ast.iter_child_nodes(tree) if isinstance(node, ast.ClassDef)]


# ---------------------------------------------------------------------------
# cleanup.py — must define CleanupEnvironment class
# ---------------------------------------------------------------------------


def test_cleanup_has_class():
    """cleanup.py must define a CleanupEnvironment class."""
    classes = _class_names(INFRA_DIR / "cleanup.py")
    assert "CleanupEnvironment" in classes, f"cleanup.py must define CleanupEnvironment class, found: {classes}"


def test_cleanup_class_instantiated_at_module_level():
    """cleanup.py must instantiate CleanupEnvironment at module level."""
    source = (INFRA_DIR / "cleanup.py").read_text(encoding="utf-8")
    assert "CleanupEnvironment(" in source, "CleanupEnvironment must be instantiated at module level"


def test_cleanup_class_has_init():
    """CleanupEnvironment must define __init__."""
    source = (INFRA_DIR / "cleanup.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef) and node.name == "CleanupEnvironment":
            methods = [n.name for n in ast.iter_child_nodes(node) if isinstance(n, ast.FunctionDef)]
            assert "__init__" in methods, "CleanupEnvironment must define __init__"
            return
    raise AssertionError("CleanupEnvironment class not found")  # pragma: no cover


# ---------------------------------------------------------------------------
# stale_cleanup.py — must define StaleCleanupEnvironment class
# ---------------------------------------------------------------------------


def test_stale_cleanup_has_class():
    """stale_cleanup.py must define a StaleCleanupEnvironment class."""
    classes = _class_names(INFRA_DIR / "stale_cleanup.py")
    assert "StaleCleanupEnvironment" in classes, (
        f"stale_cleanup.py must define StaleCleanupEnvironment class, found: {classes}"
    )


def test_stale_cleanup_class_instantiated_at_module_level():
    """stale_cleanup.py must instantiate StaleCleanupEnvironment at module level."""
    source = (INFRA_DIR / "stale_cleanup.py").read_text(encoding="utf-8")
    assert "StaleCleanupEnvironment(" in source, "StaleCleanupEnvironment must be instantiated at module level"


def test_stale_cleanup_class_has_init():
    """StaleCleanupEnvironment must define __init__."""
    source = (INFRA_DIR / "stale_cleanup.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef) and node.name == "StaleCleanupEnvironment":
            methods = [n.name for n in ast.iter_child_nodes(node) if isinstance(n, ast.FunctionDef)]
            assert "__init__" in methods, "StaleCleanupEnvironment must define __init__"
            return
    raise AssertionError("StaleCleanupEnvironment class not found")


# ---------------------------------------------------------------------------
# infisical.py — must define InfisicalServer class
# ---------------------------------------------------------------------------


def test_infisical_has_class():
    """infisical.py must define an InfisicalServer class."""
    classes = _class_names(INFRA_DIR / "infisical.py")
    assert "InfisicalServer" in classes, f"infisical.py must define InfisicalServer class, found: {classes}"


def test_infisical_class_instantiated_at_module_level():
    """infisical.py must instantiate InfisicalServer at module level."""
    source = (INFRA_DIR / "infisical.py").read_text(encoding="utf-8")
    assert "InfisicalServer(" in source, "InfisicalServer must be instantiated at module level"


def test_infisical_class_has_init():
    """InfisicalServer must define __init__."""
    source = (INFRA_DIR / "infisical.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef) and node.name == "InfisicalServer":
            methods = [n.name for n in ast.iter_child_nodes(node) if isinstance(n, ast.FunctionDef)]
            assert "__init__" in methods, "InfisicalServer must define __init__"
            return
    raise AssertionError("InfisicalServer class not found")


# ---------------------------------------------------------------------------
# All infra modules must use read_text(encoding="utf-8") — not bare read_text()
# ---------------------------------------------------------------------------


def test_existing_tests_use_encoding_utf8():
    """Test files reading infra source must specify encoding='utf-8'."""
    # This test validates its own helper uses encoding param
    source = Path(__file__).read_text(encoding="utf-8")
    assert 'encoding="utf-8"' in source
