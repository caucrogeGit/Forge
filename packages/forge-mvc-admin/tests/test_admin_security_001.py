"""Garde-fou ADMIN-CSRF-SECURITY-001.

Verrouille la sécurité des routes du back-office Forge Admin :

- aucune route `/admin` n'est publique ;
- toute route de mutation (méthode non sûre) exige le CSRF ;
- les routes GET ne demandent pas de CSRF (lecture seule) ;
- toutes les routes exigent l'authentification (`@require_auth`) : une requête
  non authentifiée est redirigée vers `/login`, avant toute lecture ou écriture.

Empêche qu'une future route admin soit ajoutée publique, sans CSRF ou sans auth.
Le CSRF des POST est déjà actif par défaut (`csrf=True`) ; ce test le verrouille.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_admin")
_testing = pytest.importorskip("forge_mvc_testing")
FakeRequest = _testing.FakeRequest

from core.http.router import UNSAFE_METHODS, Router
from forge_mvc_admin import AdminRegistry, AdminResource, register_admin_routes


def _admin_router() -> Router:
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
    register_admin_routes(router, registry=registry)
    return router


def _admin_entries():
    router = _admin_router()
    return [
        entry
        for entry in router._entries
        if entry.pattern == "/admin" or entry.pattern.startswith("/admin/")
    ]


def _methods(entry) -> list[str]:
    return entry.method if isinstance(entry.method, list) else [entry.method]


def test_couvre_le_crud_complet():
    entries = _admin_entries()
    assert len(entries) >= 8, f"routes admin attendues, trouvé {len(entries)}"
    post_routes = [e for e in entries if "POST" in _methods(e)]
    assert len(post_routes) >= 3, "création, édition et suppression sont des POST"


def test_aucune_route_admin_publique():
    for entry in _admin_entries():
        assert entry.public is False, f"{entry.pattern} ne doit pas être publique"


def test_mutations_exigent_csrf_lecture_non():
    for entry in _admin_entries():
        for method in _methods(entry):
            if method in UNSAFE_METHODS:
                assert entry.requires_csrf(method) is True, (
                    f"{method} {entry.pattern} doit exiger le CSRF"
                )
            else:
                assert entry.requires_csrf(method) is False, (
                    f"{method} {entry.pattern} (sûre) ne doit pas exiger le CSRF"
                )


def test_toutes_les_routes_exigent_authentification():
    for entry in _admin_entries():
        response = entry.handler(FakeRequest())
        assert response.status == 302, (
            f"{entry.pattern} doit rediriger un visiteur non authentifié"
        )
        assert response.headers.get("Location") == "/login", (
            f"{entry.pattern} doit rediriger vers /login"
        )
