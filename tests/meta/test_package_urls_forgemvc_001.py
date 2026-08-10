"""Garde-fou PKG-DOCS-URLS-FORGEMVC-001.

La documentation officielle de Forge est hébergée sur ``forgemvc.com``.
L'ancien GitHub Pages (``caucrogegit.github.io/Forge``) ne doit plus
apparaître dans les métadonnées publiées : ni dans le ``pyproject.toml``
racine, ni dans ceux des packages opt-in (la page PyPI de chaque
distribution exposerait sinon un lien périmé).

Ce garde-fou aurait évité l'oubli des 5 packages lors de
``DOC-URLS-FORGEMVC-001`` (qui n'avait corrigé que le pyproject racine).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

PYPROJECTS = [PROJECT_ROOT / "pyproject.toml"] + sorted(
    PROJECT_ROOT.glob("packages/*/pyproject.toml")
)

_OBSOLETE_HOST = "caucrogegit.github.io"


@pytest.mark.parametrize("pyproject", PYPROJECTS, ids=lambda p: p.parent.name)
def test_no_obsolete_github_pages_url(pyproject):
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    urls = data.get("project", {}).get("urls", {})
    offenders = {k: v for k, v in urls.items() if _OBSOLETE_HOST in v}
    assert not offenders, (
        f"{pyproject.parent.name}/pyproject.toml référence l'ancien GitHub "
        f"Pages dans [project.urls] : {offenders}. Utiliser forgemvc.com."
    )


@pytest.mark.parametrize("pyproject", PYPROJECTS, ids=lambda p: p.parent.name)
def test_documentation_points_to_forgemvc(pyproject):
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    doc = data.get("project", {}).get("urls", {}).get("Documentation")
    # Exigée, non plus optionnelle (`TESTS-DEAD-SKIPS-REVIVE-001`). Le saut
    # d'origine avait laissé `forge-mvc-testing` sans URL de documentation
    # pendant que les vingt-six autres paquets la déclaraient : sa page PyPI
    # n'offrait aucun lien vers la doc. Un saut n'est pas un succès.
    assert doc is not None, (
        f"{pyproject.parent.name}/pyproject.toml ne déclare pas "
        "[project.urls] Documentation : sa page PyPI n'offrira aucun lien "
        "vers la documentation."
    )
    assert "forgemvc.com" in doc, (
        f"{pyproject.parent.name}/pyproject.toml : Documentation = {doc!r} "
        "devrait pointer vers forgemvc.com."
    )
