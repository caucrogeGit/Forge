"""Garde-fou STARTER-IOT-EVENTS-001 (test proportionné).

Contrat du palier 2 du niveau débutant de welcome-iot — Lire les événements IoT :

- starter.json : `iot-events`, slot 26, requires_db **false** ;
- snippet : GET `/iot-events` ;
- contrôleur : `IotEventRepository.list_recent`, réponse `503` pédagogique si la
  table manque, `Response.json` ; pas d'écriture ;
- documentation sous `welcome-iot/debutant/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "iot-events"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "iot_events_controller.py"
DOC = ROOT / "docs" / "starters" / "welcome-iot" / "debutant" / "iot-events.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 26"]


def test_resolves():
    m = resolve("iot-events")
    assert m["id"] == "iot-events" and m["number"] == 26
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("iot-events", "iot_events", "26"):
        assert resolve(a)["id"] == "iot-events"


def test_doc_url_pointe_welcome_iot():
    assert "welcome-iot/debutant/iot-events" in resolve("iot-events")["doc_url"]


def test_snippet_route():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = routes_from_snippet(snip)
    assert any(m == "GET" and p == "/iot-events" for m, p, *_ in routes)


def test_controller_list_recent_and_pedagogical_state():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_iot.storage import IotEventRepository" in text
    assert "list_recent(" in text
    assert "status=503" in text
    assert "iot_storage_not_ready" in text
    assert "Response.json(" in text
    # palier en lecture seule
    assert "INSERT" not in text and "insert(" not in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "IotEventsController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert "index" in methods


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Lire les événements IoT"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "iot-events" in idx and "Lire les événements IoT" in idx
