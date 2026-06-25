"""Tests de l'intégration RBAC optionnelle (ADMIN-RBAC-INTEGRATION-001).

La garde de permission est opt-in (paramètre `permission`) et sans dépendance
dure : vérification via forge-mvc-rbac s'il est installé, fail-open sinon.
"""
from __future__ import annotations

import sys

import pytest

pytest.importorskip("forge_mvc_admin")

from core.http.router import Router
from forge_mvc_admin import AdminRegistry, AdminResource, register_admin_routes
from forge_mvc_admin.http import _permission_guard


class _Req:
    """Requête factice : la garde ne lit rien dessus, rbac est simulé."""


def _handler(_request: object) -> str:
    return "HANDLER"


def test_sans_permission_handler_inchange():
    # permission=None : aucune garde ajoutée, le handler est renvoyé tel quel.
    assert _permission_guard(_handler, None) is _handler


def test_refus_si_permission_manquante(monkeypatch):
    rbac = pytest.importorskip("forge_mvc_rbac")
    denial = object()
    appels: list[int] = []

    def fake_check(request, permission, *args, **kwargs):
        return denial

    monkeypatch.setattr(rbac, "require_contract_permission_for_request", fake_check)
    guarded = _permission_guard(lambda req: appels.append(1), "admin.access")
    assert guarded(_Req()) is denial
    assert not appels, "le handler ne doit pas être appelé en cas de refus"


def test_autorise_si_permission_presente(monkeypatch):
    rbac = pytest.importorskip("forge_mvc_rbac")

    def fake_check(request, permission, *args, **kwargs):
        return None

    monkeypatch.setattr(rbac, "require_contract_permission_for_request", fake_check)
    guarded = _permission_guard(_handler, "admin.access")
    assert guarded(_Req()) == "HANDLER"


def test_fail_closed_si_rbac_absent(monkeypatch):
    # ADMIN-RBAC-FAILCLOSED-001 : permission déclarée mais forge-mvc-rbac absent
    # -> la garde REFUSE (403), elle ne laisse plus passer silencieusement.
    monkeypatch.setitem(sys.modules, "forge_mvc_rbac", None)
    guarded = _permission_guard(_handler, "admin.access")
    response = guarded(_Req())
    assert response != "HANDLER"
    assert getattr(response, "status", None) == 403


def test_register_avec_permission_enregistre_les_routes():
    registry = AdminRegistry()
    registry.register(
        AdminResource(
            entity="Article",
            slug="articles",
            label="Article",
            plural_label="Articles",
            list_fields=("title",),
            form_fields=("title",),
            table="articles",
        )
    )
    router = Router()
    register_admin_routes(router, registry=registry, permission="admin.access")
    matched = router.match("GET", "/admin")
    assert matched is not None
    assert matched[0].public is False