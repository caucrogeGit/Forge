"""Tests PRE-RELEASE-FIX-RBAC-IMPORT-001 : imports lazy des modules optionnels.

Vérifie que forge_cli, core et integrations ne contiennent aucun import
top-level vers forge_mvc_rbac, forge_mvc_mfa, forge_mvc_workflow, forge_mvc_stats.
Un import top-level dans le code framework rend la CLI inutilisable sans
les modules optionnels (bug découvert lors de PRE-RELEASE-AUDIT-3.0-001).
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]

_OPTIONAL_MODULES = {
    "forge_mvc_rbac",
    "forge_mvc_mfa",
    "forge_mvc_workflow",
    "forge_mvc_stats",
}

_FRAMEWORK_ROOTS = [
    PROJECT_ROOT / "forge_cli",
    PROJECT_ROOT / "core",
    PROJECT_ROOT / "integrations",
]

_APP_ROOTS = [
    PROJECT_ROOT / "mvc",
]


_EXCLUDED_DIRS = {
    PROJECT_ROOT / "forge_cli" / "starters" / "data",
}


def _collect_python_files(roots: list[Path]) -> list[Path]:
    files = []
    for root in roots:
        if root.is_dir():
            files.extend(
                p for p in root.rglob("*.py")
                if "__pycache__" not in p.parts
                and not any(p.is_relative_to(excl) for excl in _EXCLUDED_DIRS)
            )
    return files


def _top_level_optional_imports(path: Path) -> list[str]:
    """Retourne les imports top-level de modules optionnels dans un fichier."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []

    hits = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in _OPTIONAL_MODULES:
                    hits.append(f"{path.relative_to(PROJECT_ROOT)}:{node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in _OPTIONAL_MODULES:
                hits.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{node.lineno}: "
                    f"from {node.module} import ..."
                )
    return hits


class TestNoTopLevelOptionalImportsInFramework:
    """Le code framework ne contient aucun import top-level de module optionnel."""

    def test_forge_cli_no_top_level_optional_imports(self):
        files = _collect_python_files([PROJECT_ROOT / "forge_cli"])
        violations = []
        for f in files:
            violations.extend(_top_level_optional_imports(f))
        assert not violations, (
            "forge_cli/ contient des imports top-level de modules optionnels "
            "(rompt forge sans les extras) :\n" + "\n".join(violations)
        )

    def test_core_no_top_level_optional_imports(self):
        files = _collect_python_files([PROJECT_ROOT / "core"])
        violations = []
        for f in files:
            violations.extend(_top_level_optional_imports(f))
        assert not violations, (
            "core/ contient des imports top-level de modules optionnels :\n"
            + "\n".join(violations)
        )

    def test_integrations_no_top_level_optional_imports(self):
        files = _collect_python_files([PROJECT_ROOT / "integrations"])
        violations = []
        for f in files:
            violations.extend(_top_level_optional_imports(f))
        assert not violations, (
            "integrations/ contient des imports top-level de modules optionnels :\n"
            + "\n".join(violations)
        )


class TestForgeCLIBootsWithoutOptionalModules:
    """forge --version et forge --help fonctionnent sans modules optionnels."""

    def _run_forge(self, args: list[str]) -> subprocess.CompletedProcess:
        import os
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT)
        return subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "forge.py")] + args,
            capture_output=True,
            text=True,
            env=env,
        )

    def test_forge_version_no_crash(self):
        result = self._run_forge(["--version"])
        assert result.returncode == 0, (
            f"forge --version a planté (returncode={result.returncode}) :\n"
            f"{result.stderr}"
        )
        assert "Forge" in result.stdout, (
            f"forge --version n'affiche pas 'Forge' : {result.stdout!r}"
        )

    def test_forge_help_no_crash(self):
        result = self._run_forge(["--help"])
        assert result.returncode == 0, (
            f"forge --help a planté (returncode={result.returncode}) :\n"
            f"{result.stderr}"
        )

    def test_forge_no_module_not_found_error(self):
        result = self._run_forge(["--version"])
        assert "ModuleNotFoundError" not in result.stderr, (
            "forge --version lève ModuleNotFoundError — un module optionnel "
            "est importé au top-level :\n" + result.stderr
        )
        assert "ImportError" not in result.stderr, (
            "forge --version lève ImportError :\n" + result.stderr
        )
