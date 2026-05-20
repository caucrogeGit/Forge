"""Tests meta — VSCODE-DX-001 : configuration VS Code JSON schemas.

Vérifie que la documentation VS Code est présente et cohérente :
- la page de documentation existe ;
- les schémas entity, relations, rbac sont mentionnés ;
- les commandes CLI de validation sont documentées ;
- VS Code est présenté comme complémentaire, pas de remplacement ;
- mkdocs.yml référence la page.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

DOC = Path("docs/entities/vscode-json-schema.md")
MKDOCS = Path("mkdocs.yml")
VSCODE_SETTINGS = Path(".vscode/settings.json")


def _text() -> str:
    return DOC.read_text(encoding="utf-8")


# ── Existence ──────────────────────────────────────────────────────────────────


def test_doc_vscode_json_schema_existe():
    assert DOC.exists()


def test_vscode_settings_json_existe():
    assert VSCODE_SETTINGS.exists()


# ── Contenu de la documentation ───────────────────────────────────────────────


def test_doc_mentionne_json_schemas():
    assert "json.schemas" in _text()


def test_doc_mentionne_entity_schema_json():
    assert "entity.schema.json" in _text()


def test_doc_mentionne_relations_schema_json():
    assert "relations.schema.json" in _text()


def test_doc_mentionne_rbac_schema_json():
    assert "rbac.schema.json" in _text()


def test_doc_mentionne_schema_doctor():
    assert "schema:doctor" in _text()


def test_doc_mentionne_entity_validate():
    assert "entity:validate" in _text()


def test_doc_mentionne_rbac_validate():
    assert "rbac:validate" in _text()


def test_doc_dit_vscode_ne_remplace_pas_cli():
    text = _text()
    assert "ne remplace pas" in text.lower() or "ne remplace pas" in text


# ── Contenu de .vscode/settings.json ─────────────────────────────────────────


def test_vscode_settings_contient_json_schemas():
    text = VSCODE_SETTINGS.read_text(encoding="utf-8")
    assert "json.schemas" in text


def test_vscode_settings_couvre_entity_json():
    text = VSCODE_SETTINGS.read_text(encoding="utf-8")
    assert "entity.schema.json" in text
    assert "mvc/entities" in text


def test_vscode_settings_couvre_relations_json():
    text = VSCODE_SETTINGS.read_text(encoding="utf-8")
    assert "relations.schema.json" in text
    assert "relations.json" in text


def test_vscode_settings_couvre_rbac_json():
    text = VSCODE_SETTINGS.read_text(encoding="utf-8")
    assert "rbac.schema.json" in text
    assert "mvc/security/rbac.json" in text


# ── mkdocs.yml référence la page ──────────────────────────────────────────────


def test_mkdocs_reference_vscode_page():
    mkdocs_text = MKDOCS.read_text(encoding="utf-8")
    assert "vscode-json-schema.md" in mkdocs_text or "vscode-json-schemas.md" in mkdocs_text
