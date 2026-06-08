from __future__ import annotations


import pytest

from forge_cli.public_contact import build_contact_template, make_public_contact, main
from tests.test_make_public_page import _prepare_project, _read


# --- build_contact_template ---

def test_contact_template_etend_layout_public():
    template = build_contact_template()

    assert '{% extends "layouts/public.html" %}' in template


def test_contact_template_utilise_bloc_title():
    template = build_contact_template()

    assert "{% block title %}" in template
    assert "trans('public.contact.title')" in template
    assert "{% endblock %}" in template


def test_contact_template_utilise_bloc_content():
    template = build_contact_template()

    assert "{% block content %}" in template


def test_contact_template_utilise_bloc_scripts():
    template = build_contact_template()

    assert "{% block scripts %}" in template


def test_contact_template_contient_titre_contact():
    template = build_contact_template()

    assert "<h1" in template
    assert "trans('public.contact.title')" in template


def test_contact_template_contient_coordonnees():
    template = build_contact_template()

    assert "trans('public.contact.coordinates')" in template
    assert "contact@example.com" in template
    assert "trans('public.contact.phone')" in template


def test_contact_template_contient_adresse():
    template = build_contact_template()

    assert "trans('public.contact.address')" in template


def test_contact_template_contient_lien_mailto():
    template = build_contact_template()

    assert "mailto:" in template


def test_contact_template_pas_de_formulaire_post():
    template = build_contact_template()

    assert "<form" not in template
    assert 'method="post"' not in template


def test_contact_template_pas_de_htmx():
    template = build_contact_template()

    assert "htmx" not in template.lower()
    assert "hx-" not in template


def test_contact_template_pas_alpine():
    template = build_contact_template()

    assert "alpine" not in template.lower()
    assert "x-data" not in template


def test_contact_template_pas_de_script():
    template = build_contact_template()

    assert "<script" not in template


def test_contact_template_pas_de_liens_admin():
    template = build_contact_template()

    assert "/admin" not in template
    assert "layouts/admin.html" not in template
    assert "make:crud" not in template


def test_contact_template_pas_dentite_ni_crud():
    template = build_contact_template()

    assert "INSERT" not in template
    assert "SELECT" not in template
    assert "get_connection" not in template


# --- make_public_contact ---

def test_make_public_contact_cree_template(tmp_path):
    _prepare_project(tmp_path)

    make_public_contact(root=tmp_path)

    template = _read(tmp_path, "mvc/views/public/contact.html")
    assert '{% extends "layouts/public.html" %}' in template
    assert "trans('public.contact.title')" in template


def test_make_public_contact_cree_controleur(tmp_path):
    _prepare_project(tmp_path)

    make_public_contact(root=tmp_path)

    controller = _read(tmp_path, "mvc/controllers/public_pages_controller.py")
    assert "class PublicPagesController" in controller
    assert "def contact(request: Request) -> Response:" in controller
    assert 'BaseController.render("public/contact.html"' in controller


def test_make_public_contact_cree_route(tmp_path):
    _prepare_project(tmp_path)

    make_public_contact(root=tmp_path)

    routes = _read(tmp_path, "mvc/routes.py")
    assert "PublicPagesController" in routes
    assert '"/contact"' in routes
    assert 'name="public_pages-contact"' in routes


def test_make_public_contact_route_idempotente(tmp_path):
    _prepare_project(tmp_path)
    make_public_contact(root=tmp_path)

    make_public_contact(root=tmp_path)

    routes = _read(tmp_path, "mvc/routes.py")
    assert routes.count('"/contact"') == 1
    assert routes.count('name="public_pages-contact"') == 1


def test_make_public_contact_preserve_template_existant(tmp_path):
    _prepare_project(tmp_path)
    template_path = tmp_path / "mvc" / "views" / "public" / "contact.html"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text("CONTENU EXISTANT", encoding="utf-8")

    result = make_public_contact(root=tmp_path)

    assert template_path.read_text(encoding="utf-8") == "CONTENU EXISTANT"
    assert "mvc/views/public/contact.html" in result.preserved


def test_make_public_contact_preserve_controleur_existant(tmp_path):
    _prepare_project(tmp_path)
    from forge_cli.public_page import make_public_page
    make_public_page("accueil", root=tmp_path)

    make_public_contact(root=tmp_path)

    controller = _read(tmp_path, "mvc/controllers/public_pages_controller.py")
    assert "def accueil(request: Request) -> Response:" in controller
    assert "def contact(request: Request) -> Response:" in controller


def test_make_public_contact_idempotent(tmp_path):
    _prepare_project(tmp_path)
    make_public_contact(root=tmp_path)

    result2 = make_public_contact(root=tmp_path)

    assert "mvc/views/public/contact.html" in result2.preserved
    assert "mvc/controllers/public_pages_controller.py" in result2.preserved


def test_make_public_contact_resultat_cree(tmp_path):
    _prepare_project(tmp_path)

    result = make_public_contact(root=tmp_path)

    assert "mvc/views/public/contact.html" in result.created
    assert "mvc/controllers/public_pages_controller.py" in result.created


def test_make_public_contact_page_sans_formulaire_dans_fichier(tmp_path):
    _prepare_project(tmp_path)

    make_public_contact(root=tmp_path)

    template = _read(tmp_path, "mvc/views/public/contact.html")
    assert "<form" not in template
    assert 'method="post"' not in template


def test_make_public_contact_pas_de_traitement_mail(tmp_path):
    _prepare_project(tmp_path)

    make_public_contact(root=tmp_path)

    controller = _read(tmp_path, "mvc/controllers/public_pages_controller.py")
    template = _read(tmp_path, "mvc/views/public/contact.html")
    generated = controller + template
    assert "send_mail" not in generated
    assert "smtp" not in generated.lower()
    assert "mail" not in controller.lower()


def test_make_public_contact_pas_dentite_creee(tmp_path):
    _prepare_project(tmp_path)

    make_public_contact(root=tmp_path)

    controller = _read(tmp_path, "mvc/controllers/public_pages_controller.py")
    assert "INSERT" not in controller
    assert "get_connection" not in controller


# --- main() ---

def test_main_refuse_arguments(tmp_path):
    _prepare_project(tmp_path)

    with pytest.raises(SystemExit):
        main(["argument_inattendu"], root=tmp_path)


def test_main_sans_argument_fonctionne(tmp_path):
    _prepare_project(tmp_path)

    result = main([], root=tmp_path)

    assert result is not None


def test_main_affiche_resume(tmp_path, capsys):
    _prepare_project(tmp_path)

    main([], root=tmp_path)

    output = capsys.readouterr().out
    assert "Page contact générée" in output
    assert "Route : /contact" in output
    assert "mvc/views/public/contact.html" in output
