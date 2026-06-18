"""Garde-fou DOCS-STRICT-VALIDATION-001 (partie 2/2).

Aucun fichier .md actif de docs/ ne doit être orphelin (présent sur disque
mais absent de mkdocs.yml).

Différence avec mkdocs build --strict :
- mkdocs émet des INFO (pas des erreurs) pour les pages hors-nav.
- En CI, personne ne lit les INFO. Ce test échoue explicitement.

Whitelist : voir EXCLUDED_DIRS et NAVLESS_FILES.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
MKDOCS_YML = PROJECT_ROOT / "mkdocs.yml"
DOCS_DIR = PROJECT_ROOT / "docs"

# Dossiers d'archives ou d'assets sans pages de navigation.
# logos/ : sources et exports PNG des logos Forge, pas des pages de documentation.
EXCLUDED_DIRS: set[str] = {"history", "audits", "logos"}

# Fichiers .md intentionnellement hors-nav (à documenter si on en ajoute).
NAVLESS_FILES: set[str] = {
    # Brouillon roadmap Contrats JSON Schema — prévu post-Phase 12, pas encore publié.
    "docs/roadmap/roadmap-forge-contrats-json-schema.md",
    # Spec d'exécution du ticket 7 (REMOVE-MEDIA-PKG, ADR-018) — brouillon en
    # attente de la publication PyPI de forge-mvc-images. Hors-nav volontairement.
    "docs/roadmap/ticket-remove-media-pkg.md",
    # Pages TEMPORAIRES du palier 3 vacances (2TNE CIEL, sans lien avec Forge) :
    # liées depuis vacances/palier-3/index.md et le dossier technique, mais hors
    # nav (équivalent markdown des PDF des paliers 1/2). À retirer avec tout le
    # dossier docs/vacances/ le 2026-06-28 (DOCS-WELCOME-VACANCE-TEMP-001).
    "docs/vacances/palier-3/palier-3-dossier-technique-reseau-virtualbox.md",
    "docs/vacances/palier-3/qcm-palier-3-reseau-virtualbox.md",
    "docs/vacances/palier-3/activite-palier-3-reseau-virtualbox.md",
    "docs/vacances/palier-3/checklist-professeur-palier-3-reseau-virtualbox.md",
}


def _md_files_on_disk() -> set[str]:
    files: set[str] = set()
    for md in DOCS_DIR.rglob("*.md"):
        if any(part in EXCLUDED_DIRS for part in md.parts):
            continue
        files.add(str(md.relative_to(PROJECT_ROOT)))
    return files


def _md_files_in_mkdocs() -> set[str]:
    if not MKDOCS_YML.exists():
        return set()
    text = MKDOCS_YML.read_text(encoding="utf-8")
    pat = re.compile(r"[\"\']?([a-zA-Z0-9_/.-]+\.md)[\"\']?")
    found: set[str] = set()
    for match in pat.findall(text):
        if not match.startswith("docs/"):
            match = f"docs/{match}"
        found.add(match)
    return found


class TestNoOrphanPagesInDocs:
    """Aucune page .md active n'est orpheline (hors nav mkdocs)."""

    def test_mkdocs_yml_exists(self):
        assert MKDOCS_YML.exists(), "mkdocs.yml doit exister à la racine."

    def test_at_least_some_pages_in_mkdocs(self):
        pages = _md_files_in_mkdocs()
        assert len(pages) >= 10, (
            f"mkdocs.yml référence trop peu de pages ({len(pages)}). "
            "Vérifier la regex d'extraction."
        )

    def test_no_orphan_md_files(self):
        on_disk = _md_files_on_disk()
        in_nav = _md_files_in_mkdocs()
        orphans = on_disk - in_nav - NAVLESS_FILES

        assert not orphans, (
            "Pages .md orphelines (sur disque mais absentes de mkdocs.yml) :\n"
            + "\n".join(f"  - {p}" for p in sorted(orphans))
            + "\n\nSoit ajouter à la nav dans mkdocs.yml, "
            "soit ajouter à NAVLESS_FILES dans ce test (avec justification)."
        )

    def test_no_dangling_nav_entries(self):
        all_on_disk: set[str] = set()
        for md in DOCS_DIR.rglob("*.md"):
            all_on_disk.add(str(md.relative_to(PROJECT_ROOT)))
        in_nav = _md_files_in_mkdocs()
        dangling = in_nav - all_on_disk

        assert not dangling, (
            "Entrées nav pointant sur des fichiers inexistants :\n"
            + "\n".join(f"  - {p}" for p in sorted(dangling))
            + "\n\nSoit créer le fichier, soit retirer l'entrée de mkdocs.yml."
        )
