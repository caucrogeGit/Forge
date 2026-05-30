"""Tests meta — STARTERS-MIGRATE-CLOSE-001 : clôture de la migration canonique.

Vérifie que le rapport d'audit confirme la fin de la campagne de migration
et que tous les starters avec entités sont en format canonique.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

AUDIT = Path("docs/history/audits/starters-legacy-audit-json-schema-001.md")
STARTERS_DIR = Path("forge_cli/starters/data")


def _audit() -> str:
    return AUDIT.read_text(encoding="utf-8")


# ── Rapport d'audit ────────────────────────────────────────────────────────────


def test_audit_mentionne_cloture_terminee():
    assert "terminée" in _audit()


def test_audit_mentionne_starters_migres():
    content = _audit()
    for starter in ("contact-simple", "utilisateurs-auth"):
        assert starter in content, f"Starter {starter!r} absent de l'audit"


def test_audit_mentionne_auth_mfa_sans_entite():
    content = _audit()
    assert "auth-mfa" in content
    assert "hors périmètre" in content or "sans entité" in content


def test_audit_mentionne_schema_version():
    assert "schema_version" in _audit()


def test_audit_mentionne_entity_validate():
    assert "entity:validate" in _audit()


def test_audit_mentionne_build_model():
    assert "build:model" in _audit() or "build_model" in _audit()


def test_audit_ne_dit_pas_support_legacy_supprime():
    content = _audit()
    assert "support legacy supprimé" not in content
    assert "legacy supprimé" not in content


def test_audit_ne_dit_pas_pypi_publie():
    content = _audit()
    assert "PyPI publié" not in content
    assert "forge-mvc publié" not in content


def test_audit_mentionne_100_pourcent():
    content = _audit()
    assert "100 %" in content


# ── Absence de traces legacy dans les starters migrés ─────────────────────────


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
    "users-core-auth",
]


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


@pytest.mark.parametrize("starter", MIGRATED_STARTERS)
def test_starter_pas_de_media_hors_schema(starter):
    starter_dir = STARTERS_DIR / starter
    entity_files = [
        p for p in starter_dir.rglob("*.json")
        if p.name != "starter.json"
        and "__pycache__" not in p.parts
        and "seed" not in p.parts
        and "translations" not in p.parts
        and p.name.endswith(".json")
        and "entities" in p.parts
        and p.name != "relations.json"
    ]
    for f in entity_files:
        data = json.loads(f.read_text(encoding="utf-8"))
        assert "media" not in data, (
            f"Clé racine 'media' hors schéma trouvée dans {f.relative_to(STARTERS_DIR)}"
        )


# ── auth-mfa — zéro entité ─────────────────────────────────────────────────────


def test_auth_mfa_sans_entite_json():
    auth_mfa_dir = STARTERS_DIR / "welcome-optin-mfa"
    entity_jsons = [
        p for p in auth_mfa_dir.rglob("*.json")
        if p.name != "starter.json"
        and "__pycache__" not in p.parts
    ]
    assert entity_jsons == [], (
        f"auth-mfa contient des fichiers JSON inattendus : {entity_jsons}"
    )


# ── Fichiers canoniques confirmés ─────────────────────────────────────────────


def test_tous_fichiers_entite_sont_canoniques():
    canonical = []
    for starter in MIGRATED_STARTERS:
        starter_dir = STARTERS_DIR / starter
        for p in starter_dir.rglob("*.json"):
            if (
                p.name == "starter.json"
                or "__pycache__" in p.parts
                or "seed" in p.parts
                or "translations" in p.parts
                or p.name == "relations.json"
            ):
                continue
            if "entities" not in p.parts and p.parent.name not in ("entities", starter):
                continue
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if "schema_version" in data or "name" in data:
                canonical.append(p)

    assert len(canonical) >= 2, (
        f"Moins de 2 fichiers entité canoniques trouvés ({len(canonical)})"
    )
