"""Garde-fou STARTER-REQUEST-DEBUG-001 (test proportionné, ~12 cas).

Contrat public minimum du starter palier 5 — Inspecter une requête :

- starter.json déclare `request-debug` (id, slot 11, requires_db false) ;
- routes.py.snippet déclare `/request-debug` ;
- contrôleur présent + imports Request / Response / BaseController ;
- contrôleur utilise `request.data` ;
- contrôleur retourne `Response.debug(request.data)` ;
- aucune vue HTML, aucun fichier SQL, migration, entité ;
- documentation présente, sans aucun des patterns interdits
  (`Starter 11`, `starter:build 11`, `starter:build request-debug`,
  `forge new mon-projet`, `cd mon-projet`,
  `source .venv/bin/activate`) ;
- la progression officielle marque le palier 5 livré.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = PROJECT_ROOT / "forge_cli" / "starters" / "data" / "request-debug"
FILES_DIR = STARTER_DIR / "files"
CONTROLLER = FILES_DIR / "mvc" / "controllers" / "request_debug_controller.py"
DOC = PROJECT_ROOT / "docs" / "starters" / "request-debug" / "index.md"
STARTERS_INDEX = PROJECT_ROOT / "docs" / "starters" / "index.md"


# ── Contrat starter ───────────────────────────────────────────────────────────


def test_starter_resolves_with_id_and_slot():
    meta = resolve("request-debug")
    assert meta["id"] == "request-debug"
    assert meta["number"] == 11
    assert meta.get("kind") == "skeleton"
    assert meta.get("requires_db") is False
    assert meta.get("status") == "available"


def test_route_declares_request_debug():
    snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    parsed = routes_from_snippet(snippet)
    paths = {path for _method, path in parsed}
    assert paths == {"/request-debug"}, (
        f"Le snippet doit déclarer exactement /request-debug, trouvé : {paths}"
    )
    assert "# forge-starter:request-debug:start" in snippet


def test_controller_imports_request_response_base_controller():
    content = CONTROLLER.read_text(encoding="utf-8")
    assert "from core.http.request import Request" in content
    assert "from core.http.response import Response" in content
    assert "from core.mvc.controller.base_controller import BaseController" in content


def test_controller_uses_request_data():
    content = CONTROLLER.read_text(encoding="utf-8")
    assert "request.data" in content, (
        "Le contrôleur doit accéder à `request.data`."
    )


def test_controller_returns_response_debug_request_data():
    content = CONTROLLER.read_text(encoding="utf-8")
    assert "Response.debug(request.data)" in content, (
        "Le contrôleur doit retourner `Response.debug(request.data)` "
        "(appel exact)."
    )


def test_no_view_no_sql_no_entity():
    html_files = list(FILES_DIR.rglob("*.html"))
    assert not html_files, (
        f"Le starter request-debug ne doit livrer aucun .html, trouvé : {html_files}"
    )
    sql_files = list(FILES_DIR.rglob("*.sql"))
    assert not sql_files, (
        f"Le starter request-debug ne doit livrer aucun .sql, trouvé : {sql_files}"
    )
    for candidate in ("models", "migrations", "schema", "entities"):
        assert not (FILES_DIR / "mvc" / candidate).exists(), (
            f"`mvc/{candidate}/` ne doit pas être livré par ce starter."
        )


# ── Documentation ─────────────────────────────────────────────────────────────


def test_doc_exists():
    assert DOC.exists(), f"Doc starter introuvable : {DOC}"


@pytest.mark.parametrize("forbidden", [
    "Starter 11",
    "forge starter:build 11",
    "forge starter:build request-debug",
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


def test_doc_mentions_palier_5_and_concepts():
    content = DOC.read_text(encoding="utf-8")
    assert "palier 5" in content.lower() or "Palier 5" in content
    assert "request.data" in content
    assert "Response.debug" in content
    assert "/request-debug" in content


# ── Progression officielle : palier 5 livré ───────────────────────────────────


def test_progression_marks_palier_5_as_delivered():
    text = STARTERS_INDEX.read_text(encoding="utf-8")
    assert "STARTER-REQUEST-DEBUG-001" in text
    idx_palier5 = text.find("5. **Inspecter une requête**")
    idx_palier6 = text.find("6. **Premier formulaire POST**")
    assert idx_palier5 != -1, "Item « 5. **Inspecter une requête** » introuvable."
    assert idx_palier6 != -1, "Item « 6. **Premier formulaire POST** » introuvable."
    palier5_block = text[idx_palier5:idx_palier6]
    assert "livré" in palier5_block, (
        "Le palier 5 (Inspecter une requête) doit être marqué « livré » "
        "dans docs/starters/index.md après STARTER-REQUEST-DEBUG-001."
    )
    assert "request-debug" in palier5_block
