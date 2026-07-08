from __future__ import annotations

import json
from pathlib import Path

import pytest

from cli.public.public_list import (
    build_public_list_controller,
    build_public_list_spec,
    build_public_list_template,
    load_public_list_definition,
    main,
    make_public_list,
    public_list_fields,
)


def _field(
    name: str,
    sql_type: str,
    *,
    column: str | None = None,
    python_type: str = "str",
    primary_key: bool = False,
    auto_increment: bool = False,
) -> dict:
    return {
        "name": name,
        "column": column or "".join(part.capitalize() for part in name.split("_")),
        "python_type": python_type,
        "sql_type": sql_type,
        "nullable": False,
        "primary_key": primary_key,
        "auto_increment": auto_increment,
        "constraints": {},
    }


HEBERGEMENT_JSON = {
    "entity": "Hebergement",
    "table": "hebergement",
    "description": "",
    "fields": [
        _field("id", "INT", column="Id", python_type="int", primary_key=True, auto_increment=True),
        _field("nom", "VARCHAR(120)", column="Nom"),
        _field("description", "TEXT", column="Description"),
        _field("prix", "DECIMAL(10,2)", column="Prix", python_type="float"),
        _field("commune_id", "INT", column="CommuneId", python_type="int"),
        _field("created_at", "DATETIME", column="CreatedAt", python_type="datetime"),
        _field("updated_at", "DATETIME", column="UpdatedAt", python_type="datetime"),
        _field("password_hash", "VARCHAR(255)", column="PasswordHash"),
        _field("token", "VARCHAR(255)", column="Token"),
        _field("secret", "VARCHAR(255)", column="Secret"),
    ],
}


def _prepare_project(root: Path, definition: dict = HEBERGEMENT_JSON) -> Path:
    entity = definition["entity"]
    snake = "hebergement" if entity == "Hebergement" else entity.lower()
    entity_dir = root / "mvc" / "entities" / snake
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{snake}.json").write_text(json.dumps(definition), encoding="utf-8")
    (root / "mvc" / "views" / "layouts").mkdir(parents=True, exist_ok=True)
    (root / "mvc" / "views" / "layouts" / "public.html").write_text(
        '{% block title %}Forge{% endblock %}\n'
        "{% block content %}{% endblock %}\n"
        "{% block scripts %}{% endblock %}\n",
        encoding="utf-8",
    )
    (root / "mvc" / "routes" / "__init__.py").parent.mkdir(parents=True, exist_ok=True)
    (root / "mvc" / "routes" / "__init__.py").write_text(
        "from core.http.router import Router\n"
        "\n"
        "router = Router()\n",
        encoding="utf-8",
    )
    return root / "mvc" / "entities"


def _read(root: Path, path: str) -> str:
    return (root / path).read_text(encoding="utf-8")


