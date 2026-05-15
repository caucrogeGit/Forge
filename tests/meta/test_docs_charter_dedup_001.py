"""Tests DOCS-CHARTER-DEDUP-001 : charte v2 a une source canonique unique."""
from __future__ import annotations

from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CHARTER_ROOT = PROJECT_ROOT / "CHARTE_DOC.md"
CHARTER_DOCS = PROJECT_ROOT / "docs" / "charter.md"


class TestCanonicalCharter:
    """CHARTE_DOC.md à la racine est la source canonique."""

    def test_charter_root_exists(self):
        assert CHARTER_ROOT.exists()

    def test_charter_root_has_authority_note(self):
        content = CHARTER_ROOT.read_text(encoding="utf-8")
        assert "canonique" in content.lower(), (
            "CHARTE_DOC.md devrait porter une note d'autorité indiquant "
            "qu'il est le document canonique"
        )

    def test_charter_root_mentions_all_principles(self):
        """Vérification de complétude : les 11 principes sont présents."""
        content = CHARTER_ROOT.read_text(encoding="utf-8")
        for n in range(1, 12):
            assert f"### {n}." in content or f"## {n}." in content, (
                f"Principe {n} attendu dans CHARTE_DOC.md "
                f"(format ## {n}. ou ### {n}.)"
            )


class TestDocsCharterIsAlias:
    """docs/charter.md est un alias court vers la source canonique."""

    def test_charter_docs_exists(self):
        assert CHARTER_DOCS.exists()

    def test_charter_docs_is_short(self):
        content = CHARTER_DOCS.read_text(encoding="utf-8")
        line_count = len(content.splitlines())
        assert line_count < 50, (
            f"docs/charter.md fait {line_count} lignes — devrait être "
            f"un alias court (<50 lignes). La charte complète est "
            f"dans CHARTE_DOC.md à la racine."
        )

    def test_charter_docs_references_canonical(self):
        content = CHARTER_DOCS.read_text(encoding="utf-8")
        assert "CHARTE_DOC.md" in content, (
            "docs/charter.md devrait mentionner CHARTE_DOC.md à la racine"
        )


class TestNoLongerIdentical:
    """Les deux fichiers ne sont plus identiques par design."""

    def test_files_have_different_content(self):
        content_root = CHARTER_ROOT.read_text(encoding="utf-8")
        content_docs = CHARTER_DOCS.read_text(encoding="utf-8")
        assert content_root != content_docs, (
            "CHARTE_DOC.md et docs/charter.md devraient avoir un "
            "contenu différent : le premier est la source canonique "
            "(complète), le second est un alias court."
        )

    def test_root_is_substantially_larger(self):
        size_root = CHARTER_ROOT.stat().st_size
        size_docs = CHARTER_DOCS.stat().st_size
        assert size_root > size_docs * 3, (
            f"CHARTE_DOC.md ({size_root} octets) devrait être "
            f"substantiellement plus gros que docs/charter.md "
            f"({size_docs} octets). Si c'est presque pareil, la "
            f"déduplication n'a pas été faite correctement."
        )
