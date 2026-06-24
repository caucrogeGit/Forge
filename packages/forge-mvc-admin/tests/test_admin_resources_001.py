"""Tests unitaires du contrat de ressource admin (ADMIN-RESOURCE-CONTRACT-001).

`AdminResource` valide sa propre forme à la construction : entité PascalCase,
slug d'URL, libellés non vides, champs snake_case non vides et sans doublon.
"""
from __future__ import annotations

import dataclasses

import pytest

pytest.importorskip("forge_mvc_admin")

from forge_mvc_admin import AdminResource, AdminResourceError


def _valid() -> AdminResource:
    return AdminResource(
        entity="Article",
        slug="articles",
        label="Article",
        plural_label="Articles",
        list_fields=("title", "published_at"),
        form_fields=("title", "body"),
    )


def test_ressource_valide():
    r = _valid()
    assert r.entity == "Article"
    assert r.slug == "articles"
    assert r.label == "Article"
    assert r.plural_label == "Articles"
    assert r.list_fields == ("title", "published_at")
    assert r.form_fields == ("title", "body")


def test_ressource_est_immuable():
    r = _valid()
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.slug = "autre"  # type: ignore[misc]


@pytest.mark.parametrize("bad_entity", ["article", "123Article", "Article-2", ""])
def test_entity_invalide(bad_entity: str):
    with pytest.raises(AdminResourceError):
        dataclasses.replace(_valid(), entity=bad_entity)


@pytest.mark.parametrize("bad_slug", ["Articles", "2articles", "art_icles", "art icles", ""])
def test_slug_invalide(bad_slug: str):
    with pytest.raises(AdminResourceError):
        dataclasses.replace(_valid(), slug=bad_slug)


@pytest.mark.parametrize("field_name", ["label", "plural_label"])
def test_libelle_vide(field_name: str):
    with pytest.raises(AdminResourceError):
        dataclasses.replace(_valid(), **{field_name: ""})


@pytest.mark.parametrize("field_name", ["list_fields", "form_fields"])
def test_champs_vides_refuses(field_name: str):
    with pytest.raises(AdminResourceError):
        dataclasses.replace(_valid(), **{field_name: ()})


@pytest.mark.parametrize("bad_field", ["Title", "1title", "title-x", ""])
def test_nom_de_champ_invalide(bad_field: str):
    with pytest.raises(AdminResourceError):
        dataclasses.replace(_valid(), list_fields=(bad_field,))


def test_champ_en_double_refuse():
    with pytest.raises(AdminResourceError):
        dataclasses.replace(_valid(), form_fields=("title", "title"))
