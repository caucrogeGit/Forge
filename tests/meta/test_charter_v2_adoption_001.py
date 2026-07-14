"""Tests CHARTER-V2-ADOPTION-001 : presence et coherence des documents fondateurs.

Verifie que :
- CHARTE_DOC.md v2 est presente a la racine avec les principes attendus ;
- la charte v1 est archivee dans docs/history/ et marquee comme telle ;
- les 5 ADR (003-007) sont presents avec statut Accepte et section Decision ;
- README.md reference la charte v2 et les ADR.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]


CHARTER_PATH = Path("CHARTE_DOC.md")
HISTORY_DIR = Path("docs/history")
ADR_DIR = Path("docs/adr")
EXPECTED_ADRS = [
    "003-language-convention.md",
    "004-core-perimeter.md",
    "005-packaging.md",
    "006-python-version.md",
    "007-charter-v2-adoption.md",
]


# ---------------------------------------------------------------------------
# Classe 1 — Charte v2 a la racine
# ---------------------------------------------------------------------------


class TestCharterV2Present:

    def test_charter_v2_at_root(self):
        assert CHARTER_PATH.exists(), "CHARTE_DOC.md doit être présent à la racine"

    def test_charter_v2_mentions_principle_8(self):
        content = CHARTER_PATH.read_text(encoding="utf-8")
        assert "Noyau minimal, briques opt-in" in content

    def test_charter_v2_mentions_principle_11(self):
        content = CHARTER_PATH.read_text(encoding="utf-8")
        assert "Une seule façon" in content or "Une seule façon officielle" in content

    def test_charter_v2_mentions_evolution_rules(self):
        content = CHARTER_PATH.read_text(encoding="utf-8")
        assert "Règles d'évolution" in content

    def test_charter_v2_marks_v1_as_history(self):
        content = CHARTER_PATH.read_text(encoding="utf-8")
        assert "v1" in content.lower()

    def test_charter_v2_has_phrase_directrice(self):
        content = CHARTER_PATH.read_text(encoding="utf-8")
        assert "Phrase directrice" in content

    def test_charter_v2_has_formule_de_decision(self):
        content = CHARTER_PATH.read_text(encoding="utf-8")
        assert "Formule de décision" in content or "formule de décision" in content.lower()


# ---------------------------------------------------------------------------
# Classe 2 — Charte v1 archivee
# ---------------------------------------------------------------------------


class TestCharterV1Archived:

    def test_v1_in_history(self):
        v1_path = HISTORY_DIR / "charte-v1.md"
        assert v1_path.exists(), "La charte v1 doit être archivée dans docs/history/"

    def test_v1_marked_as_archived(self):
        v1_path = HISTORY_DIR / "charte-v1.md"
        content = v1_path.read_text(encoding="utf-8")
        assert "archivée" in content.lower() or "archived" in content.lower()

    def test_v1_references_v2(self):
        v1_path = HISTORY_DIR / "charte-v1.md"
        content = v1_path.read_text(encoding="utf-8")
        assert "CHARTE_DOC.md" in content or "charte v2" in content.lower()


# ---------------------------------------------------------------------------
# Classe 3 — 5 ADR presents et conformes
# ---------------------------------------------------------------------------


class TestAllAdrsPresent:

    @pytest.mark.parametrize("adr_filename", EXPECTED_ADRS)
    def test_adr_file_present(self, adr_filename):
        adr_path = ADR_DIR / adr_filename
        assert adr_path.exists(), f"ADR manquant : {adr_filename}"

    @pytest.mark.parametrize("adr_filename", EXPECTED_ADRS)
    def test_adr_has_status_accepted(self, adr_filename):
        adr_path = ADR_DIR / adr_filename
        content = adr_path.read_text(encoding="utf-8")
        assert "Statut" in content
        assert "Accepté" in content or "Accepted" in content

    @pytest.mark.parametrize("adr_filename", EXPECTED_ADRS)
    def test_adr_has_decision_section(self, adr_filename):
        adr_path = ADR_DIR / adr_filename
        content = adr_path.read_text(encoding="utf-8")
        assert "## Décision" in content

    @pytest.mark.parametrize("adr_filename", EXPECTED_ADRS)
    def test_adr_has_context_section(self, adr_filename):
        adr_path = ADR_DIR / adr_filename
        content = adr_path.read_text(encoding="utf-8")
        assert "## Contexte" in content

    @pytest.mark.parametrize("adr_filename", EXPECTED_ADRS)
    def test_adr_not_empty(self, adr_filename):
        adr_path = ADR_DIR / adr_filename
        content = adr_path.read_text(encoding="utf-8")
        assert len(content) > 500, f"{adr_filename} semble trop court"


# ---------------------------------------------------------------------------
# Classe 4 — README reference la charte et les ADR
# ---------------------------------------------------------------------------


class TestReadmeReferencesCharter:

    def test_readme_links_to_charter(self):
        readme = Path("README.md")
        if not readme.exists():
            pytest.skip("README.md absent")
        content = readme.read_text(encoding="utf-8")
        assert "CHARTE_DOC.md" in content or "charte" in content.lower()

    def test_readme_links_to_adrs(self):
        readme = Path("README.md")
        if not readme.exists():
            pytest.skip("README.md absent")
        content = readme.read_text(encoding="utf-8")
        assert "adr" in content.lower() or "ADR" in content
