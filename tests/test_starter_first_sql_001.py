"""Garde-fou STARTER-FIRST-SQL-001 (test proportionné, ~16 cas).

Contrat public minimum du starter palier 8 — Première base SQL :

- starter.json déclare `first-sql` (id, slot 14, requires_db **true**) ;
- routes.py.snippet déclare `GET /first-sql` ;
- contrôleur présent + imports Request / Response / BaseController +
  `core.database.db.fetch_one` ;
- contrôleur contient un SELECT visible (chaîne de module) sur la
  table `first_sql_messages` ;
- contrôleur retourne `Response.text(f"Message depuis la base : {message}")` ;
- une migration SQL existe au format `YYYYMMDDHHMMSS_*.sql` ;
- la migration crée la table `first_sql_messages` ;
- la migration insère/permet la donnée `Bonjour SQL` ;
- aucun fichier d'entité JSON, aucun CRUD généré (pas de
  `*_form.py`, `*_model.py`) ;
- documentation présente, sans aucun des patterns interdits ;
- la progression officielle marque le palier 8 livré.

Ne couvre PAS : connexion MariaDB réelle, moteur de migration, ORM,
suite méta complète.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = PROJECT_ROOT / "forge_cli" / "starters" / "data" / "first-sql"
FILES_DIR = STARTER_DIR / "files"
CONTROLLER = FILES_DIR / "mvc" / "controllers" / "first_sql_controller.py"
MIGRATIONS_DIR = FILES_DIR / "mvc" / "migrations"
DOC = PROJECT_ROOT / "docs" / "starters" / "progression" / "first-sql.md"
STARTERS_INDEX = PROJECT_ROOT / "docs" / "starters" / "index.md"

MIGRATION_FILENAME_RE = re.compile(r"^(\d{14})_([a-z0-9_]+)\.sql$")


# ── Contrat starter ───────────────────────────────────────────────────────────


def test_starter_resolves_with_id_and_slot():
    meta = resolve("first-sql")
    assert meta["id"] == "first-sql"
    assert meta["number"] == 14
    assert meta.get("kind") == "skeleton"
    assert meta.get("status") == "available"


def test_starter_requires_db_is_true():
    # Premier starter pédagogique avec MariaDB de la progression
    meta = resolve("first-sql")
    assert meta.get("requires_db") is True, (
        "Le starter first-sql doit avoir requires_db: true."
    )


def test_route_declares_get_first_sql():
    snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    parsed = routes_from_snippet(snippet)
    paths = {(method, path) for method, path in parsed}
    assert ("GET", "/first-sql") in paths
    assert "# forge-starter:first-sql:start" in snippet


def test_controller_imports_db_request_response_base_controller():
    content = CONTROLLER.read_text(encoding="utf-8")
    assert "from core.database.db import fetch_one" in content, (
        "Le contrôleur doit utiliser l'API officielle "
        "`core.database.db.fetch_one`."
    )
    assert "from core.http.request import Request" in content
    assert "from core.http.response import Response" in content
    assert "from core.mvc.controller.base_controller import BaseController" in content


def test_controller_contains_visible_select():
    content = CONTROLLER.read_text(encoding="utf-8")
    # SELECT visible en chaîne lisible (pas masqué dans une méthode)
    assert "SELECT" in content
    assert "first_sql_messages" in content, (
        "Le contrôleur doit interroger la table `first_sql_messages`."
    )


def test_controller_returns_response_text_message():
    content = CONTROLLER.read_text(encoding="utf-8")
    assert 'Response.text(f"Message depuis la base : {message}")' in content, (
        "Le contrôleur doit retourner "
        "`Response.text(f\"Message depuis la base : {message}\")`."
    )


def test_controller_calls_fetch_one():
    content = CONTROLLER.read_text(encoding="utf-8")
    assert "fetch_one(" in content


# ── Migration SQL ─────────────────────────────────────────────────────────────


def test_migration_exists():
    assert MIGRATIONS_DIR.exists(), (
        f"Dossier migrations introuvable : {MIGRATIONS_DIR}"
    )
    sql_files = list(MIGRATIONS_DIR.glob("*.sql"))
    assert len(sql_files) >= 1, (
        "Au moins une migration SQL doit être livrée par le starter."
    )


def test_migration_filename_format():
    # Format attendu par le collecteur : YYYYMMDDHHMMSS_nom.sql
    sql_files = list(MIGRATIONS_DIR.glob("*.sql"))
    for path in sql_files:
        m = MIGRATION_FILENAME_RE.fullmatch(path.name)
        assert m is not None, (
            f"Nom de migration invalide : {path.name}. "
            "Format attendu : YYYYMMDDHHMMSS_nom.sql."
        )


def test_migration_creates_first_sql_messages_table():
    sql_files = list(MIGRATIONS_DIR.glob("*.sql"))
    assert sql_files
    combined = "\n".join(p.read_text(encoding="utf-8") for p in sql_files)
    assert "CREATE TABLE" in combined
    assert "first_sql_messages" in combined, (
        "La migration doit créer la table `first_sql_messages`."
    )


def test_migration_inserts_bonjour_sql():
    sql_files = list(MIGRATIONS_DIR.glob("*.sql"))
    combined = "\n".join(p.read_text(encoding="utf-8") for p in sql_files)
    assert "Bonjour SQL" in combined, (
        "La migration doit insérer la donnée de démo 'Bonjour SQL'."
    )
    assert "INSERT" in combined


def test_migration_only_one_demo_table():
    sql_files = list(MIGRATIONS_DIR.glob("*.sql"))
    combined = "\n".join(p.read_text(encoding="utf-8") for p in sql_files)
    # Une seule table de démo ; on tolère les tables système (none ici).
    create_count = combined.upper().count("CREATE TABLE")
    assert create_count == 1, (
        f"Le starter ne doit créer qu'une seule table — trouvé "
        f"{create_count} CREATE TABLE."
    )


# ── Aucune entité JSON, aucun CRUD ────────────────────────────────────────────


def test_no_entity_json_in_starter_dir():
    # Les starters CRUD utilisent un *.json à la racine du starter
    # (cf. contact-simple/contact.json). Ici, on ne veut PAS générer
    # de CRUD — uniquement le starter.json (manifeste) doit exister.
    json_files = [p for p in STARTER_DIR.glob("*.json") if p.name != "starter.json"]
    assert not json_files, (
        f"Le starter first-sql ne doit pas livrer de fichier d'entité "
        f"JSON ; trouvé : {[p.name for p in json_files]}."
    )


def test_no_crud_files_shipped():
    for forbidden in ("forms", "models", "entities"):
        path = FILES_DIR / "mvc" / forbidden
        assert not path.exists(), (
            f"`mvc/{forbidden}/` ne doit pas être livré par ce "
            "starter (pas de CRUD généré)."
        )


# ── Documentation ─────────────────────────────────────────────────────────────


def test_doc_exists():
    assert DOC.exists(), f"Doc starter introuvable : {DOC}"


@pytest.mark.parametrize("forbidden", [
    "Starter 14",
    "forge starter:build 14",
    "forge starter:build first-sql",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
])
def test_doc_does_not_contain_forbidden_pattern(forbidden: str):
    content = DOC.read_text(encoding="utf-8")
    assert forbidden not in content, (
        f"La doc du starter ne doit pas contenir '{forbidden}'."
    )


def test_doc_mentions_palier_8_and_concepts():
    content = DOC.read_text(encoding="utf-8")
    assert "palier 8" in content.lower() or "Palier 8" in content
    assert "fetch_one" in content
    assert "first_sql_messages" in content
    assert "Bonjour SQL" in content
    assert "forge migration:apply" in content
    assert "/first-sql" in content


# ── Progression officielle : palier 8 livré ───────────────────────────────────


def test_progression_marks_palier_8_as_delivered():
    text = STARTERS_INDEX.read_text(encoding="utf-8")
    assert "STARTER-FIRST-SQL-001" in text
    idx_palier8 = text.find("8. **Première base SQL**")
    idx_palier9 = text.find("9. **Premier CRUD**")
    assert idx_palier8 != -1
    assert idx_palier9 != -1
    palier8_block = text[idx_palier8:idx_palier9]
    assert "livré" in palier8_block
    assert "first-sql" in palier8_block
