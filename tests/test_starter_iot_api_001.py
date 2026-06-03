"""Garde-fou STARTER-IOT-API-001 (test proportionné).

Contrat du palier 2 du niveau intermédiaire de welcome-iot — Exposer l'API IoT :

- starter.json : `iot-api`, slot 35, requires_db **true** ;
- snippet : branche `register_iot_routes(router)` (délégation au paquet) ;
- migration `iot_events` ;
- documentation sous `intermediaire/`, catalogue.

Ce palier n'a **pas** de contrôleur : il délègue l'API au paquet `forge-mvc-iot`.
"""
from __future__ import annotations

from pathlib import Path

from forge_cli.starters.registry import resolve


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "iot-api"
FILES = STARTER_DIR / "files"
MIGRATIONS = FILES / "mvc" / "migrations"
DOC = ROOT / "docs" / "starters" / "welcome-iot" / "intermediaire" / "iot-api.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 35"]


def test_resolves():
    m = resolve("iot-api")
    assert m["id"] == "iot-api" and m["number"] == 35
    assert m.get("requires_db") is True


def test_aliases():
    for a in ("iot-api", "iot_api", "35"):
        assert resolve(a)["id"] == "iot-api"


def test_doc_url_pointe_welcome_iot():
    assert "welcome-iot/intermediaire/iot-api" in resolve("iot-api")["doc_url"]


def test_snippet_delegates_to_package():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    assert "# forge-starter:iot-api:start" in snip
    assert "# forge-starter:iot-api:end" in snip
    assert "from forge_mvc_iot import register_iot_routes" in snip
    assert "register_iot_routes(router)" in snip


def test_no_controller_pure_delegation():
    # Le palier délègue au paquet : aucun contrôleur applicatif.
    controllers = FILES / "mvc" / "controllers"
    assert not controllers.exists() or not list(controllers.glob("*.py"))


def test_migration_creates_iot_events():
    sqls = list(MIGRATIONS.glob("*.sql"))
    assert sqls
    content = "\n".join(p.read_text(encoding="utf-8") for p in sqls)
    assert "CREATE TABLE IF NOT EXISTS iot_events" in content


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Exposer l'API IoT"
    text = DOC.read_text(encoding="utf-8")
    assert "register_iot_routes" in text
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "iot-api" in idx and "Exposer l'API IoT" in idx
