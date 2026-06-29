"""Garde-fou ENTITY-CONTRACT-006.

Vérifie que schemas/forge.schema.index.json :
- existe et est un JSON valide ;
- contient schema_version = "1.0" ;
- contient schemas avec exactement 4 entrées connues ;
- chaque chemin commence par "./" ;
- chaque chemin pointe vers un fichier existant dans schemas/ ;
- chaque clé pointe vers le bon fichier attendu ;
- aucune URL distante n'est utilisée ;
- aucun schéma non encore créé n'est référencé.

Ce test ne fait aucune validation réseau et n'utilise pas de bibliothèque
de validation JSON Schema externe.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent
INDEX_PATH = PROJECT_ROOT / "schemas" / "forge.schema.index.json"
SCHEMAS_DIR = PROJECT_ROOT / "schemas"

_EXPECTED_SCHEMAS = {
    "common": "./common.schema.json",
    "field": "./field.schema.json",
    "entity": "./entity.schema.json",
    "relations": "./relations.schema.json",
}

_FORBIDDEN_URL_PREFIXES = ("http://", "https://", "ftp://")


@pytest.fixture(scope="module")
def index() -> dict:
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


class TestFilePresence:
    def test_index_file_exists(self):
        assert INDEX_PATH.exists(), "schemas/forge.schema.index.json doit exister."

    def test_index_file_is_valid_json(self):
        json.loads(INDEX_PATH.read_text(encoding="utf-8"))


class TestSchemaVersion:
    def test_schema_version_exists(self, index):
        assert "schema_version" in index, "schema_version doit exister dans le registre."

    def test_schema_version_is_1_0(self, index):
        assert index["schema_version"] == "1.0", (
            "schema_version doit valoir '1.0'."
        )


class TestSchemasKey:
    def test_schemas_key_exists(self, index):
        assert "schemas" in index, "La clé 'schemas' doit exister dans le registre."

    def test_schemas_is_object(self, index):
        assert isinstance(index["schemas"], dict), (
            "'schemas' doit être un objet JSON."
        )

    def test_schemas_has_exactly_expected_keys(self, index):
        keys = set(index["schemas"].keys())
        expected = set(_EXPECTED_SCHEMAS.keys())
        assert keys == expected, (
            f"Clés inattendues ou manquantes dans 'schemas' : "
            f"inattendues={keys - expected}, manquantes={expected - keys}."
        )


class TestEachSchemaEntry:
    @pytest.mark.parametrize("key,expected_path", sorted(_EXPECTED_SCHEMAS.items()))
    def test_exact_path_value(self, index, key, expected_path):
        actual = index["schemas"].get(key, "")
        assert actual == expected_path, (
            f"schemas.{key} doit valoir '{expected_path}' — trouvé : '{actual}'."
        )

    @pytest.mark.parametrize("key", sorted(_EXPECTED_SCHEMAS.keys()))
    def test_path_starts_with_dot_slash(self, index, key):
        path = index["schemas"][key]
        assert path.startswith("./"), (
            f"schemas.{key} doit commencer par './' — trouvé : '{path}'."
        )

    @pytest.mark.parametrize("key", sorted(_EXPECTED_SCHEMAS.keys()))
    def test_referenced_file_exists(self, index, key):
        relative = index["schemas"][key]
        resolved = SCHEMAS_DIR / relative.lstrip("./")
        assert resolved.exists(), (
            f"schemas.{key} référence '{relative}' mais le fichier est introuvable."
        )

    @pytest.mark.parametrize("key", sorted(_EXPECTED_SCHEMAS.keys()))
    def test_no_remote_url(self, index, key):
        path = index["schemas"][key]
        for prefix in _FORBIDDEN_URL_PREFIXES:
            assert not path.startswith(prefix), (
                f"schemas.{key} ne doit pas utiliser d'URL distante — trouvé : '{path}'."
            )
