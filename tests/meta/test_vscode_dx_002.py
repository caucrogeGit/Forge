"""Tests meta — VSCODE-DX-002 : validation de l'expérience VS Code JSON schemas.

Vérifie que .vscode/settings.json et la documentation DX sont cohérents et complets :
- les trois associations de schémas sont présentes ;
- la documentation couvre ce que VS Code valide et ne valide pas ;
- les commandes CLI complémentaires sont documentées ;
- une section dépannage est présente ;
- VS Code est présenté comme complémentaire, pas comme remplacement CLI.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

SETTINGS = Path(".vscode/settings.json")
DOC = Path("docs/entities/vscode-json-schema.md")


def _settings() -> str:
    return SETTINGS.read_text(encoding="utf-8")


def _doc() -> str:
    return DOC.read_text(encoding="utf-8")


# ── .vscode/settings.json ─────────────────────────────────────────────────────


def test_vscode_settings_existe():
    assert SETTINGS.exists()


def test_vscode_settings_contient_json_schemas():
    assert "json.schemas" in _settings()


def test_vscode_settings_reference_entity_schema():
    assert "entity.schema.json" in _settings()


def test_vscode_settings_reference_relations_schema():
    assert "relations.schema.json" in _settings()


def test_vscode_settings_reference_rbac_schema():
    assert "rbac.schema.json" in _settings()


# ── Documentation — ce que VS Code valide ────────────────────────────────────


def test_doc_mentionne_ce_que_vscode_valide():
    text = _doc()
    assert "VS Code peut détecter" in text or "VS Code valide" in text


def test_doc_mentionne_ce_que_vscode_ne_valide_pas():
    text = _doc()
    assert "ne remplace pas" in text or "ne valide pas" in text


# ── Documentation — commandes CLI ────────────────────────────────────────────


def test_doc_mentionne_schema_doctor():
    assert "schema:doctor" in _doc()


def test_doc_mentionne_entity_validate():
    assert "entity:validate" in _doc()


def test_doc_mentionne_rbac_validate():
    assert "rbac:validate" in _doc()


def test_doc_dit_vscode_ne_remplace_pas_cli():
    text = _doc()
    assert "ne remplace pas" in text


# ── Documentation — section dépannage ────────────────────────────────────────


def test_doc_contient_section_depannage():
    text = _doc()
    assert "Dépannage" in text or "dépannage" in text.lower()


def test_doc_depannage_mentionne_schema_doctor():
    text = _doc()
    depannage_pos = text.lower().find("dépannage")
    assert depannage_pos != -1
    assert "schema:doctor" in text[depannage_pos:]


def test_doc_depannage_mentionne_rechargement_vscode():
    text = _doc()
    depannage_pos = text.lower().find("dépannage")
    assert depannage_pos != -1
    section = text[depannage_pos:]
    assert "Reload" in section or "reload" in section.lower() or "relancer" in section.lower()
