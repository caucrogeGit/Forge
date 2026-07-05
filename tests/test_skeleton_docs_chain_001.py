"""SKELETON-STANDARDS-CONFORMANCE-001 / T3 (ADR-063) — chaîne documentaire.

`forge new` livre par défaut de quoi documenter le projet : un `mkdocs.yml`
(thème Material, français, navigation automatique), un `requirements-docs.txt`
(chaîne MkDocs), et une page d'accueil `docs/index.md`.

La navigation est volontairement automatique (aucune clé `nav`) pour rester
valide sous `mkdocs build --strict` quel que soit le contenu ajouté à `docs/`,
notamment `docs/adr/` posé par `forge agents:init`.
"""
from __future__ import annotations

from pathlib import Path

import yaml

SKELETON = Path(__file__).parent.parent / "cli" / "skeleton" / "data"


def _mkdocs() -> dict[str, object]:
    return yaml.safe_load((SKELETON / "mkdocs.yml").read_text(encoding="utf-8"))


# ── mkdocs.yml : Material, français, nav automatique ─────────────────────────

def test_squelette_livre_mkdocs():
    assert (SKELETON / "mkdocs.yml").is_file(), "cli/skeleton/data/mkdocs.yml attendu (ADR-063)"


def test_mkdocs_material_francais():
    config = _mkdocs()
    assert config.get("site_name"), "site_name attendu"
    theme = config["theme"]
    assert isinstance(theme, dict)
    assert theme["name"] == "material"
    assert theme["language"] == "fr"


def test_mkdocs_navigation_automatique():
    # Pas de clé nav : la navigation est construite depuis l'arborescence, ce
    # qui garde `mkdocs build --strict` vert quand docs/adr/ s'ajoute.
    assert "nav" not in _mkdocs(), "le squelette ne fige pas de nav (nav automatique)"


# ── requirements-docs.txt + page d'accueil ───────────────────────────────────

def test_requirements_docs_livre_mkdocs_material():
    reqs = SKELETON / "requirements-docs.txt"
    assert reqs.is_file(), "cli/skeleton/data/requirements-docs.txt attendu (ADR-063)"
    assert "mkdocs-material" in reqs.read_text(encoding="utf-8")


def test_page_accueil_livree():
    assert (SKELETON / "docs" / "index.md").is_file(), "docs/index.md attendu (ADR-063)"
