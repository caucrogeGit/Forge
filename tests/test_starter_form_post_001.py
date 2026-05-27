"""Garde-fou STARTER-FORM-POST-001 (test proportionné, ~15 cas).

Contrat public minimum du starter palier 6 — Premier formulaire POST :

- starter.json déclare `form-post` (id, slot 12, requires_db false) ;
- routes.py.snippet déclare `GET /form-post` ET `POST /form-post` ;
- contrôleur présent + imports Request / Response / BaseController ;
- index() utilise `BaseController.render("form_post/index.html", ...)`
  et passe `csrf_token` (via `BaseController.csrf_token(request)`) ;
- submit() lit `request.form("name", default="Forge")` et retourne
  `Response.text(f"Bonjour {name}")` ;
- vue HTML présente, contient `form method="post" action="/form-post"`
  et `input name="name"` et le champ caché `csrf_token` ;
- aucun fichier SQL, migration, entité ;
- documentation présente, sans aucun des patterns interdits ;
- la progression officielle marque le palier 6 livré.

Ne couvre PAS : moteur CSRF, moteur de templates, routeur, suite méta
complète — déjà couverts ailleurs.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = PROJECT_ROOT / "forge_cli" / "starters" / "data" / "form-post"
FILES_DIR = STARTER_DIR / "files"
CONTROLLER = FILES_DIR / "mvc" / "controllers" / "form_post_controller.py"
VIEW = FILES_DIR / "mvc" / "views" / "form_post" / "index.html"
DOC = PROJECT_ROOT / "docs" / "starters" / "form-post" / "index.md"
STARTERS_INDEX = PROJECT_ROOT / "docs" / "starters" / "index.md"


# ── Contrat starter ───────────────────────────────────────────────────────────


def test_starter_resolves_with_id_and_slot():
    meta = resolve("form-post")
    assert meta["id"] == "form-post"
    assert meta["number"] == 12
    assert meta.get("kind") == "skeleton"
    assert meta.get("requires_db") is False
    assert meta.get("status") == "available"


def test_routes_declare_get_and_post_form_post():
    snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    parsed = routes_from_snippet(snippet)
    assert ("GET", "/form-post") in parsed, (
        f"GET /form-post manquant dans le snippet, trouvé : {parsed}"
    )
    assert ("POST", "/form-post") in parsed, (
        f"POST /form-post manquant dans le snippet, trouvé : {parsed}"
    )
    assert "# forge-starter:form-post:start" in snippet


def test_controller_imports_request_response_base_controller():
    content = CONTROLLER.read_text(encoding="utf-8")
    assert "from core.http.request import Request" in content
    assert "from core.http.response import Response" in content
    assert "from core.mvc.controller.base_controller import BaseController" in content


def test_index_renders_form_post_template():
    content = CONTROLLER.read_text(encoding="utf-8")
    assert 'BaseController.render(' in content
    assert '"form_post/index.html"' in content


def test_index_passes_csrf_token_to_template():
    content = CONTROLLER.read_text(encoding="utf-8")
    assert "BaseController.csrf_token(request)" in content, (
        "L'action `index` doit générer le token CSRF via "
        "`BaseController.csrf_token(request)` et le passer au contexte."
    )
    assert '"csrf_token"' in content


def test_submit_reads_form_name():
    content = CONTROLLER.read_text(encoding="utf-8")
    assert 'request.form("name"' in content, (
        "L'action `submit` doit lire le champ `name` via "
        "`request.form(\"name\", ...)`."
    )
    assert 'default="Forge"' in content


def test_submit_returns_response_text_bonjour():
    content = CONTROLLER.read_text(encoding="utf-8")
    assert 'Response.text(f"Bonjour {name}")' in content, (
        "L'action `submit` doit retourner "
        "`Response.text(f\"Bonjour {name}\")`."
    )


def test_view_form_post_minimal():
    assert VIEW.exists(), f"Vue introuvable : {VIEW}"
    html = VIEW.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html
    assert 'method="post"' in html
    assert 'action="/form-post"' in html
    assert 'name="name"' in html
    # Champ CSRF caché obligatoire (Forge active CSRF par défaut)
    assert 'name="csrf_token"' in html
    assert '{{ csrf_token }}' in html


def test_view_no_tailwind_no_layout_no_js():
    html = VIEW.read_text(encoding="utf-8")
    forbidden = ["tailwind", "{% extends", "{% include", "<script"]
    for noise in forbidden:
        assert noise not in html, (
            f"`{noise}` ne doit pas apparaître dans la vue minimale."
        )


def test_no_sql_no_entity_no_migration():
    sql_files = list(FILES_DIR.rglob("*.sql"))
    assert not sql_files, (
        f"Le starter form-post ne doit livrer aucun .sql, trouvé : {sql_files}"
    )
    for candidate in ("models", "migrations", "schema", "entities"):
        assert not (FILES_DIR / "mvc" / candidate).exists(), (
            f"`mvc/{candidate}/` ne doit pas être livré par ce starter."
        )


# ── Documentation ─────────────────────────────────────────────────────────────


def test_doc_exists():
    assert DOC.exists(), f"Doc starter introuvable : {DOC}"


@pytest.mark.parametrize("forbidden", [
    "Starter 12",
    "forge starter:build 12",
    "forge starter:build form-post",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
])
def test_doc_does_not_contain_forbidden_pattern(forbidden: str):
    content = DOC.read_text(encoding="utf-8")
    assert forbidden not in content, (
        f"La doc du starter ne doit pas contenir '{forbidden}'."
    )


def test_doc_mentions_palier_6_and_form_concepts():
    content = DOC.read_text(encoding="utf-8")
    assert "palier 6" in content.lower() or "Palier 6" in content
    assert 'request.form(' in content
    assert "csrf_token" in content
    assert "/form-post" in content


# ── Progression officielle : palier 6 livré ───────────────────────────────────


def test_progression_marks_palier_6_as_delivered():
    text = STARTERS_INDEX.read_text(encoding="utf-8")
    assert "STARTER-FORM-POST-001" in text
    idx_palier6 = text.find("6. **Premier formulaire POST**")
    idx_palier7 = text.find("7. **Validation serveur**")
    assert idx_palier6 != -1, "Item « 6. **Premier formulaire POST** » introuvable."
    assert idx_palier7 != -1, "Item « 7. **Validation serveur** » introuvable."
    palier6_block = text[idx_palier6:idx_palier7]
    assert "livré" in palier6_block, (
        "Le palier 6 (Premier formulaire POST) doit être marqué « livré » "
        "dans docs/starters/index.md après STARTER-FORM-POST-001."
    )
    assert "form-post" in palier6_block
