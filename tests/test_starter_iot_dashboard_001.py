"""Garde-fou STARTER-IOT-DASHBOARD-001 (test proportionné).

Contrat du palier 3 du niveau intermédiaire de welcome-iot — Tableau de bord :

- starter.json : `iot-dashboard`, slot 30, requires_db **true** ;
- snippet : GET `/iot-dashboard` ;
- contrôleur : `IotEventRepository.list_recent` + `render`, lecture seule ;
- vue : tableau HTML des événements + état vide ;
- migration `iot_events` ; documentation sous `intermediaire/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "iot-dashboard"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "iot_dashboard_controller.py"
VIEW = FILES / "mvc" / "views" / "iot_dashboard" / "index.html"
MIGRATIONS = FILES / "mvc" / "migrations"
DOC = ROOT / "docs" / "starters" / "welcome-iot" / "intermediaire" / "iot-dashboard.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 30"]


def test_resolves():
    m = resolve("iot-dashboard")
    assert m["id"] == "iot-dashboard" and m["number"] == 30
    assert m.get("requires_db") is True


def test_aliases():
    for a in ("iot-dashboard", "iot_dashboard", "30"):
        assert resolve(a)["id"] == "iot-dashboard"


def test_doc_url_pointe_welcome_iot():
    assert "welcome-iot/intermediaire/iot-dashboard" in resolve("iot-dashboard")["doc_url"]


def test_snippet_route():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = routes_from_snippet(snip)
    assert any(m == "GET" and p == "/iot-dashboard" for m, p, *_ in routes)


def test_controller_list_and_render():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_iot.storage import IotEventRepository" in text
    assert "list_recent(" in text
    assert "render(" in text and "iot_dashboard/index.html" in text
    # lecture seule
    assert "INSERT" not in text and "insert(" not in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "IotDashboardController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert "index" in methods


def test_view_table_and_empty_state():
    html = VIEW.read_text(encoding="utf-8")
    assert "{% for e in events %}" in html
    assert "{% if events %}" in html


def test_migration_creates_iot_events():
    sqls = list(MIGRATIONS.glob("*.sql"))
    assert sqls
    content = "\n".join(p.read_text(encoding="utf-8") for p in sqls)
    assert "CREATE TABLE IF NOT EXISTS iot_events" in content


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Tableau de bord IoT"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "iot-dashboard" in idx and "Tableau de bord IoT" in idx
