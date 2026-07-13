"""Contrat des gabarits publics : français LITTÉRAL, sans trans().

Décision : comme le CRUD, les pages publiques générées (`make:public-*`)
portent des libellés français littéraux, pas d'appel `trans()`. Un projet neuf
n'installe pas `forge-mvc-i18n` : le repli du cœur renverrait la clé brute, donc
un catalogue ne suffirait pas à rendre la page française out-of-the-box. Le
générateur émet donc directement le texte. L'i18n reste un opt-in que
l'application câble elle-même si elle vise le multilingue.

Ce fichier remplace l'ancien contrat i18n des pages publiques (clés `public.*`
+ catalogue de référence), retiré avec le passage au littéral.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.meta

from cli.public.public_contact import build_contact_template
from cli.public.public_form import build_public_form_spec, build_public_form_template
from cli.public.public_list import (
    build_public_list_spec,
    build_public_list_template,
    build_public_show_template,
)
from cli.public.public_page import build_public_page_spec, build_public_template
from tests.test_make_public_list import _field, HEBERGEMENT_JSON


def _form_template() -> str:
    definition = {
        "entity": "Demande",
        "table": "demande",
        "description": "",
        "fields": [
            _field("id", "INT", column="Id", python_type="int", primary_key=True, auto_increment=True),
            _field("nom", "VARCHAR(80)", column="Nom"),
        ],
    }
    return build_public_form_template(build_public_form_spec(definition))


def _all_templates() -> str:
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    return (
        build_public_template(build_public_page_spec("accueil"))
        + build_public_list_template(spec)
        + build_public_show_template(spec)
        + build_contact_template()
        + _form_template()
    )


# --- Libellés français littéraux dans les gabarits générés ---

def test_page_template_libelle_litteral():
    template = build_public_template(build_public_page_spec("accueil"))
    assert "Page publique générée par Forge." in template


def test_list_template_vide_litteral():
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    assert "Aucun élément public à afficher." in build_public_list_template(spec)


def test_show_template_retour_et_introuvable_litteraux():
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    template = build_public_show_template(spec)
    assert ">Retour</a>" in template
    assert "Élément public introuvable." in template


def test_form_template_bouton_litteral():
    assert "Envoyer" in _form_template()


@pytest.mark.parametrize(
    "libelle",
    [
        "Contact",
        "Vous pouvez nous contacter avec les informations ci-dessous.",
        "Coordonnées",
        "Téléphone",
        "Adresse",
        "Adresse à compléter",
    ],
)
def test_contact_template_libelles_litteraux(libelle: str):
    assert libelle in build_contact_template()


# --- Garantie : plus aucun trans('public.*') dans les gabarits ---

def test_gabarits_publics_sans_trans():
    templates = _all_templates()
    assert "trans(" not in templates


# --- Garanties négatives (inchangées) ---

def test_templates_publics_sans_routes_traduites():
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    templates = build_public_list_template(spec) + build_public_show_template(spec)
    assert "/fr/" not in templates
    assert "/en/" not in templates
    assert "locale" not in templates


def test_templates_publics_sans_htmx():
    templates = _all_templates()
    assert "htmx" not in templates.lower()
    assert "hx-" not in templates


def test_templates_publics_sans_alpine():
    templates = _all_templates()
    assert "alpine" not in templates.lower()
    assert "x-data" not in templates


def test_templates_publics_sans_crud_admin():
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    templates = (
        build_public_list_template(spec)
        + build_public_show_template(spec)
        + build_contact_template()
    )
    assert "/edit" not in templates
    assert "/delete" not in templates
    assert "layouts/admin.html" not in templates
