"""Tests meta — LEGACY-POLICY-001 : audit du support legacy dans le core.

Vérifie que le rapport d'audit existe, couvre les points requis, et confirme
que les starters ne dépendent plus du format legacy.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

AUDIT = Path("docs/history/audits/legacy-support-core-audit-001.md")
STARTERS_DIR = Path("forge_cli/starters/data")

LEGACY_KEYS = [
    "format_version",
    "sql_type",
    "python_type",
    "primary_key",
    "auto_increment",
    "from_entity",
    "to_entity",
    "foreign_key_name",
]

MIGRATED_STARTERS = [
    "contact-simple",
    "utilisateurs-auth",
    "carnet-contacts",
    "suivi-comportement-eleves",
    "communes-sejours",
]


def _audit() -> str:
    return AUDIT.read_text(encoding="utf-8")


# ── Rapport ────────────────────────────────────────────────────────────────────


def test_audit_existe():
    assert AUDIT.exists()


def test_audit_mentionne_format_version():
    assert "format_version" in _audit()


def test_audit_mentionne_legacy():
    assert "legacy" in _audit()


def test_audit_mentionne_build_model():
    content = _audit()
    assert "build:model" in content or "build_model" in content


def test_audit_mentionne_entity_validate():
    assert "entity:validate" in _audit()


def test_audit_mentionne_les_starters():
    content = _audit()
    for starter in MIGRATED_STARTERS:
        assert starter in content or "starters" in content


def test_audit_confirme_starters_sans_legacy():
    content = _audit()
    assert "0 occurrence" in content or "plus du format legacy" in content


def test_audit_mentionne_risques_suppression():
    content = _audit()
    assert "Risques si suppression" in content or "risque" in content.lower()


def test_audit_propose_legacy_policy_002():
    assert "LEGACY-POLICY-002" in _audit()


def test_audit_ne_dit_pas_support_supprime():
    content = _audit()
    assert "support legacy supprimé" not in content
    assert "legacy supprimé" not in content


def test_audit_mentionne_trois_options():
    content = _audit()
    assert "Option A" in content
    assert "Option B" in content
    assert "Option C" in content


def test_audit_mentionne_canonical_model_normalizer():
    assert "canonical_model_normalizer" in _audit()


# ── Vérification starters sans legacy ─────────────────────────────────────────


@pytest.mark.parametrize("starter", MIGRATED_STARTERS)
def test_starter_sans_trace_legacy(starter):
    starter_dir = STARTERS_DIR / starter
    entity_files = [
        p for p in starter_dir.rglob("*.json")
        if p.name != "starter.json"
        and "__pycache__" not in p.parts
        and "seed" not in p.parts
        and "translations" not in p.parts
    ]
    for f in entity_files:
        content = f.read_text(encoding="utf-8")
        for key in LEGACY_KEYS:
            assert key not in content, (
                f"Clé legacy '{key}' trouvée dans {f.relative_to(STARTERS_DIR)}"
            )
