from __future__ import annotations

import pytest

from cli.public.public_list import (
    build_public_list_spec,
    build_public_show_controller,
    build_public_show_template,
    load_public_list_definition,
    make_public_list,
    make_public_show,
)
from cli.public.public_show import main
from tests.test_make_public_list import HEBERGEMENT_JSON, _prepare_project, _read


def test_make_public_show_refuse_entite_inexistante(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_public_list_definition("Inconnue", entities_root=tmp_path / "mvc" / "entities")


def test_make_public_show_genere_template_public(tmp_path):
    _prepare_project(tmp_path)

    make_public_show("Hebergement", output_root=tmp_path)

    template = _read(tmp_path, "mvc/views/public/hebergements/show.html")
    assert '{% extends "layouts/base.html" %}' in template
    assert "{% block title %}Hebergement{% endblock %}" in template
    assert "{% block content %}" in template
    assert "{% block scripts %}{% endblock %}" in template
    assert "{{ hebergement[field.name] }}" in template
    assert "Élément public introuvable." in template
    assert '<a href="{{ back_url }}"' in template


def test_make_public_show_genere_controleur_public_dedie(tmp_path):
    _prepare_project(tmp_path)

    make_public_show("Hebergement", output_root=tmp_path)

    controller = _read(tmp_path, "mvc/controllers/public_hebergements_controller.py")
    assert "class PublicHebergementsController(BaseController):" in controller
    assert "def show(request: Request) -> Response:" in controller
    assert 'BaseController.render(\n            "public/hebergements/show.html",' in controller
    assert '"hebergement": row' in controller
    assert "return BaseController.not_found()" in controller


def test_make_public_show_complete_controleur_public_existant(tmp_path):
    _prepare_project(tmp_path)
    make_public_list("Hebergement", output_root=tmp_path)

    make_public_show("Hebergement", output_root=tmp_path)

    controller = _read(tmp_path, "mvc/controllers/public_hebergements_controller.py")
    assert "def index(request: Request) -> Response:" in controller
    assert "def show(request: Request) -> Response:" in controller
    assert "SELECT_PUBLIC_LIST" in controller
    assert "SELECT_PUBLIC_DETAIL" in controller


def test_make_public_show_ajoute_route_publique_idempotente(tmp_path):
    _prepare_project(tmp_path)

    make_public_show("Hebergement", output_root=tmp_path)
    make_public_show("Hebergement", output_root=tmp_path)

    routes = _read(tmp_path, "mvc/routes/__init__.py")
    assert "from mvc.controllers.public_hebergements_controller import PublicHebergementsController" in routes
    assert 'public.add("GET", "/hebergements/{id}", PublicHebergementsController.show, name="public_hebergements-show")' in routes
    assert routes.count('"/hebergements/{id}"') == 1
    assert routes.count('name="public_hebergements-show"') == 1


def test_make_public_show_necrase_pas_template_existant(tmp_path):
    _prepare_project(tmp_path)
    template = tmp_path / "mvc" / "views" / "public" / "hebergements" / "show.html"
    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_text("template show manuel\n", encoding="utf-8")

    result = make_public_show("Hebergement", output_root=tmp_path)

    assert template.read_text(encoding="utf-8") == "template show manuel\n"
    assert "mvc/views/public/hebergements/show.html" in result.preserved


def test_make_public_show_necrase_pas_controleur_existant_non_reconnu(tmp_path):
    _prepare_project(tmp_path)
    controller = tmp_path / "mvc" / "controllers" / "public_hebergements_controller.py"
    controller.parent.mkdir(parents=True, exist_ok=True)
    controller.write_text("# controleur manuel\n", encoding="utf-8")

    result = make_public_show("Hebergement", output_root=tmp_path)

    assert controller.read_text(encoding="utf-8") == "# controleur manuel\n"
    assert "mvc/controllers/public_hebergements_controller.py" in result.preserved
    assert result.warnings
    assert "public_hebergements_controller" not in _read(tmp_path, "mvc/routes/__init__.py")


def test_make_public_show_genere_requete_sql_visible():
    controller = build_public_show_controller(build_public_list_spec(HEBERGEMENT_JSON))

    assert 'SELECT_PUBLIC_DETAIL = "SELECT Nom AS nom, Description AS description, Prix AS prix FROM hebergement WHERE Id = ?"' in controller
    assert "cursor.execute(SELECT_PUBLIC_DETAIL, (public_id,))" in controller
    assert "get_connection()" in controller
    assert "ORM" not in controller


def test_make_public_show_exclut_champs_sensibles_et_id_bruts():
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    generated = build_public_show_template(spec) + build_public_show_controller(spec)

    assert '"fields": [{\'name\': \'nom\'' in generated
    assert "password_hash" not in generated
    assert "created_at" not in generated
    assert "updated_at" not in generated
    assert "commune_id" not in generated
    assert "token" not in generated
    assert "secret" not in generated


def test_make_public_show_nexpose_aucun_lien_crud_admin():
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    generated = build_public_show_template(spec) + build_public_show_controller(spec)

    assert "/hebergements/new" not in generated
    assert "/edit" not in generated
    assert "/delete" not in generated
    assert "Supprimer" not in generated
    assert "Modifier" not in generated
    assert "layouts/admin.html" not in generated
    assert "crud" not in generated.lower()


def test_make_public_show_najoute_pas_dependances_optionnelles():
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    generated = build_public_show_template(spec) + build_public_show_controller(spec)

    assert "htmx" not in generated.lower()
    assert "hx-" not in generated
    assert "alpine" not in generated.lower()
    assert "_(" not in generated
    assert "<script" not in generated


def test_make_public_show_reste_independant_de_make_crud(tmp_path):
    _prepare_project(tmp_path)

    make_public_show("Hebergement", output_root=tmp_path)

    generated = "\n".join(
        [
            _read(tmp_path, "mvc/views/public/hebergements/show.html"),
            _read(tmp_path, "mvc/controllers/public_hebergements_controller.py"),
            _read(tmp_path, "mvc/routes/__init__.py"),
        ]
    )
    assert "make_crud" not in generated
    assert "make:crud" not in generated
    assert "ContactController" not in generated


def test_make_public_show_cli_affiche_resume(tmp_path, capsys):
    _prepare_project(tmp_path)

    main(["Hebergement"], root=tmp_path)

    output = capsys.readouterr().out
    assert "Fiche publique générée : Hebergement" in output
    assert "Route : /hebergements/{id}" in output
    assert "Template : mvc/views/public/hebergements/show.html" in output
    assert "Contrôleur : mvc/controllers/public_hebergements_controller.py" in output
