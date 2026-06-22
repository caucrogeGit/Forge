"""Garde-fou ENTITY-CONTRACT-011F.

Vérifie que mvc/entities/relations.json est en format canonique
schema_version "1.0" et que entity:validate retourne 0 erreur.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RELATIONS_JSON = PROJECT_ROOT / "mvc" / "entities" / "relations.json"


# ── Structure du fichier ──────────────────────────────────────────────────────

def test_relations_json_exists():
    assert RELATIONS_JSON.exists(), "mvc/entities/relations.json introuvable"


def test_relations_json_is_valid_json():
    data = json.loads(RELATIONS_JSON.read_text(encoding="utf-8"))
    assert isinstance(data, dict)


def test_relations_json_schema_version_canonical():
    data = json.loads(RELATIONS_JSON.read_text(encoding="utf-8"))
    assert data.get("schema_version") == "1.0"


def test_relations_json_no_format_version():
    data = json.loads(RELATIONS_JSON.read_text(encoding="utf-8"))
    assert "format_version" not in data


def test_relations_json_no_from_entity():
    text = RELATIONS_JSON.read_text(encoding="utf-8")
    assert "from_entity" not in text


def test_relations_json_no_to_entity():
    text = RELATIONS_JSON.read_text(encoding="utf-8")
    assert "to_entity" not in text


def test_relations_json_no_foreign_key_name():
    text = RELATIONS_JSON.read_text(encoding="utf-8")
    assert "foreign_key_name" not in text


def test_relations_json_no_source_key():
    text = RELATIONS_JSON.read_text(encoding="utf-8")
    assert "source_key" not in text


def test_relations_json_no_target_key():
    text = RELATIONS_JSON.read_text(encoding="utf-8")
    assert "target_key" not in text


def test_relations_json_has_relations_list():
    data = json.loads(RELATIONS_JSON.read_text(encoding="utf-8"))
    assert "relations" in data
    assert isinstance(data["relations"], list)


# ── entity:validate ───────────────────────────────────────────────────────────

def test_entity_validate_json_valid_true():
    """entity:validate --json retourne valid: true après migration complète."""
    result = subprocess.run(
        [sys.executable, "forge.py", "entity:validate", "--json"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)
    assert output.get("valid") is True, f"entity:validate --json non valide : {output}"


def test_entity_validate_json_errors_count_zero():
    """entity:validate --json retourne errors_count: 0 après migration complète."""
    result = subprocess.run(
        [sys.executable, "forge.py", "entity:validate", "--json"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)
    assert output.get("errors_count") == 0, f"Erreurs inattendues : {output.get('errors')}"


def test_entity_validate_json_no_relations_errors():
    """entity:validate --json ne signale aucune erreur sur relations.json."""
    result = subprocess.run(
        [sys.executable, "forge.py", "entity:validate", "--json"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)
    relations_errors = [
        e for e in output.get("errors", [])
        if "relations.json" in e.get("file", "")
    ]
    assert not relations_errors, f"Erreurs sur relations.json : {relations_errors}"


# ── build:model ───────────────────────────────────────────────────────────────

def test_build_model_still_works_with_canonical_relations(tmp_path):
    """build:model fonctionne avec relations.json canonique (liste vide)."""
    import shutil
    from cli.entities.model import build_model

    entities_root = tmp_path / "mvc" / "entities"
    shutil.copytree(PROJECT_ROOT / "mvc" / "entities", entities_root)

    result = build_model(entities_root)

    assert entities_root / "relations.sql" in result.written
