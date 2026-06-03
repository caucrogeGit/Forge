"""Garde-fou STARTER-SERVER-VALIDATION-001 (test proportionné, ~16 cas).

Contrat public minimum du starter palier 9 — Validation serveur :

- starter.json déclare `server-validation` (id, slot 10,
  requires_db false) ;
- routes.py.snippet déclare `GET /server-validation` ET
  `POST /server-validation` ;
- contrôleur présent + imports Request / Response / BaseController ;
- index() rend `server_validation/index.html` avec `csrf_token` au
  contexte ;
- submit() lit `request.form("name", default="").strip()` ;
- branche vide retourne `Response.text("Le prénom est obligatoire",
  status=422)` ;
- branche valide retourne `Response.text(f"Bonjour {name}")` ;
- vue HTML présente, contient `form method="post"
  action="/server-validation"`, `input name="name"`, champ caché
  `csrf_token`, pas de Tailwind/JS/réaffichage dynamique ;
- aucun fichier SQL, migration, entité ;
- documentation présente, sans aucun des patterns interdits ;
- la progression officielle marque le palier 9 livré.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = PROJECT_ROOT / "forge_cli" / "starters" / "data" / "server-validation"
FILES_DIR = STARTER_DIR / "files"
CONTROLLER = FILES_DIR / "mvc" / "controllers" / "server_validation_controller.py"
VIEW = FILES_DIR / "mvc" / "views" / "server_validation" / "index.html"
DOC = PROJECT_ROOT / "docs" / "starters" / "welcome-forge" / "server-validation.md"
STARTERS_INDEX = PROJECT_ROOT / "docs" / "starters" / "index.md"


# ── Contrat starter ───────────────────────────────────────────────────────────


def test_starter_resolves_with_id_and_slot():
    meta = resolve("server-validation")
    assert meta["id"] == "server-validation"
    assert meta["number"] == 10
    assert meta.get("kind") == "skeleton"
    assert meta.get("requires_db") is False
    assert meta.get("status") == "available"


def test_routes_declare_get_and_post():
    snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    parsed = routes_from_snippet(snippet)
    assert ("GET", "/server-validation") in parsed
    assert ("POST", "/server-validation") in parsed
    assert "# forge-starter:server-validation:start" in snippet


def test_controller_imports_request_response_base_controller():
    content = CONTROLLER.read_text(encoding="utf-8")
    assert "from core.http.request import Request" in content
    assert "from core.http.response import Response" in content
    assert "from core.mvc.controller.base_controller import BaseController" in content


def test_index_renders_server_validation_template():
    content = CONTROLLER.read_text(encoding="utf-8")
    assert "BaseController.render(" in content
    assert '"server_validation/index.html"' in content


def test_index_passes_csrf_token_to_template():
    content = CONTROLLER.read_text(encoding="utf-8")
    assert "BaseController.csrf_token(request)" in content
    assert '"csrf_token"' in content


def test_submit_reads_form_name_with_strip():
    content = CONTROLLER.read_text(encoding="utf-8")
    assert 'request.form("name"' in content
    assert 'default=""' in content
    assert ".strip()" in content, (
        "Le contrôleur doit appeler `.strip()` pour traiter les "
        "espaces blancs comme une saisie vide."
    )


def test_submit_returns_422_for_empty_name():
    content = CONTROLLER.read_text(encoding="utf-8")
    assert 'Response.text("Le prénom est obligatoire", status=422)' in content, (
        "La branche vide doit retourner exactement "
        "`Response.text(\"Le prénom est obligatoire\", status=422)`."
    )


def test_submit_returns_bonjour_for_valid_name():
    content = CONTROLLER.read_text(encoding="utf-8")
    assert 'Response.text(f"Bonjour {name}")' in content, (
        "La branche valide doit retourner "
        "`Response.text(f\"Bonjour {name}\")`."
    )


def test_view_present_and_minimal():
    assert VIEW.exists(), f"Vue introuvable : {VIEW}"
    html = VIEW.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html
    assert 'method="post"' in html
    assert 'action="/server-validation"' in html
    assert 'name="name"' in html
    assert 'name="csrf_token"' in html
    assert '{{ csrf_token }}' in html


def test_view_no_tailwind_no_js_no_dynamic_error():
    html = VIEW.read_text(encoding="utf-8")
    forbidden = [
        "tailwind",
        "<script",
        "{% extends",
        "{% include",
        "{% if error",  # pas de réaffichage HTML avec messages dynamiques
        "{{ error }}",
    ]
    for noise in forbidden:
        assert noise not in html, (
            f"`{noise}` ne doit pas apparaître dans la vue minimale "
            "(hors périmètre de ce starter)."
        )


def test_no_sql_no_entity_no_migration():
    sql_files = list(FILES_DIR.rglob("*.sql"))
    assert not sql_files
    for candidate in ("models", "migrations", "schema", "entities"):
        assert not (FILES_DIR / "mvc" / candidate).exists(), (
            f"`mvc/{candidate}/` ne doit pas être livré par ce starter."
        )


# ── Documentation ─────────────────────────────────────────────────────────────


def test_doc_exists():
    assert DOC.exists(), f"Doc starter introuvable : {DOC}"


@pytest.mark.parametrize("forbidden", [
    "Starter 13",
    "forge starter:build 13",
    "forge starter:build server-validation",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
])
def test_doc_does_not_contain_forbidden_pattern(forbidden: str):
    content = DOC.read_text(encoding="utf-8")
    assert forbidden not in content, (
        f"La doc du starter ne doit pas contenir '{forbidden}'."
    )


def test_doc_mentions_palier_9_and_concepts():
    content = DOC.read_text(encoding="utf-8")
    assert "palier 9" in content.lower() or "Palier 9" in content
    assert "422" in content
    assert "request.form" in content
    assert "/server-validation" in content
    assert "Le prénom est obligatoire" in content


# ── Progression officielle : palier 9 livré ───────────────────────────────────


def test_progression_marks_palier_9_as_delivered():
    text = STARTERS_INDEX.read_text(encoding="utf-8")
    assert "STARTER-SERVER-VALIDATION-001" in text
    idx_palier9 = text.find("9. **Validation serveur**")
    idx_palier10 = text.find("10. **Première base SQL**")
    assert idx_palier9 != -1
    assert idx_palier10 != -1
    palier9_block = text[idx_palier9:idx_palier10]
    assert "livré" in palier9_block
    assert "server-validation" in palier9_block
