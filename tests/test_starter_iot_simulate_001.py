"""Garde-fou STARTER-IOT-SIMULATE-001 (test proportionné).

Contrat du palier 1 du niveau intermédiaire de welcome-iot — Simuler une mesure :

- starter.json : `iot-simulate`, slot 34, requires_db **true** ;
- snippet : GET formulaire, POST injection ;
- contrôleur : `build_payload` + `parse_message` + `IotEventRepository.insert`,
  gestion `ContractError`, CSRF, redirection (PRG) ;
- vue : formulaire POST + jeton CSRF + champs mesure ;
- migration `iot_events` ; documentation sous `intermediaire/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "iot-simulate"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "iot_simulate_controller.py"
VIEW = FILES / "mvc" / "views" / "iot_simulate" / "index.html"
MIGRATIONS = FILES / "mvc" / "migrations"
DOC = ROOT / "docs" / "starters" / "welcome-iot" / "intermediaire" / "iot-simulate.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 34"]


def test_resolves():
    m = resolve("iot-simulate")
    assert m["id"] == "iot-simulate" and m["number"] == 34
    assert m.get("requires_db") is True


def test_aliases():
    for a in ("iot-simulate", "iot_simulate", "34"):
        assert resolve(a)["id"] == "iot-simulate"


def test_doc_url_pointe_welcome_iot():
    assert "welcome-iot/intermediaire/iot-simulate" in resolve("iot-simulate")["doc_url"]


def test_snippet_routes():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = {(m, p) for m, p, *_ in routes_from_snippet(snip)}
    assert ("GET", "/iot-simulate") in routes
    assert ("POST", "/iot-simulate") in routes


def test_controller_simulate_flow():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_iot.cli.simulate import build_payload, build_topic, utc_timestamp" in text
    assert "from forge_mvc_iot.mqtt.contract import ContractError, parse_message" in text
    assert "from forge_mvc_iot.storage import IotEventRepository" in text
    assert "parse_message(" in text
    assert ".insert(" in text
    assert "ContractError" in text
    assert "csrf_token" in text
    assert "redirect(" in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "IotSimulateController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "simulate"} <= methods


def test_view_post_form_with_csrf():
    html = VIEW.read_text(encoding="utf-8")
    assert 'method="post"' in html
    assert 'name="csrf_token"' in html
    assert 'name="value"' in html and 'name="kind"' in html


def test_migration_creates_iot_events():
    sqls = list(MIGRATIONS.glob("*.sql"))
    assert sqls
    content = "\n".join(p.read_text(encoding="utf-8") for p in sqls)
    assert "CREATE TABLE IF NOT EXISTS iot_events" in content


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Simuler une mesure IoT"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "iot-simulate" in idx and "Simuler une mesure IoT" in idx
