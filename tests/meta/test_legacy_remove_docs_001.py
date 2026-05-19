"""Tests meta — LEGACY-REMOVE-004 : alignement de la documentation après suppression du legacy.

Vérifie que les pages utilisateur et ADR actuelles ne présentent plus le format legacy
comme supporté ou accepté. Les audits historiques (docs/history/audits/) peuvent conserver
des traces legacy par contexte — ils ne sont pas testés ici.
"""

import pytest

from pathlib import Path

pytestmark = pytest.mark.meta

DOCS_ROOT = Path(__file__).parent.parent.parent / "docs"
ADR_012 = DOCS_ROOT / "adr" / "012-legacy-format-deprecation-policy.md"
MIGRATION_GUIDE = DOCS_ROOT / "entities" / "migration-legacy-vers-canonique.md"
JSON_CANONIQUE = DOCS_ROOT / "entities" / "json-canonique.md"
ENTITY_VALIDATE = DOCS_ROOT / "entities" / "entity-validate.md"
LIMITES = DOCS_ROOT / "entities" / "limites-contrats-json.md"
LEGACY_REMOVE_PLAN = DOCS_ROOT / "history" / "audits" / "legacy-remove-plan-001.md"


# ── ADR-012 ───────────────────────────────────────────────────────────────────


def test_adr_012_exists():
    assert ADR_012.exists()


def test_adr_012_mentions_schema_version_obligatoire():
    text = ADR_012.read_text(encoding="utf-8")
    assert "schema_version" in text
    assert "1.0" in text


def test_adr_012_mentions_format_version_refusé():
    text = ADR_012.read_text(encoding="utf-8")
    assert "refusé" in text.lower() or "refus" in text.lower()


def test_adr_012_ne_dit_plus_supporté_temporairement():
    text = ADR_012.read_text(encoding="utf-8")
    # La section "Ancienne décision (archivée)" peut mentionner l'ancienne formulation.
    # Vérifier que la section "Décision" active ne dit plus que le legacy est accepté temporairement.
    decision_section = text.split("## Ancienne décision")[0]
    assert "supporté temporairement" not in decision_section
    assert "accepté temporairement" not in decision_section


def test_adr_012_mentionne_legacy_remove_tickets():
    text = ADR_012.read_text(encoding="utf-8")
    assert "LEGACY-REMOVE-001" in text
    assert "LEGACY-REMOVE-002" in text


# ── Guide de conversion ───────────────────────────────────────────────────────


def test_migration_guide_exists():
    assert MIGRATION_GUIDE.exists()


def test_migration_guide_avertit_que_legacy_est_refusé():
    text = MIGRATION_GUIDE.read_text(encoding="utf-8")
    assert "refusé" in text.lower() or "n'est plus accepté" in text.lower()


def test_migration_guide_ne_présente_pas_legacy_comme_déprécié_temporairement():
    text = MIGRATION_GUIDE.read_text(encoding="utf-8")
    assert "déprécié" not in text.split("---")[0]


# ── json-canonique ────────────────────────────────────────────────────────────


def test_json_canonique_ne_dit_pas_legacy_conservé_temporairement():
    text = JSON_CANONIQUE.read_text(encoding="utf-8")
    assert "conservé temporairement" not in text
    assert "supporté temporairement" not in text


def test_json_canonique_mentionne_schema_version():
    text = JSON_CANONIQUE.read_text(encoding="utf-8")
    assert 'schema_version' in text
    assert '"1.0"' in text


# ── entity-validate ───────────────────────────────────────────────────────────


def test_entity_validate_ne_dit_pas_legacy_accepté():
    text = ENTITY_VALIDATE.read_text(encoding="utf-8")
    assert "Le format legacy est accepté" not in text
    assert "accepté mais non recommandé" not in text


def test_entity_validate_mentionne_format_version_refusé():
    text = ENTITY_VALIDATE.read_text(encoding="utf-8")
    assert "refusé" in text.lower()


# ── limites-contrats-json ─────────────────────────────────────────────────────


def test_limites_ne_dit_pas_compatibilité_legacy_temporaire():
    text = LIMITES.read_text(encoding="utf-8")
    assert "Compatibilité legacy temporaire" not in text
    assert "conserve temporairement un chemin de compatibilité" not in text


def test_limites_mentionne_format_legacy_refusé():
    text = LIMITES.read_text(encoding="utf-8")
    assert "refusé" in text.lower()


# ── legacy-remove-plan ────────────────────────────────────────────────────────


def test_legacy_remove_plan_mentionne_legacy_remove_004():
    text = LEGACY_REMOVE_PLAN.read_text(encoding="utf-8")
    assert "LEGACY-REMOVE-004" in text
