"""Garde-fou DOCS-RELEASE-SECTION-AUDIT-001.

Vérifie que la documentation release est consolidée et cohérente :
- les 4 docs actifs existent (2 process + 1 politique + 1 hub)
- le hub release-and-compatibility.md lie vers les docs process
- pas de prolifération de nouveaux docs release à la racine docs/
- chaque doc release est référencé dans mkdocs.yml

Structure attendue (4 docs actifs, aucun docs/release/ séparé) :
  docs/release/release.md                     — checklist process mainteneur
  docs/release/release-local.md               — validation wheel locale
  docs/release/release-policy.md              — politique SemVer Forge
  docs/release/release-and-compatibility.md   — hub de la section
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

_DOCS = Path("docs")
_HUB = _DOCS / "release" / "release-and-compatibility.md"

_REQUIRED_RELEASE_DOCS = [
    "release/release.md",
    "release/release-local.md",
    "release/release-policy.md",
    "release/release-and-compatibility.md",
]

# Seuil : ne pas dépasser ce nombre de docs release à la racine docs/
_MAX_RELEASE_DOCS_AT_ROOT = 4


class TestRequiredReleaseDocsExist:
    """Les 4 docs release attendus existent."""

    @pytest.mark.parametrize("filename", _REQUIRED_RELEASE_DOCS)
    def test_release_doc_exists(self, filename):
        assert (_DOCS / filename).exists(), (
            f"docs/{filename} doit exister — doc release actif attendu."
        )


class TestReleaseDocsInNav:
    """Chaque doc release est référencé dans mkdocs.yml."""

    @pytest.mark.parametrize("filename", _REQUIRED_RELEASE_DOCS)
    def test_release_doc_in_mkdocs(self, filename):
        mkdocs = Path("mkdocs.yml").read_text(encoding="utf-8")
        assert filename in mkdocs, (
            f"docs/{filename} doit apparaître dans la nav de mkdocs.yml."
        )


class TestReleaseHubIntegrity:
    """release-and-compatibility.md est un hub qui lie vers les docs process."""

    def test_hub_links_to_release_process(self):
        text = _HUB.read_text(encoding="utf-8")
        assert "release.md" in text, (
            f"{_HUB} doit lier vers release.md (checklist process)."
        )

    def test_hub_links_to_release_local(self):
        text = _HUB.read_text(encoding="utf-8")
        assert "release-local.md" in text, (
            f"{_HUB} doit lier vers release-local.md (validation locale)."
        )

    def test_hub_no_stale_version_qualifier(self):
        """Le hub ne doit pas mentionner une version Forge spécifique obsolète."""
        text = _HUB.read_text(encoding="utf-8")
        assert "Forge 2.x" not in text, (
            f"{_HUB} ne doit pas mentionner 'Forge 2.x' — utiliser 'Forge' sans qualifier."
        )


class TestNoReleaseDocProliferation:
    """Le nombre de docs release à la racine docs/ ne dépasse pas le seuil."""

    def test_release_docs_count_at_root(self):
        release_docs = [
            f for f in _DOCS.glob("release*.md")
        ]
        assert len(release_docs) <= _MAX_RELEASE_DOCS_AT_ROOT, (
            f"docs/ contient {len(release_docs)} docs release*.md "
            f"(max {_MAX_RELEASE_DOCS_AT_ROOT}). "
            "Les docs historiques doivent être migrés vers docs/history/release/."
        )
