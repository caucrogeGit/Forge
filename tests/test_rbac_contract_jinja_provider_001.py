"""C : provider Jinja can() adossé au CONTRAT (rbac.json), natif.

Manque terrain C : le provider auto-enregistré vise le modèle table (permissions/
role_permissions). Le provider contrat natif permet un can() de template adossé à
rbac.json, sans ces tables, et supprime le provider maison.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac import (
    make_contract_jinja_context,
    make_contract_jinja_context_with_can,
    register_contract_rbac_provider,
)
from forge_mvc_rbac.jinja import make_contract_jinja_can


def _contract(root: Path) -> None:
    sec = root / "mvc" / "security"
    sec.mkdir(parents=True, exist_ok=True)
    (sec / "rbac.json").write_text(
        json.dumps({
            "schema_version": "1.0",
            "roles": {
                "admin": ["article.delete", "article.list"],
                "viewer": ["article.list"],
            },
        }),
        encoding="utf-8",
    )


class _Req:
    def __init__(self, roles: object) -> None:
        self.roles = roles


class TestContractCan:

    def test_permission_granted_by_role(self, tmp_path: Path) -> None:
        _contract(tmp_path)
        can = make_contract_jinja_can(_Req(["viewer"]), project_root=tmp_path)
        assert can("article.list") is True
        assert can("article.delete") is False

    def test_admin_has_all(self, tmp_path: Path) -> None:
        _contract(tmp_path)
        can = make_contract_jinja_can(_Req(["admin"]), project_root=tmp_path)
        assert can("article.delete") is True

    def test_no_roles_denies(self, tmp_path: Path) -> None:
        _contract(tmp_path)
        can = make_contract_jinja_can(_Req([]), project_root=tmp_path)
        assert can("article.list") is False

    def test_missing_contract_denies_without_raising(self, tmp_path: Path) -> None:
        # Pas de rbac.json : can() refuse, ne lève jamais vers le template.
        can = make_contract_jinja_can(_Req(["admin"]), project_root=tmp_path)
        assert can("article.list") is False


class TestContractContext:

    def test_context_exposes_can_and_auth(self, tmp_path: Path) -> None:
        _contract(tmp_path)
        ctx = make_contract_jinja_context(_Req(["viewer"]), project_root=tmp_path)
        assert set(ctx) >= {"current_user", "is_authenticated", "can"}
        assert callable(ctx["can"])
        assert ctx["can"]("article.list") is True

    def test_with_can_wrapper_is_no_arg(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _contract(tmp_path)
        monkeypatch.chdir(tmp_path)
        ctx = make_contract_jinja_context_with_can(_Req(["admin"]))
        assert ctx["can"]("article.delete") is True


def test_register_contract_provider_does_not_raise() -> None:
    # L'enregistrement dans le registre core est disponible et sans effet de bord fatal.
    register_contract_rbac_provider()
