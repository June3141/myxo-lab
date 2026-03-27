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


def _has_module_level_instantiation(module_path: Path, class_name: str) -> bool:
    """Check if *class_name* is instantiated at module level via AST.

    Looks for a top-level ``ast.Assign`` or ``ast.AnnAssign`` whose value
    is an ``ast.Call`` to *class_name*.
    """
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(module_path))
    for node in ast.iter_child_nodes(tree):
        call_node = None
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.Expr)) and isinstance(node.value, ast.Call):
            call_node = node.value
        if call_node is not None:
            func_name = ast.unparse(call_node.func)
            if func_name == class_name:
                return True
    return False


# ---------------------------------------------------------------------------
# cleanup.py — must define CleanupEnvironment class
# ---------------------------------------------------------------------------


def test_cleanup_has_class():
    """cleanup.py must define a CleanupEnvironment class."""
    classes = _class_names(INFRA_DIR / "cleanup.py")
    assert "CleanupEnvironment" in classes, f"cleanup.py must define CleanupEnvironment class, found: {classes}"


def test_cleanup_class_instantiated_at_module_level():
    """cleanup.py must instantiate CleanupEnvironment at module level."""
    assert _has_module_level_instantiation(INFRA_DIR / "cleanup.py", "CleanupEnvironment"), (
        "CleanupEnvironment must be instantiated at module level"
    )


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
    assert _has_module_level_instantiation(INFRA_DIR / "stale_cleanup.py", "StaleCleanupEnvironment"), (
        "StaleCleanupEnvironment must be instantiated at module level"
    )


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
    assert _has_module_level_instantiation(INFRA_DIR / "infisical.py", "InfisicalServer"), (
        "InfisicalServer must be instantiated at module level"
    )


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
# All read_text() calls in this test file must specify encoding="utf-8"
# ---------------------------------------------------------------------------


def test_existing_tests_use_encoding_utf8():
    """Every read_text() call in this file must specify encoding='utf-8'."""
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(Path(__file__)))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "read_text":
            encoding_kw = next((kw for kw in node.keywords if kw.arg == "encoding"), None)
            assert encoding_kw is not None, f"read_text() at line {node.lineno} must specify encoding='utf-8'"
            if isinstance(encoding_kw.value, ast.Constant):
                assert encoding_kw.value.value == "utf-8", (
                    f"read_text() at line {node.lineno}: encoding must be 'utf-8'"
                )
