"""Syntax validation for all Python files in the project."""
import ast
import os
import pytest


def get_all_python_files():
    """Collect all .py files in the project (excluding tests and __pycache__)."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    py_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (
            "__pycache__", ".git", "node_modules", ".claude", ".venv",
            "venv", "env", ".env",
        )]
        for f in filenames:
            if f.endswith(".py"):
                py_files.append(os.path.join(dirpath, f))
    return py_files


@pytest.mark.parametrize(
    "filepath",
    get_all_python_files(),
    ids=lambda p: os.path.relpath(p),
)
def test_syntax_valid(filepath):
    """Every Python file must parse without syntax errors."""
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
    ast.parse(source, filename=filepath)
