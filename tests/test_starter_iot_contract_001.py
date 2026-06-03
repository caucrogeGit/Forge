"""Garde-fou STARTER-IOT-CONTRACT-001 (test proportionné).

Contrat du palier 1 du niveau avancé de welcome-iot — Valider un message IoT :

- starter.json : `iot-contract`, slot 37, requires_db **false** ;
- snippet : GET formulaire, POST validation ;
- contrôleur : `parse_message`, gestion `ContractError` (code + message), CSRF ;
  pas de base de données ;
- vue : formulaire POST + jeton CSRF + champs topic/payload ;
- documentation sous `avance/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "iot-contract"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "iot_contract_controller.py"
VIEW = FILES / "mvc" / "views" / "iot_contract" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-iot" / "avance" / "iot-contract.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 37"]


def test_resolves():
    m = resolve("iot-contract")
    assert m["id"] == "iot-contract" and m["number"] == 37
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("iot-contract", "iot_contract", "37"):
        assert resolve(a)["id"] == "iot-contract"


def test_doc_url_pointe_welcome_iot():
    assert "welcome-iot/avance/iot-contract" in resolve("iot-contract")["doc_url"]


def test_snippet_routes():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = {(m, p) for m, p, *_ in routes_from_snippet(snip)}
    assert ("GET", "/iot-contract") in routes
    assert ("POST", "/iot-contract") in routes


def test_controller_parse_message_and_error_code():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_iot.mqtt.contract import ContractError, parse_message" in text
    assert "parse_message(" in text
    assert "exc.code" in text
    assert "csrf_token" in text
    assert "core.database" not in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "IotContractController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "validate"} <= methods


def test_view_post_form_with_csrf():
    html = VIEW.read_text(encoding="utf-8")
    assert 'method="post"' in html
    assert 'name="csrf_token"' in html
    assert 'name="topic"' in html and 'name="payload"' in html


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Valider un message IoT"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "iot-contract" in idx and "Valider un message IoT" in idx
