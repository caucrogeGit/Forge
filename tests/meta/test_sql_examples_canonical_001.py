"""Tests SQL-EXAMPLES-CANONICAL-001 : modèles applicatifs livrés utilisent l'API canonique."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

MODELS_DIR = Path("mvc/models")
STARTERS_MODELS_DIRS = list(
    Path("cli/starters/data").glob("*/files/mvc/models")
)

FORBIDDEN_PATTERNS = [
    r"\bget_connection\s*\(",
    r"\bclose_connection\s*\(",
    r"\.fetchone\s*\(",
    r"\.fetchall\s*\(",
]

ALL_MODEL_FILES = [
    f for f in MODELS_DIR.glob("*.py") if f.name != "__init__.py"
] + [
    f
    for d in STARTERS_MODELS_DIRS
    for f in d.glob("*.py")
    if f.name != "__init__.py"
]


class TestModelsUseCanonicalApi:
    """Vérifie que les modèles dans mvc/models/ et les starters n'utilisent que core.database.db.*"""

    @pytest.mark.parametrize("py_file", ALL_MODEL_FILES, ids=lambda f: str(f))
    def test_no_low_level_db_calls(self, py_file):
        content = py_file.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PATTERNS:
            matches = re.findall(pattern, content)
            assert not matches, (
                f"{py_file} utilise un appel DB bas niveau ({pattern}). "
                "Utiliser core.database.db.fetch_one/fetch_all/execute/insert."
            )

    @pytest.mark.parametrize("py_file", ALL_MODEL_FILES, ids=lambda f: str(f))
    def test_imports_from_canonical_api_if_db_used(self, py_file):
        content = py_file.read_text(encoding="utf-8")
        if not any(kw in content for kw in ("SELECT", "INSERT", "UPDATE", "DELETE")):
            return
        assert (
            "from core.database.db import" in content
            or "from core.database import db" in content
        ), f"{py_file} contient du SQL mais n'importe pas core.database.db"


class TestCrudGeneratorEmitsCanonical:
    """Vérifie que le générateur CRUD produit du code utilisant l'API canonique."""

    def test_generated_model_import_line(self):
        from cli.entities.crud.model_builder import build_model

        definition = {
            "entity": "Article",
            "table": "article",
            "fields": [
                {"name": "id", "column": "Id", "type": "int", "primary_key": True, "auto_increment": True},
                {"name": "titre", "column": "Titre", "type": "str"},
            ],
        }
        code = build_model(definition)
        assert "from core.database.db import" in code
        assert "get_connection" not in code
        assert "close_connection" not in code

    def test_generated_model_no_cursor_execute(self):
        from cli.entities.crud.model_builder import build_model

        definition = {
            "entity": "Tag",
            "table": "tag",
            "fields": [
                {"name": "id", "column": "Id", "type": "int", "primary_key": True, "auto_increment": True},
                {"name": "nom", "column": "Nom", "type": "str"},
            ],
        }
        code = build_model(definition)
        assert "cursor.execute" not in code
        assert ".fetchone(" not in code
        assert ".fetchall(" not in code

    def test_generated_get_uses_fetch_all(self):
        from cli.entities.crud.model_builder import build_model

        definition = {
            "entity": "Produit",
            "table": "produit",
            "fields": [
                {"name": "id", "column": "Id", "type": "int", "primary_key": True, "auto_increment": True},
                {"name": "nom", "column": "Nom", "type": "str"},
            ],
        }
        code = build_model(definition)
        assert "fetch_all(SELECT_ALL)" in code
        assert "fetch_one(SELECT_BY_ID" in code

    def test_generated_add_auto_inc_uses_insert(self):
        from cli.entities.crud.model_builder import build_model

        definition = {
            "entity": "Produit",
            "table": "produit",
            "fields": [
                {"name": "id", "column": "Id", "type": "int", "primary_key": True, "auto_increment": True},
                {"name": "nom", "column": "Nom", "type": "str"},
            ],
        }
        code = build_model(definition)
        assert "return insert(INSERT," in code

    def test_generated_delete_uses_execute(self):
        from cli.entities.crud.model_builder import build_model

        definition = {
            "entity": "Produit",
            "table": "produit",
            "fields": [
                {"name": "id", "column": "Id", "type": "int", "primary_key": True, "auto_increment": True},
                {"name": "nom", "column": "Nom", "type": "str"},
            ],
        }
        code = build_model(definition)
        assert "execute(DELETE," in code

    def test_generated_bulk_delete_uses_execute(self):
        from cli.entities.crud.model_builder import build_model

        definition = {
            "entity": "Produit",
            "table": "produit",
            "fields": [
                {"name": "id", "column": "Id", "type": "int", "primary_key": True, "auto_increment": True},
                {"name": "nom", "column": "Nom", "type": "str"},
            ],
        }
        code = build_model(definition)
        assert 'execute("DELETE FROM produit WHERE Id IN (' in code
