"""Garde-fou ENTITY-CONTRACT-011E.

Vérifie que mvc/entities/media/media.json est en format canonique
schema_version "1.0" et reste compatible avec build:model via le normaliseur.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from cli.entities.model import build_model

PROJECT_ROOT = Path(__file__).parent.parent
MEDIA_JSON = PROJECT_ROOT / "tests" / "fixtures" / "app" / "mvc" / "entities" / "media" / "media.json"


# ── Structure du fichier ──────────────────────────────────────────────────────

def test_media_json_exists():
    assert MEDIA_JSON.exists(), "mvc/entities/media/media.json introuvable"


def test_media_json_is_valid_json():
    data = json.loads(MEDIA_JSON.read_text(encoding="utf-8"))
    assert isinstance(data, dict)


def test_media_json_schema_version_canonical():
    data = json.loads(MEDIA_JSON.read_text(encoding="utf-8"))
    assert data.get("schema_version") == "1.0"


def test_media_json_no_format_version():
    data = json.loads(MEDIA_JSON.read_text(encoding="utf-8"))
    assert "format_version" not in data


def test_media_json_no_sql_type():
    text = MEDIA_JSON.read_text(encoding="utf-8")
    assert "sql_type" not in text


def test_media_json_no_python_type():
    text = MEDIA_JSON.read_text(encoding="utf-8")
    assert "python_type" not in text


def test_media_json_no_id_in_fields():
    data = json.loads(MEDIA_JSON.read_text(encoding="utf-8"))
    field_names = [f["name"] for f in data.get("fields", [])]
    assert "id" not in field_names


def test_media_json_name_is_media():
    data = json.loads(MEDIA_JSON.read_text(encoding="utf-8"))
    assert data.get("name") == "Media"


def test_media_json_has_table():
    data = json.loads(MEDIA_JSON.read_text(encoding="utf-8"))
    assert "table" in data
    assert isinstance(data["table"], str)
    assert data["table"]


def test_media_json_all_fields_have_name_and_type():
    data = json.loads(MEDIA_JSON.read_text(encoding="utf-8"))
    for field in data.get("fields", []):
        assert "name" in field, f"Champ sans 'name' : {field}"
        assert "type" in field, f"Champ '{field.get('name')}' sans 'type'"


# ── entity:validate ───────────────────────────────────────────────────────────

def test_entity_validate_json_does_not_report_media():
    """entity:validate --json ne signale plus d'erreur sur media.json après migration."""
    result = subprocess.run(
        [sys.executable, "forge.py", "entity:validate", "--json"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)
    media_errors = [
        e for e in output.get("errors", [])
        if "media/media.json" in e.get("file", "")
    ]
    assert not media_errors, f"Erreurs inattendues sur media.json : {media_errors}"


# ── build:model ───────────────────────────────────────────────────────────────

def test_build_model_with_canonical_media(tmp_path):
    """build:model fonctionne end-to-end avec media.json canonique via le normaliseur."""
    entities_root = tmp_path / "mvc" / "entities"
    media_dir = entities_root / "media"
    media_dir.mkdir(parents=True)
    (media_dir / "media.json").write_text(
        MEDIA_JSON.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (entities_root / "relations.json").write_text(
        json.dumps({"schema_version": "1.0", "relations": []}), encoding="utf-8"
    )

    result = build_model(entities_root)

    assert entities_root / "media" / "media.sql" in result.written
    assert entities_root / "media" / "media_base.py" in result.written


def test_build_model_canonical_media_sql_no_none(tmp_path):
    """Le SQL généré depuis media.json canonique ne contient pas 'None'."""
    entities_root = tmp_path / "mvc" / "entities"
    media_dir = entities_root / "media"
    media_dir.mkdir(parents=True)
    (media_dir / "media.json").write_text(
        MEDIA_JSON.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (entities_root / "relations.json").write_text(
        json.dumps({"schema_version": "1.0", "relations": []}), encoding="utf-8"
    )

    build_model(entities_root)

    sql = (entities_root / "media" / "media.sql").read_text(encoding="utf-8")
    assert "None" not in sql


def test_build_model_canonical_media_sql_has_primary_key(tmp_path):
    """Le SQL généré contient PRIMARY KEY (Id) avec id auto-injecté."""
    entities_root = tmp_path / "mvc" / "entities"
    media_dir = entities_root / "media"
    media_dir.mkdir(parents=True)
    (media_dir / "media.json").write_text(
        MEDIA_JSON.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (entities_root / "relations.json").write_text(
        json.dumps({"schema_version": "1.0", "relations": []}), encoding="utf-8"
    )

    build_model(entities_root)

    sql = (entities_root / "media" / "media.sql").read_text(encoding="utf-8")
    assert "PRIMARY KEY (Id)" in sql
    assert "Id BIGINT UNSIGNED NOT NULL" in sql


def test_build_model_canonical_media_base_py_has_entity_name(tmp_path):
    """La classe générée dans media_base.py est bien MediaBase."""
    entities_root = tmp_path / "mvc" / "entities"
    media_dir = entities_root / "media"
    media_dir.mkdir(parents=True)
    (media_dir / "media.json").write_text(
        MEDIA_JSON.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (entities_root / "relations.json").write_text(
        json.dumps({"schema_version": "1.0", "relations": []}), encoding="utf-8"
    )

    build_model(entities_root)

    base_py = (entities_root / "media" / "media_base.py").read_text(encoding="utf-8")
    assert "class MediaBase" in base_py
    assert "entity_name" in base_py
    assert "self.id" in base_py
