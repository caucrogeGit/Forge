"""Garde-fou STARTER-MAIL-DOCTOR-001 — Diagnostiquer le module Mail (slot 107)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "mail-doctor"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "mail_doctor_controller.py"
DOC = ROOT / "docs" / "starters" / "welcome-mail" / "avance" / "mail-doctor.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 107"]


def test_resolves():
    m = resolve("mail-doctor")
    assert m["id"] == "mail-doctor" and m["number"] == 107
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("mail-doctor", "mail_doctor", "107"):
        assert resolve(a)["id"] == "mail-doctor"


def test_doc_url():
    assert "welcome-mail/avance/mail-doctor" in resolve("mail-doctor")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/mail-doctor") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "MailDoctorController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert "index" in {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Diagnostiquer le module Mail"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "mail-doctor" in idx and "Diagnostiquer le module Mail" in idx
