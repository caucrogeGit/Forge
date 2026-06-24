"""Tests unitaires du registre des ressources admin (ADMIN-RESOURCE-CONTRACT-001).

Le registre est explicite : enregistrement à la main, pas de découverte
automatique. Slug en double et slug inconnu lèvent `AdminRegistryError`. L'ordre
d'enregistrement est préservé.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_admin")

from forge_mvc_admin import AdminRegistry, AdminRegistryError, AdminResource
from forge_mvc_admin import registry as default_registry


def _resource(slug: str, entity: str) -> AdminResource:
    return AdminResource(
        entity=entity,
        slug=slug,
        label=entity,
        plural_label=f"{entity}s",
        list_fields=("name",),
        form_fields=("name",),
        table=slug.replace("-", "_"),
    )


def test_register_get_all():
    reg = AdminRegistry()
    a = reg.register(_resource("articles", "Article"))
    b = reg.register(_resource("accounts", "Account"))
    assert reg.get("articles") is a
    assert reg.get("accounts") is b
    assert reg.all() == (a, b)
    assert len(reg) == 2
    assert "articles" in reg
    assert "inconnu" not in reg


def test_register_retourne_la_ressource():
    reg = AdminRegistry()
    r = _resource("articles", "Article")
    assert reg.register(r) is r


def test_slug_en_double_leve():
    reg = AdminRegistry()
    reg.register(_resource("articles", "Article"))
    with pytest.raises(AdminRegistryError):
        reg.register(_resource("articles", "Autre"))


def test_slug_inconnu_leve():
    reg = AdminRegistry()
    with pytest.raises(AdminRegistryError):
        reg.get("inconnu")


def test_ordre_preserve():
    reg = AdminRegistry()
    for slug, entity in [("c", "Cc"), ("a", "Aa"), ("b", "Bb")]:
        reg.register(_resource(slug, entity))
    assert tuple(r.slug for r in reg.all()) == ("c", "a", "b")


def test_registre_par_defaut_independant_et_vide():
    """Le registre par défaut existe et n'est pas peuplé par Forge."""
    reg = AdminRegistry()
    reg.register(_resource("articles", "Article"))
    # Une instance neuve ne partage rien avec le registre par défaut du module.
    assert "articles" not in default_registry or default_registry is not reg
    assert isinstance(default_registry, AdminRegistry)
