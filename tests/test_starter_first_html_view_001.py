"""Garde-fou STARTER-FIRST-HTML-VIEW-001 (test proportionné, ~12 cas).

Contrat public minimum du starter palier 3 — Première vue HTML :

- starter.json déclare `first-html-view` (id, slot 9, requires_db false) ;
- routes.py.snippet déclare `/first-html-view` ;
- contrôleur présent + imports Request / Response / BaseController ;
- contrôleur appelle `BaseController.render("first_html_view/index.html", request=request)` ;
- vue HTML présente et minimale ;
- aucun fichier SQL, migration, entité ;
- documentation présente, sans aucun des patterns interdits
  (`Starter 9`, `starter:build 9`, `starter:build first-html-view`,
  `forge new mon-projet`, `cd mon-projet`, `source .venv/bin/activate`) ;
- la progression officielle marque le palier 3 livré.

Ne couvre PAS : moteur de templates, routeur, génération Forge,
suite méta complète, dry-run CLI — déjà couverts ailleurs.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = PROJECT_ROOT / "forge_cli" / "starters" / "data" / "first-html-view"
FILES_DIR = STARTER_DIR / "files"
CONTROLLER = FILES_DIR / "mvc" / "controllers" / "first_html_view_controller.py"
VIEW = FILES_DIR / "mvc" / "views" / "first_html_view" / "index.html"
DOC = PROJECT_ROOT / "docs" / "starters" / "first-html-view" / "index.md"
STARTERS_INDEX = PROJECT_ROOT / "docs" / "starters" / "index.md"


# ── Contrat starter (metadata + routes + contrôleur + vue + scope) ────────────


def test_starter_resolves_with_id_and_slot():
    meta = resolve("first-html-view")
    assert meta["id"] == "first-html-view"
    assert meta["number"] == 9
    assert meta.get("kind") == "skeleton"
    assert meta.get("requires_db") is False
    assert meta.get("status") == "available"


def test_route_declares_first_html_view():
    snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    parsed = routes_from_snippet(snippet)
    paths = {path for _method, path in parsed}
    assert paths == {"/first-html-view"}, (
        f"Le snippet doit déclarer exactement /first-html-view, trouvé : {paths}"
    )
    assert "# forge-starter:first-html-view:start" in snippet


def test_controller_imports_request_response_base_controller():
    content = CONTROLLER.read_text(encoding="utf-8")
    assert "from core.http.request import Request" in content
    assert "from core.http.response import Response" in content
    assert "from core.mvc.controller.base_controller import BaseController" in content


def test_controller_uses_base_controller_render():
    content = CONTROLLER.read_text(encoding="utf-8")
    expected = 'BaseController.render("first_html_view/index.html", request=request)'
    assert expected in content, (
        f"Le contrôleur doit appeler exactement `{expected}`."
    )


def test_view_present_and_minimal_html():
    assert VIEW.exists(), f"Vue introuvable : {VIEW}"
    html = VIEW.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html
    assert "<h1>Première vue HTML</h1>" in html
    # Pas de Tailwind, pas de layout, pas d'include, pas de SVG inline
    forbidden_in_view = ["tailwind", "{% extends", "{% include", "<svg"]
    for noise in forbidden_in_view:
        assert noise not in html, (
            f"`{noise}` ne doit pas apparaître dans la vue minimale."
        )


def test_no_sql_migration_entity_files():
    # Le starter livre uniquement le contrôleur + la vue
    forbidden_globs = ["*.sql", "models", "migrations", "schema", "entities"]
    for pat in forbidden_globs:
        if "*" in pat:
            assert not list(FILES_DIR.rglob(pat)), (
                f"Aucun fichier '{pat}' attendu dans le starter."
            )
        else:
            assert not (FILES_DIR / "mvc" / pat).exists(), (
                f"`mvc/{pat}/` ne doit pas être livré par ce starter."
            )


# ── Documentation du starter (présence + interdits stricts) ───────────────────


def test_doc_exists():
    assert DOC.exists(), f"Doc starter introuvable : {DOC}"


@pytest.mark.parametrize("forbidden", [
    "Starter 9",
    "forge starter:build 9",
    "forge starter:build first-html-view",
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


def test_doc_mentions_palier_3_and_render():
    content = DOC.read_text(encoding="utf-8")
    assert "palier 3" in content.lower() or "Palier 3" in content
    assert "BaseController.render(" in content
    assert "/first-html-view" in content


# ── Progression officielle : palier 3 livré ───────────────────────────────────


def test_progression_marks_palier_3_as_delivered():
    # On ancre sur l'item numéroté de la progression (« 3. **Première
    # vue HTML** ») pour ne pas matcher la ligne du tableau de
    # synthèse qui répète le même nom (le `find()` retournerait la
    # première occurrence — celle du tableau — au lieu de l'item
    # progression).
    text = STARTERS_INDEX.read_text(encoding="utf-8")
    assert "STARTER-FIRST-HTML-VIEW-001" in text
    idx_palier3 = text.find("3. **Première vue HTML**")
    idx_palier4 = text.find("4. **Route dynamique**")
    assert idx_palier3 != -1, "Item « 3. **Première vue HTML** » introuvable."
    assert idx_palier4 != -1, "Item « 4. **Route dynamique** » introuvable."
    palier3_block = text[idx_palier3:idx_palier4]
    assert "livré" in palier3_block, (
        "Le palier 3 (Première vue HTML) doit être marqué « livré » "
        "dans docs/starters/index.md après STARTER-FIRST-HTML-VIEW-001."
    )
    assert "first-html-view" in palier3_block
