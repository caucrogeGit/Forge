"""Garde-fou STARTER-MFA-REVALIDATION-001 — palier 1 avancé welcome-mfa (slot 73)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "mfa-revalidation"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "mfa_revalidation_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "mfa_revalidation" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-mfa" / "avance" / "mfa-revalidation.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 73"]


def test_resolves():
    m = resolve("mfa-revalidation")
    assert m["id"] == "mfa-revalidation" and m["number"] == 73
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("mfa-revalidation", "mfa_revalidation", "73"):
        assert resolve(a)["id"] == "mfa-revalidation"


def test_doc_url():
    assert "welcome-mfa/avance/mfa-revalidation" in resolve("mfa-revalidation")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/mfa-revalidation") in routes
    assert ("POST", "/mfa-revalidation") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "mark_mfa_revalidated" in text and "has_recent_mfa_revalidation" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "MfaRevalidationController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert {"index", "revalidate"} <= {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Revalidation (step-up)"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "mfa-revalidation" in idx and "Revalidation (step-up)" in idx
