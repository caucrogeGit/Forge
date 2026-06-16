"""Garde-fou CORE-TYPING-PYRIGHT-BASELINE-001 (ADR-036).

Le cœur est typé et vérifié par pyright en CI. Ce garde-fou verrouille
l'**outillage** (pas le résultat, qui est lancé par la CI) :

- config `[tool.pyright]` dans pyproject (périmètre `core`, mode au moins basic) ;
- marqueur PEP 561 `core/py.typed` exposant les types aux projets utilisateurs,
  inclus dans le wheel (package-data) ;
- `pyright` déclaré en dépendance de développement ;
- une étape pyright dans la CI.

Le cliquet (ADR-036) étendra ensuite le périmètre (integrations, opt-ins) et la
strictness (`# pyright: strict`) module par module.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ROOT = Path(__file__).parent.parent.parent


def _pyproject() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_config_pyright_couvre_core():
    cfg = _pyproject().get("tool", {}).get("pyright", {})
    assert cfg, "[tool.pyright] doit exister dans pyproject.toml (ADR-036)."
    assert "core" in cfg.get("include", []), "pyright doit couvrir core/."
    assert cfg.get("typeCheckingMode") in ("basic", "standard", "strict")


def test_core_py_typed_present():
    assert (ROOT / "core" / "py.typed").is_file(), (
        "core/py.typed (PEP 561) manquant : sans lui, les types du cœur sont "
        "ignorés dans les projets utilisateurs."
    )


def test_py_typed_dans_package_data():
    pd = _pyproject()["tool"]["setuptools"]["package-data"]
    assert "py.typed" in pd.get("core", []), (
        "core/py.typed doit figurer dans package-data pour être inclus au wheel."
    )


def test_pyright_declare_en_dep_dev():
    assert "pyright" in (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")


def test_ci_execute_pyright():
    assert "pyright" in (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
