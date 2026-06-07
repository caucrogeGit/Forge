"""Garde-fou STARTER-IOT-DEVICE-001 (test proportionné).

Contrat du palier 3 du niveau débutant de welcome-iot — Les événements d'un
capteur :

- starter.json : `iot-device`, slot 27, requires_db **false** ;
- snippet : GET `/iot-device/{site}/{device_id}` ;
- contrôleur : `route`, `find_by_device` + `count_by_device`, réponse
  `503` pédagogique ; lecture seule ;
- documentation sous `welcome-iot/debutant/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "iot-device"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "iot_device_controller.py"
DOC = ROOT / "docs" / "starters" / "welcome-iot" / "debutant" / "iot-device.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 27"]


def test_resolves():
    m = resolve("iot-device")
    assert m["id"] == "iot-device" and m["number"] == 27
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("iot-device", "iot_device", "27"):
        assert resolve(a)["id"] == "iot-device"


def test_doc_url_pointe_welcome_iot():
    assert "welcome-iot/debutant/iot-device" in resolve("iot-device")["doc_url"]


def test_snippet_route():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = routes_from_snippet(snip)
    assert any(m == "GET" and p == "/iot-device/{site}/{device_id}" for m, p, *_ in routes)


def test_controller_device_reads():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_iot.storage import IotEventRepository" in text
    assert 'request.route("site")' in text
    assert 'request.route("device_id")' in text
    assert "find_by_device(" in text
    assert "count_by_device(" in text
    assert "status=503" in text
    # lecture seule
    assert "INSERT" not in text and "insert(" not in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "IotDeviceController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert "index" in methods


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Les événements d'un capteur"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "iot-device" in idx and "Les événements d'un capteur" in idx
