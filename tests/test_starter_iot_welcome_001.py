"""Garde-fou STARTER-IOT-WELCOME-001 (test proportionné).

Contrat du palier 1 du niveau débutant de la progression welcome-iot —
Bonjour Forge IoT :

- starter.json : `iot-welcome`, slot 31, requires_db **false** ;
- snippet : GET `/iot-welcome`, GET `/iot-welcome/inspect` ;
- contrôleur : `load_iot_config`, mot de passe **masqué**, `Response.text` +
  `Response.json` ; pas de base de données ;
- documentation sous `welcome-iot/debutant/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "iot-welcome"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "iot_welcome_controller.py"
DOC = ROOT / "docs" / "starters" / "welcome-iot" / "debutant" / "iot-welcome.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 31"]


def test_resolves():
    m = resolve("iot-welcome")
    assert m["id"] == "iot-welcome" and m["number"] == 31
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("iot-welcome", "iot_welcome", "31"):
        assert resolve(a)["id"] == "iot-welcome"


def test_doc_url_pointe_welcome_iot():
    assert "welcome-iot/debutant/iot-welcome" in resolve("iot-welcome")["doc_url"]


def test_snippet_routes():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = {(m, p) for m, p, *_ in routes_from_snippet(snip)}
    assert ("GET", "/iot-welcome") in routes
    assert ("GET", "/iot-welcome/inspect") in routes


def test_controller_config_masked_no_db():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_iot.config import load_iot_config" in text
    assert "load_iot_config()" in text
    # mot de passe masqué — jamais exposé en clair
    assert '"***"' in text and "mqtt_password" in text
    assert "Response.text(" in text and "Response.json(" in text
    assert "core.database" not in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "IotWelcomeController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "inspect"} <= methods


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Bonjour Forge IoT"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "iot-welcome" in idx and "Bonjour Forge IoT" in idx
