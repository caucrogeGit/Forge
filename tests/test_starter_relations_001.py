"""Garde-fou STARTER-RELATIONS-001 (test proportionné).

Contrat public minimum du palier 1 du niveau avancé — Relations entre tables :

- starter.json déclare `relations` (id, slot 20, requires_db **true**) ;
- routes.py.snippet déclare `GET /relations` ;
- contrôleur présent + imports Request / Response / BaseController +
  `core.database.db.fetch_all` ;
- contrôleur contient un `JOIN` visible (chaîne de module) et rend une vue ;
- la vue boucle sur les lignes (`{% for %}`) et gère le cas vide ;
- une migration SQL existe au format `YYYYMMDDHHMMSS_*.sql`, avec deux tables
  liées par une `FOREIGN KEY` ;
- aucune écriture applicative (pas d'INSERT/UPDATE/DELETE dans le contrôleur) ;
- documentation présente sous `avance/`, sans pattern interdit ;
- le starter figure dans le catalogue `docs/starters/index.md`.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = PROJECT_ROOT / "forge_cli" / "starters" / "data" / "relations"
FILES_DIR = STARTER_DIR / "files"
CONTROLLER = FILES_DIR / "mvc" / "controllers" / "relations_controller.py"
VIEW = FILES_DIR / "mvc" / "views" / "relations" / "index.html"
MIGRATIONS_DIR = FILES_DIR / "mvc" / "migrations"
DOC = PROJECT_ROOT / "docs" / "starters" / "welcome-forge" / "avance" / "relations.md"
STARTERS_INDEX = PROJECT_ROOT / "docs" / "starters" / "index.md"

MIGRATION_FILENAME_RE = re.compile(r"^(\d{14})_([a-z0-9_]+)\.sql$")

FORBIDDEN = [
    "forge starter:build",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/activate",
    "Starter 20",
]


# ── Contrat starter.json ──────────────────────────────────────────────────────

def test_resolves_with_id_and_slot():
    meta = resolve("relations")
    assert meta["id"] == "relations"
    assert meta["number"] == 20
    assert meta.get("kind") == "skeleton"
    assert meta.get("status") == "available"


def test_requires_db_true():
    assert resolve("relations").get("requires_db") is True


def test_aliases_resolvent():
    for alias in ("relations", "relation", "20"):
        assert resolve(alias)["id"] == "relations"


def test_doc_url_pointe_avance():
    assert "welcome-forge/avance/relations" in resolve("relations")["doc_url"]


# ── routes.py.snippet ─────────────────────────────────────────────────────────

def test_snippet_declare_la_route():
    snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    assert "# forge-starter:relations:start" in snippet
    assert "# forge-starter:relations:end" in snippet
    routes = routes_from_snippet(snippet)
    assert any(m == "GET" and p == "/relations" for m, p, *_ in routes)


# ── Contrôleur ────────────────────────────────────────────────────────────────

def test_controller_imports_et_fetch_all():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from core.http.request import Request" in text
    assert "from core.http.response import Response" in text
    assert "from core.mvc.controller.base_controller import BaseController" in text
    assert "from core.database.db import fetch_all" in text


def test_controller_join_visible_et_render():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "JOIN categories" in text
    assert "fetch_all(" in text
    assert "render(" in text and "relations/index.html" in text


def test_controller_methode_typee():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "def index(request: Request) -> Response" in text
    tree = ast.parse(text)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    ctrl = next((c for c in classes if c.name == "RelationsController"), None)
    assert ctrl is not None
    assert "BaseController" in [ast.unparse(b) for b in ctrl.bases]


def test_controller_pas_d_ecriture():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "INSERT" not in text and "UPDATE" not in text and "DELETE" not in text


# ── Vue ───────────────────────────────────────────────────────────────────────

def test_vue_boucle_et_cas_vide():
    html = VIEW.read_text(encoding="utf-8")
    assert "{% for a in articles %}" in html
    assert "{% if articles %}" in html


# ── Migration ─────────────────────────────────────────────────────────────────

def test_migration_presente_et_format():
    sqls = list(MIGRATIONS_DIR.glob("*.sql"))
    assert sqls, "une migration SQL doit être livrée"
    assert all(MIGRATION_FILENAME_RE.match(p.name) for p in sqls)
    content = "\n".join(p.read_text(encoding="utf-8") for p in sqls)
    assert "FOREIGN KEY" in content
    assert "categories" in content and "articles" in content
    assert "CREATE TABLE IF NOT EXISTS" in content


# ── Documentation ─────────────────────────────────────────────────────────────

def test_doc_existe_et_titre():
    assert DOC.exists()
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Relations entre tables"


def test_doc_sans_pattern_interdit():
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text, f"pattern interdit dans la doc : {bad}"


def test_catalogue_liste_le_starter():
    text = STARTERS_INDEX.read_text(encoding="utf-8")
    assert "relations" in text
    assert "Relations entre tables" in text
