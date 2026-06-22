from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_i18n")

from forge_mvc_i18n import trans, load_catalog
from cli.public_contact import build_contact_template
from cli.public_form import build_public_form_spec, build_public_form_template
from cli.public_list import (
    build_public_list_spec,
    build_public_list_template,
    build_public_show_template,
)
from cli.public_page import build_public_page_spec, build_public_template
from tests.test_make_public_list import _field, HEBERGEMENT_JSON


# --- Clés i18n présentes dans translations/fr.json ---

CATALOG_PATH = Path("translations/fr.json")
PUBLIC_KEYS = [
    "public.page.generated",
    "public.list.empty",
    "public.show.back",
    "public.show.not_found",
    "public.form.submit",
    "public.form.success",
    "public.contact.title",
    "public.contact.intro",
    "public.contact.coordinates",
    "public.contact.address",
    "public.contact.email_label",
    "public.contact.phone",
    "public.contact.address_placeholder",
]


def test_catalogue_fr_contient_toutes_les_cles_publiques():
    catalog = load_catalog("fr")

    for key in PUBLIC_KEYS:
        assert key in catalog, f"Clé manquante : {key}"


def test_cles_publiques_ont_des_valeurs_non_vides():
    catalog = load_catalog("fr")

    for key in PUBLIC_KEYS:
        assert catalog.get(key, "").strip(), f"Valeur vide pour : {key}"


def test_trans_retourne_valeur_pour_cle_page_generated():
    assert trans("public.page.generated") == "Page publique générée par Forge."


def test_trans_retourne_valeur_pour_cle_list_empty():
    assert trans("public.list.empty") == "Aucun élément public à afficher."


def test_trans_retourne_valeur_pour_cle_show_back():
    assert trans("public.show.back") == "Retour"


def test_trans_retourne_valeur_pour_cle_form_submit():
    assert trans("public.form.submit") == "Envoyer"


def test_trans_retourne_valeur_pour_cle_contact_title():
    assert trans("public.contact.title") == "Contact"


def test_trans_retourne_valeur_pour_cle_contact_intro():
    assert trans("public.contact.intro") == "Vous pouvez nous contacter avec les informations ci-dessous."


# --- Utilisation de trans() dans les templates générés ---

def test_make_public_page_template_utilise_trans():
    spec = build_public_page_spec("accueil")
    template = build_public_template(spec)

    assert "trans('public.page.generated')" in template


def test_make_public_list_template_utilise_trans_pour_vide():
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    template = build_public_list_template(spec)

    assert "trans('public.list.empty')" in template


def test_make_public_show_template_utilise_trans_pour_retour():
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    template = build_public_show_template(spec)

    assert "trans('public.show.back')" in template


def test_make_public_show_template_utilise_trans_pour_introuvable():
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    template = build_public_show_template(spec)

    assert "trans('public.show.not_found')" in template


def test_make_public_form_template_utilise_trans_pour_bouton():
    definition = {
        "entity": "Demande",
        "table": "demande",
        "description": "",
        "fields": [
            _field("id", "INT", column="Id", python_type="int", primary_key=True, auto_increment=True),
            _field("nom", "VARCHAR(80)", column="Nom"),
        ],
    }
    spec = build_public_form_spec(definition)
    template = build_public_form_template(spec)

    assert "trans('public.form.submit')" in template


def test_make_public_contact_template_utilise_trans_pour_titre():
    template = build_contact_template()

    assert "trans('public.contact.title')" in template


def test_make_public_contact_template_utilise_trans_pour_intro():
    template = build_contact_template()

    assert "trans('public.contact.intro')" in template


def test_make_public_contact_template_utilise_trans_pour_coordonnees():
    template = build_contact_template()

    assert "trans('public.contact.coordinates')" in template


def test_make_public_contact_template_utilise_trans_pour_adresse():
    template = build_contact_template()

    assert "trans('public.contact.address')" in template


# --- Fallback : clé inconnue → retourne la clé ---

def test_trans_cle_inconnue_retourne_cle():
    result = trans("public.inexistant.xyz")

    assert result == "public.inexistant.xyz"


def test_templates_restent_utilisables_si_cle_absente(tmp_path):
    """Sans clé dans le catalogue, trans() retourne la clé — page lisible."""
    catalog_path = tmp_path / "translations" / "fr.json"
    catalog_path.parent.mkdir()
    catalog_path.write_text('{}', encoding="utf-8")

    from forge_mvc_i18n.translator import load_catalog as _load, trans as _trans
    catalog = _load("fr", tmp_path / "translations")
    assert "public.list.empty" not in catalog
    result = _trans("public.list.empty", translations_dir=tmp_path / "translations")
    assert result == "public.list.empty"


# --- Garanties négatives ---

def test_templates_publics_sans_routes_traduites():
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    templates = build_public_list_template(spec) + build_public_show_template(spec)

    assert "/fr/" not in templates
    assert "/en/" not in templates
    assert "locale" not in templates


def test_templates_publics_sans_noms_entite_traduits():
    """Les noms d'entité restent tels quels, non passés dans trans()."""
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    template = build_public_list_template(spec)

    assert "trans('hebergement" not in template
    assert "trans('Hebergement" not in template


def test_templates_publics_sans_htmx():
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    templates = (
        build_public_list_template(spec)
        + build_public_show_template(spec)
        + build_contact_template()
    )

    assert "htmx" not in templates.lower()
    assert "hx-" not in templates


def test_templates_publics_sans_alpine():
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    templates = (
        build_public_list_template(spec)
        + build_public_show_template(spec)
        + build_contact_template()
    )

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


def test_cles_publiques_coherentes_avec_convention_existante():
    """Toutes les clés commencent par 'public.' comme 'crud.' et 'common.'"""
    for key in PUBLIC_KEYS:
        assert key.startswith("public."), f"Clé hors convention : {key}"


def test_fichiers_existants_non_ecrases(tmp_path):
    """make:public-contact ne touche pas un template existant."""
    from tests.test_make_public_page import _prepare_project
    from cli.public_contact import make_public_contact

    _prepare_project(tmp_path)
    template_path = tmp_path / "mvc" / "views" / "public" / "contact.html"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text("VERSION PRECEDENTE", encoding="utf-8")

    make_public_contact(root=tmp_path)

    assert template_path.read_text(encoding="utf-8") == "VERSION PRECEDENTE"
