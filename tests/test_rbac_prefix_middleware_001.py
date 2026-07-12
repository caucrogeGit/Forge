"""B : garde RBAC par préfixe d'URL en middleware (contrat).

Manque terrain B : le natif ne protège qu'au décorateur, route par route.
PrefixPermissionMiddleware protège des domaines entiers par préfixe, table
préfixe -> permission évaluée par requête (couvre les routes futures).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac import PrefixPermissionMiddleware


def _contract(root: Path) -> None:
    sec = root / "mvc" / "security"
    sec.mkdir(parents=True, exist_ok=True)
    (sec / "rbac.json").write_text(
        json.dumps({
            "schema_version": "1.0",
            "roles": {
                "admin": ["admin.access", "billing.view"],
                "comptable": ["billing.view"],
            },
        }),
        encoding="utf-8",
    )


class _Req:
    def __init__(self, path: str, roles: object) -> None:
        self.path = path
        self.roles = roles


def _mw(root: Path) -> PrefixPermissionMiddleware:
    return PrefixPermissionMiddleware(
        {"/admin": "admin.access", "/facturation": "billing.view"},
        project_root=root,
    )


class TestMatching:

    def test_no_rule_matches_passes(self, tmp_path: Path) -> None:
        _contract(tmp_path)
        assert _mw(tmp_path).check(_Req("/public", ["comptable"])) is None

    def test_prefix_boundary_not_substring(self, tmp_path: Path) -> None:
        _contract(tmp_path)
        # /administrateur ne doit PAS matcher /admin.
        assert _mw(tmp_path).check(_Req("/administrateur", [])) is None


class TestEnforcement:

    def test_denied_returns_403(self, tmp_path: Path) -> None:
        _contract(tmp_path)
        resp = _mw(tmp_path).check(_Req("/admin/users", ["comptable"]))
        assert resp is not None and resp.status == 403

    def test_granted_returns_none(self, tmp_path: Path) -> None:
        _contract(tmp_path)
        assert _mw(tmp_path).check(_Req("/admin/users", ["admin"])) is None

    def test_covers_nested_future_routes(self, tmp_path: Path) -> None:
        _contract(tmp_path)
        # N'importe quelle route sous /facturation est couverte, sans la déclarer.
        assert _mw(tmp_path).check(_Req("/facturation/2026/07/export", ["comptable"])) is None
        resp = _mw(tmp_path).check(_Req("/facturation/2026/07/export", []))
        assert resp is not None and resp.status == 403

    def test_exact_prefix_path(self, tmp_path: Path) -> None:
        _contract(tmp_path)
        assert _mw(tmp_path).check(_Req("/admin", ["admin"])) is None
        resp = _mw(tmp_path).check(_Req("/admin", []))
        assert resp is not None and resp.status == 403


class TestSpecificity:

    def test_most_specific_prefix_wins(self, tmp_path: Path) -> None:
        _contract(tmp_path)
        mw = PrefixPermissionMiddleware(
            {"/admin": "admin.access", "/admin/billing": "billing.view"},
            project_root=tmp_path,
        )
        # comptable a billing.view mais pas admin.access : sous /admin/billing,
        # c'est la règle la plus spécifique (billing.view) qui s'applique -> autorisé.
        assert mw.check(_Req("/admin/billing/x", ["comptable"])) is None
        # sous /admin (non /billing), c'est admin.access -> refusé pour comptable.
        resp = mw.check(_Req("/admin/users", ["comptable"]))
        assert resp is not None and resp.status == 403


class TestCustomDenied:

    def test_custom_denied_response(self, tmp_path: Path) -> None:
        from core.http.response import Response

        _contract(tmp_path)
        mw = PrefixPermissionMiddleware(
            {"/admin": "admin.access"},
            project_root=tmp_path,
            denied_response=lambda: Response(302, headers={"Location": "/login"}),
        )
        resp = mw.check(_Req("/admin", []))
        assert resp is not None and resp.status == 302
