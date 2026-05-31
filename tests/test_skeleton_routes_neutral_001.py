"""SKELETON-ROUTES-NEUTRAL-001 — le squelette mvc/routes.py est neutre.

Après clone du dépôt ou installation via pipx, `mvc/routes.py` n'expose qu'une
seule route : `GET /` vers la landing page. Auth, MFA et le starter welcome ne
sont plus pré-câblés (ADR-016 D7) — ils s'ajoutent à la demande via les
starters / opt-ins.

Charte : principe 8 (noyau minimal, briques opt-in), principe 3 (refuser la
magie cachée), principe 1 (séparer framework et application métier).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ROUTES = PROJECT_ROOT / "mvc" / "routes.py"


@pytest.fixture(scope="module")
def routes_source() -> str:
    return ROUTES.read_text(encoding="utf-8")


class TestNeutralSkeletonPresence:
    """Ce que le squelette neutre DOIT contenir."""

    def test_routes_file_exists(self):
        assert ROUTES.exists()

    def test_home_route_on_root(self, routes_source):
        assert "HomeController" in routes_source
        assert '"GET", "/"' in routes_source

    def test_imports_are_minimal(self, routes_source):
        """Seuls Router et HomeController sont importés au niveau module."""
        tree = ast.parse(routes_source)
        modules = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ImportFrom):
                modules.append(node.module or "")
        assert modules == [
            "core.http.router",
            "mvc.controllers.home_controller",
        ], f"Imports inattendus dans le squelette neutre : {modules}"


class TestNeutralSkeletonAbsence:
    """Ce que le squelette neutre ne DOIT PLUS contenir (tests d'absence, §6)."""

    @pytest.mark.parametrize("forbidden", [
        "/login",
        "/logout",
        "/login/mfa",
        "/welcome",
        "mfa_available",
        "AuthController",
        "WelcomeController",
        "MfaChallengeController",
        "forge-starter:welcome",
    ])
    def test_token_absent_from_routes(self, routes_source, forbidden):
        assert forbidden not in routes_source, (
            f"{forbidden!r} ne doit plus être pré-câblé dans le squelette neutre "
            f"(SKELETON-ROUTES-NEUTRAL-001)."
        )
