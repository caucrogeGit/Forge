"""Garde-fou STARTER-IOT-SUBSCRIBER-001 (test proportionné).

Contrat du palier 2 du niveau avancé de welcome-iot — Le subscriber MQTT :

- starter.json : `iot-subscriber`, slot 32, requires_db **false** ;
- snippet : GET `/iot-subscriber` ;
- contrôleur : `load_iot_config`, affiche la config broker (pas d'écoute web) ;
- vue : mentionne `forge iot:listen` et le topic ;
- documentation sous `avance/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "iot-subscriber"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "iot_subscriber_controller.py"
VIEW = FILES / "mvc" / "views" / "iot_subscriber" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-iot" / "avance" / "iot-subscriber.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 32"]


def test_resolves():
    m = resolve("iot-subscriber")
    assert m["id"] == "iot-subscriber" and m["number"] == 32
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("iot-subscriber", "iot_subscriber", "32"):
        assert resolve(a)["id"] == "iot-subscriber"


def test_doc_url_pointe_welcome_iot():
    assert "welcome-iot/avance/iot-subscriber" in resolve("iot-subscriber")["doc_url"]


def test_snippet_route():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = routes_from_snippet(snip)
    assert any(m == "GET" and p == "/iot-subscriber" for m, p, *_ in routes)


def test_controller_shows_broker_config():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_iot.config import load_iot_config" in text
    assert "load_iot_config()" in text
    assert "mqtt_host" in text and "mqtt_topic" in text
    assert "tls_enabled" in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "IotSubscriberController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert "index" in methods


def test_view_mentions_listen_command():
    html = VIEW.read_text(encoding="utf-8")
    assert "forge iot:listen" in html
    assert "{{ topic }}" in html


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Le subscriber MQTT"
    text = DOC.read_text(encoding="utf-8")
    assert "forge iot:listen" in text
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "iot-subscriber" in idx and "Le subscriber MQTT" in idx
