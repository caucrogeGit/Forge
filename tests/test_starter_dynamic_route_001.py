"""Garde-fou STARTER-DYNAMIC-ROUTE-001 (test proportionné, ~12 cas).

Contrat public minimum du starter palier 4 — Route dynamique :

- starter.json déclare `dynamic-route` (id, slot 10, requires_db false) ;
- routes.py.snippet déclare `/dynamic-route/articles/{id}` ;
- contrôleur présent + imports Request / Response / BaseController ;
- contrôleur utilise `request.route_param("id", default="inconnu")` ;
- contrôleur retourne `Response.text(f"Article {article_id}")` ;
- aucune vue HTML, aucun fichier SQL, migration, entité ;
- documentation présente, sans aucun des patterns interdits
  (`Starter 10`, `starter:build 10`, `starter:build dynamic-route`,
  `forge new mon-projet`, `cd mon-projet`,
  `source .venv/bin/activate`) ;
- la progression officielle marque le palier 4 livré.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = PROJECT_ROOT / "forge_cli" / "starters" / "data" / "dynamic-route"
FILES_DIR = STARTER_DIR / "files"
CONTROLLER = FILES_DIR / "mvc" / "controllers" / "dynamic_route_controller.py"
DOC = PROJECT_ROOT / "docs" / "starters" / "welcome" / "dynamic-route.md"
STARTERS_INDEX = PROJECT_ROOT / "docs" / "starters" / "index.md"


# ── Contrat starter ───────────────────────────────────────────────────────────


def test_starter_resolves_with_id_and_slot():
    meta = resolve("dynamic-route")
    assert meta["id"] == "dynamic-route"
    assert meta["number"] == 10
    assert meta.get("kind") == "skeleton"
    assert meta.get("requires_db") is False
    assert meta.get("status") == "available"


def test_route_declares_dynamic_articles_id():
    snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    parsed = routes_from_snippet(snippet)
    paths = {path for _method, path in parsed}
    assert paths == {"/dynamic-route/articles/{id}"}, (
        f"Le snippet doit déclarer exactement /dynamic-route/articles/{{id}}, trouvé : {paths}"
    )
    assert "# forge-starter:dynamic-route:start" in snippet
    assert "{id}" in snippet, (
        "Le segment dynamique `{id}` doit apparaître littéralement dans le snippet."
    )


def test_controller_imports_request_response_base_controller():
    content = CONTROLLER.read_text(encoding="utf-8")
    assert "from core.http.request import Request" in content
    assert "from core.http.response import Response" in content
    assert "from core.mvc.controller.base_controller import BaseController" in content


def test_controller_uses_route_param():
    content = CONTROLLER.read_text(encoding="utf-8")
    assert 'request.route_param("id"' in content, (
        "Le contrôleur doit appeler `request.route_param(\"id\", ...)`."
    )
    # default explicit (cf. spec ticket)
    assert 'default="inconnu"' in content


def test_controller_returns_response_text_article():
    content = CONTROLLER.read_text(encoding="utf-8")
    assert 'Response.text(f"Article {article_id}")' in content, (
        "Le contrôleur doit retourner `Response.text(f\"Article {article_id}\")`."
    )


def test_no_view_no_sql_no_entity():
    # Aucune vue HTML
    html_files = list(FILES_DIR.rglob("*.html"))
    assert not html_files, (
        f"Le starter dynamic-route ne doit livrer aucun .html, trouvé : {html_files}"
    )
    # Aucun .sql
    sql_files = list(FILES_DIR.rglob("*.sql"))
    assert not sql_files, (
        f"Le starter dynamic-route ne doit livrer aucun .sql, trouvé : {sql_files}"
    )
    # Aucun dossier models/migrations/schema/entities
    for candidate in ("models", "migrations", "schema", "entities"):
        assert not (FILES_DIR / "mvc" / candidate).exists(), (
            f"`mvc/{candidate}/` ne doit pas être livré par ce starter."
        )


def test_no_response_debug():
    # Response.debug est repoussé au palier 5
    content = CONTROLLER.read_text(encoding="utf-8")
    assert "Response.debug" not in content, (
        "Response.debug est repoussé au palier 5 (STARTER-REQUEST-DEBUG-001)."
    )


# ── Documentation ─────────────────────────────────────────────────────────────


def test_doc_exists():
    assert DOC.exists(), f"Doc starter introuvable : {DOC}"


@pytest.mark.parametrize("forbidden", [
    "Starter 10",
    "forge starter:build 10",
    "forge starter:build dynamic-route",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
])
def test_doc_does_not_contain_forbidden_pattern(forbidden: str):
    content = DOC.read_text(encoding="utf-8")
    assert forbidden not in content, (
        f"La doc du starter ne doit pas contenir '{forbidden}'. "
        "L'utilisateur est supposé déjà dans un projet créé avec ce "
        "starter ; seul `forge run` est autorisé pour lancer le serveur."
    )


def test_doc_mentions_palier_4_and_route_param():
    content = DOC.read_text(encoding="utf-8")
    assert "palier 4" in content.lower() or "Palier 4" in content
    assert 'request.route_param("id")' in content
    assert "/dynamic-route/articles/{id}" in content
    assert "Article 42" in content


# ── Progression officielle : palier 4 livré ───────────────────────────────────


def test_progression_marks_palier_4_as_delivered():
    text = STARTERS_INDEX.read_text(encoding="utf-8")
    assert "STARTER-DYNAMIC-ROUTE-001" in text
    idx_palier4 = text.find("4. **Route dynamique**")
    idx_palier5 = text.find("5. **Inspecter une requête**")
    assert idx_palier4 != -1, "Item « 4. **Route dynamique** » introuvable."
    assert idx_palier5 != -1, "Item « 5. **Inspecter une requête** » introuvable."
    palier4_block = text[idx_palier4:idx_palier5]
    assert "livré" in palier4_block, (
        "Le palier 4 (Route dynamique) doit être marqué « livré » "
        "dans docs/starters/index.md après STARTER-DYNAMIC-ROUTE-001."
    )
    assert "dynamic-route" in palier4_block
