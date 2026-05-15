"""Tests PRE-RELEASE-FIX-PYPROJECT-PYTHON-001 : alignement requires-python >= 3.12.

Vérifie que tous les pyproject.toml (racine + 4 modules) déclarent
requires-python >= 3.12 conformément à ADR-006, et qu'aucun ne contient
le classifier obsolète Python :: 3.11.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]

_ROOT_PYPROJECT = PROJECT_ROOT / "pyproject.toml"

_MODULE_PYPROJECTS = [
    PROJECT_ROOT / "packages" / "forge-mvc-mfa"      / "pyproject.toml",
    PROJECT_ROOT / "packages" / "forge-mvc-rbac"     / "pyproject.toml",
    PROJECT_ROOT / "packages" / "forge-mvc-stats"    / "pyproject.toml",
    PROJECT_ROOT / "packages" / "forge-mvc-workflow"  / "pyproject.toml",
]

_ALL_PYPROJECTS = [_ROOT_PYPROJECT] + _MODULE_PYPROJECTS


class TestRequiresPython312:
    """Tous les pyproject.toml déclarent requires-python >= 3.12."""

    def test_root_requires_python_312(self):
        content = _ROOT_PYPROJECT.read_text(encoding="utf-8")
        assert 'requires-python = ">=3.12"' in content, (
            f"pyproject.toml racine : requires-python doit être >=3.12 (ADR-006) — "
            f"trouvé : {[l for l in content.splitlines() if 'requires-python' in l]}"
        )

    @pytest.mark.parametrize("path", _MODULE_PYPROJECTS)
    def test_module_requires_python_312(self, path):
        content = path.read_text(encoding="utf-8")
        assert 'requires-python = ">=3.12"' in content, (
            f"{path.relative_to(PROJECT_ROOT)} : requires-python doit être >=3.12 (ADR-006)"
        )


class TestNo311Classifier:
    """Aucun pyproject.toml ne contient le classifier Python :: 3.11."""

    @pytest.mark.parametrize("path", _ALL_PYPROJECTS)
    def test_no_python_311_classifier(self, path):
        content = path.read_text(encoding="utf-8")
        assert "Python :: 3.11" not in content, (
            f"{path.relative_to(PROJECT_ROOT)} : classifier 'Python :: 3.11' "
            f"obsolète — Forge requiert Python 3.12+ (ADR-006)"
        )


class TestRuffTargetVersion:
    """Le tool.ruff target-version du root est aligné sur py312."""

    def test_ruff_target_version_py312(self):
        content = _ROOT_PYPROJECT.read_text(encoding="utf-8")
        assert 'target-version = "py312"' in content, (
            "pyproject.toml racine [tool.ruff] : target-version doit être py312"
        )
        assert 'target-version = "py311"' not in content, (
            "pyproject.toml racine : target-version py311 encore présent"
        )


class TestModulesHave313And314Classifiers:
    """Les 4 modules déclarent les classifiers Python 3.13 et 3.14."""

    @pytest.mark.parametrize("path", _MODULE_PYPROJECTS)
    def test_has_python_313_classifier(self, path):
        content = path.read_text(encoding="utf-8")
        assert "Python :: 3.13" in content, (
            f"{path.relative_to(PROJECT_ROOT)} : classifier 'Python :: 3.13' manquant"
        )

    @pytest.mark.parametrize("path", _MODULE_PYPROJECTS)
    def test_has_python_314_classifier(self, path):
        content = path.read_text(encoding="utf-8")
        assert "Python :: 3.14" in content, (
            f"{path.relative_to(PROJECT_ROOT)} : classifier 'Python :: 3.14' manquant"
        )