def test_make_public_list_refuse_entite_inexistante(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_public_list_definition("Inconnue", entities_root=tmp_path / "mvc" / "entities")


def test_make_public_list_genere_template_public_de_liste(tmp_path):
    _prepare_project(tmp_path)

    make_public_list("Hebergement", output_root=tmp_path)

    template = _read(tmp_path, "mvc/views/public/hebergements/index.html")
    assert '{% extends "layouts/base.html" %}' in template
    assert "{% block title %}Hebergements{% endblock %}" in template
    assert "{% block content %}" in template
    assert "{% block scripts %}{% endblock %}" in template
    assert "{% for row in hebergements %}" in template
    assert "trans('public.list.empty')" in template


def test_make_public_list_genere_controleur_public_dedie(tmp_path):
    _prepare_project(tmp_path)

    make_public_list("Hebergement", output_root=tmp_path)

    controller = _read(tmp_path, "mvc/controllers/public_hebergements_controller.py")
    assert "class PublicHebergementsController(BaseController):" in controller
    assert "def index(request: Request) -> Response:" in controller
    assert 'BaseController.render(\n            "public/hebergements/index.html",' in controller
    assert '"hebergements": rows' in controller


def test_make_public_list_ajoute_route_publique_idempotente(tmp_path):
    _prepare_project(tmp_path)

    make_public_list("Hebergement", output_root=tmp_path)
    make_public_list("Hebergement", output_root=tmp_path)

    routes = _read(tmp_path, "mvc/routes/__init__.py")
    assert "from mvc.controllers.public_hebergements_controller import PublicHebergementsController" in routes
    assert 'public.add("GET", "/hebergements", PublicHebergementsController.index, name="public_hebergements-index")' in routes
    assert routes.count('"/hebergements"') == 1
    assert routes.count('name="public_hebergements-index"') == 1


def test_make_public_list_necrase_pas_template_existant(tmp_path):
    _prepare_project(tmp_path)
    template = tmp_path / "mvc" / "views" / "public" / "hebergements" / "index.html"
    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_text("template manuel\n", encoding="utf-8")

    result = make_public_list("Hebergement", output_root=tmp_path)

    assert template.read_text(encoding="utf-8") == "template manuel\n"
    assert "mvc/views/public/hebergements/index.html" in result.preserved


def test_make_public_list_necrase_pas_controleur_existant(tmp_path):
    _prepare_project(tmp_path)
    controller = tmp_path / "mvc" / "controllers" / "public_hebergements_controller.py"
    controller.parent.mkdir(parents=True, exist_ok=True)
    controller.write_text("# controleur manuel\n", encoding="utf-8")

    result = make_public_list("Hebergement", output_root=tmp_path)

    assert controller.read_text(encoding="utf-8") == "# controleur manuel\n"
    assert "mvc/controllers/public_hebergements_controller.py" in result.preserved


def test_make_public_list_nexpose_aucun_lien_crud_admin():
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    generated = build_public_list_template(spec) + build_public_list_controller(spec)

    assert "/hebergements/new" not in generated
    assert "/edit" not in generated
    assert "/delete" not in generated
    assert "Supprimer" not in generated
    assert "Modifier" not in generated
    assert "layouts/admin.html" not in generated
    assert "crud" not in generated.lower()


def test_make_public_list_najoute_pas_dependances_optionnelles():
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    generated = build_public_list_template(spec) + build_public_list_controller(spec)

    assert "htmx" not in generated.lower()
    assert "hx-" not in generated
    assert "alpine" not in generated.lower()
    assert "_(" not in generated
    assert "<script" not in generated


def test_make_public_list_exclut_champs_sensibles_et_techniques():
    fields = public_list_fields(HEBERGEMENT_JSON)
    names = [field.name for field in fields]

    assert names == ["nom", "description", "prix"]
    assert "id" not in names
    assert "created_at" not in names
    assert "updated_at" not in names
    assert "password_hash" not in names
    assert "token" not in names
    assert "secret" not in names
    assert "commune_id" not in names


def test_make_public_list_genere_requete_sql_lisible():
    controller = build_public_list_controller(build_public_list_spec(HEBERGEMENT_JSON))

    assert 'SELECT_PUBLIC_LIST = "SELECT Nom AS nom, Description AS description, Prix AS prix FROM hebergement ORDER BY Id DESC"' in controller
    assert "cursor.execute(SELECT_PUBLIC_LIST)" in controller
    assert "get_connection()" in controller
    assert "ORM" not in controller


def test_make_public_list_reste_independant_de_make_crud(tmp_path):
    _prepare_project(tmp_path)

    make_public_list("Hebergement", output_root=tmp_path)

    generated = "\n".join(
        [
            _read(tmp_path, "mvc/views/public/hebergements/index.html"),
            _read(tmp_path, "mvc/controllers/public_hebergements_controller.py"),
            _read(tmp_path, "mvc/routes/__init__.py"),
        ]
    )
    assert "make_crud" not in generated
    assert "make:crud" not in generated
    assert "ContactController" not in generated


def test_make_public_list_cli_affiche_resume(tmp_path, capsys):
    _prepare_project(tmp_path)

    main(["Hebergement"], root=tmp_path)

    output = capsys.readouterr().out
    assert "Liste publique générée : Hebergement" in output
    assert "Route : /hebergements" in output
    assert "Template : mvc/views/public/hebergements/index.html" in output
    assert "Contrôleur : mvc/controllers/public_hebergements_controller.py" in output
