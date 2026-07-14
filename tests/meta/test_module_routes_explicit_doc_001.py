"""Garde-fou méta MODULE-ROUTES-EXPLICIT-DOC-001.

Vérifie que la documentation des routes modules décrit correctement
le contrat explicite : generate_module_routes, pas d'injection automatique.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).parent.parent.parent
MODULE_AUTHOR_GUIDE = PROJECT_ROOT / "docs" / "philosophy" / "module-author-guide.md"
REFERENCE_MODULES = PROJECT_ROOT / "docs" / "reference" / "modules.md"


def _read(path: Path) -> str:
    if not path.exists():
        pytest.skip(f"{path.relative_to(PROJECT_ROOT)} introuvable")
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Contrat positif — ce que la doc doit mentionner
# ---------------------------------------------------------------------------

def test_guide_mentions_generate_module_routes():
    """Le guide auteur doit mentionner generate_module_routes ou module:routes."""
    src = _read(MODULE_AUTHOR_GUIDE)
    assert "module:routes" in src or "generate_module_routes" in src, (
        "docs/philosophy/module-author-guide.md doit documenter module:routes"
    )


def test_guide_mentions_dedicated_routes_file():
    """Le guide doit mentionner le fichier dédié mvc/routes_<module>.py."""
    src = _read(MODULE_AUTHOR_GUIDE)
    assert "mvc/routes_" in src, (
        "docs/philosophy/module-author-guide.md doit mentionner mvc/routes_<module>.py"
    )


def test_guide_mentions_explicit_lines_in_mvc_routes():
    """Le guide doit expliquer que le développeur ajoute les lignes dans mvc/routes/__init__.py."""
    src = _read(MODULE_AUTHOR_GUIDE)
    assert "mvc/routes/__init__.py" in src, (
        "docs/philosophy/module-author-guide.md doit mentionner mvc/routes/__init__.py"
    )


def test_guide_states_no_automatic_injection():
    """Le guide doit préciser que Forge ne modifie pas mvc/routes/__init__.py automatiquement."""
    src = _read(MODULE_AUTHOR_GUIDE)
    assert "ne modifie" in src or "pas automatiquement" in src or "manuellement" in src, (
        "docs/philosophy/module-author-guide.md doit indiquer que Forge ne modifie pas "
        "mvc/routes/__init__.py automatiquement"
    )


def test_guide_mentions_migration_section():
    """Le guide doit contenir une section sur la migration des anciens projets."""
    src = _read(MODULE_AUTHOR_GUIDE)
    assert "Migration" in src or "migration" in src, (
        "docs/philosophy/module-author-guide.md doit contenir une section migration"
    )


def test_reference_mentions_explicit_branchement():
    """La référence doit mentionner le branchement explicite."""
    src = _read(REFERENCE_MODULES)
    assert "mvc/routes_" in src, (
        "docs/reference/modules.md doit documenter mvc/routes_<module>.py"
    )


# ---------------------------------------------------------------------------
# Contrat négatif — ce que la doc ne doit plus recommander
# ---------------------------------------------------------------------------

def test_guide_does_not_recommend_prepare_injection():
    """Le guide ne doit pas recommander prepare_module_route_injection."""
    src = _read(MODULE_AUTHOR_GUIDE)
    assert "prepare_module_route_injection" not in src, (
        "docs/philosophy/module-author-guide.md ne doit pas référencer "
        "prepare_module_route_injection (supprimé en 6.1)"
    )


def test_guide_does_not_recommend_module_route_injection_result():
    """Le guide ne doit pas référencer ModuleRouteInjectionResult."""
    src = _read(MODULE_AUTHOR_GUIDE)
    assert "ModuleRouteInjectionResult" not in src, (
        "docs/philosophy/module-author-guide.md ne doit pas référencer ModuleRouteInjectionResult"
    )


def test_guide_does_not_describe_automatic_bridge_in_mvc_routes():
    """Le guide ne doit plus décrire un pont automatique injecté dans mvc/routes.py."""
    src = _read(MODULE_AUTHOR_GUIDE)
    assert "Forge ajoute aussi automatiquement le pont" not in src, (
        "docs/philosophy/module-author-guide.md ne doit plus décrire l'ajout automatique "
        "d'un pont dans mvc/routes.py"
    )


def test_reference_does_not_recommend_prepare_injection():
    """La référence ne doit pas référencer prepare_module_route_injection."""
    src = _read(REFERENCE_MODULES)
    assert "prepare_module_route_injection" not in src, (
        "docs/reference/modules.md ne doit pas référencer "
        "prepare_module_route_injection"
    )


def test_reference_does_not_recommend_module_route_injection_result():
    """La référence ne doit pas référencer ModuleRouteInjectionResult."""
    src = _read(REFERENCE_MODULES)
    assert "ModuleRouteInjectionResult" not in src, (
        "docs/reference/modules.md ne doit pas référencer ModuleRouteInjectionResult"
    )
