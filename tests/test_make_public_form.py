from __future__ import annotations

import ast
import json
from pathlib import Path

from core.http.request import Request


from forge_cli.public_form import (
    build_form_route_block,
    build_public_form_controller,
    build_public_form_create_method,
    build_public_form_spec,
    build_public_form_template,
    make_public_form,
    public_form_fields,
)
from tests.test_make_public_list import _field


DEMANDE_JSON = {
    "entity": "Demande",
    "table": "demande",
    "description": "",
    "fields": [
        _field("id", "INT", column="Id", python_type="int", primary_key=True, auto_increment=True),
        _field("prenom", "VARCHAR(80)", column="Prenom"),
        _field("nom", "VARCHAR(80)", column="Nom"),
        _field("email", "VARCHAR(120)", column="Email"),
        _field("message", "TEXT", column="Message"),
        _field("created_at", "DATETIME", column="CreatedAt", python_type="datetime"),
        _field("updated_at", "DATETIME", column="UpdatedAt", python_type="datetime"),
        _field("password_hash", "VARCHAR(255)", column="PasswordHash"),
        _field("commune_id", "INT", column="CommuneId", python_type="int"),
    ],
}

BOOL_JSON = {
    "entity": "Inscription",
    "table": "inscription",
    "description": "",
    "fields": [
        _field("id", "INT", column="Id", python_type="int", primary_key=True, auto_increment=True),
        _field("nom", "VARCHAR(80)", column="Nom"),
        _field("accepte_cgu", "TINYINT(1)", column="AccepteCgu", python_type="bool"),
        _field("age", "INT", column="Age", python_type="int"),
        _field("date_naissance", "DATE", column="DateNaissance", python_type="date"),
        _field("rdv_at", "DATETIME", column="RdvAt", python_type="datetime"),
        _field("site_web", "VARCHAR(255)", column="SiteWeb"),
        _field("phone_number", "VARCHAR(20)", column="PhoneNumber"),
    ],
}

SENSITIVE_ONLY_JSON = {
    "entity": "Secret",
    "table": "secret",
    "description": "",
    "fields": [
        _field("id", "INT", column="Id", python_type="int", primary_key=True, auto_increment=True),
        _field("password", "VARCHAR(255)", column="Password"),
        _field("api_token", "VARCHAR(255)", column="ApiToken"),
        _field("is_admin", "BOOL", column="IsAdmin", python_type="bool"),
        _field("is_active", "BOOL", column="IsActive", python_type="bool"),
    ],
}


def _prepare_form_project(root: Path, definition: dict) -> Path:
    snake = definition["entity"].lower()
    from forge_cli.entities.make_crud import _to_snake
    snake = _to_snake(definition["entity"])
    entity_dir = root / "mvc" / "entities" / snake
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{snake}.json").write_text(json.dumps(definition), encoding="utf-8")
    (root / "mvc" / "views" / "layouts").mkdir(parents=True, exist_ok=True)
    (root / "mvc" / "views" / "layouts" / "public.html").write_text(
        "{% block title %}{% endblock %}\n"
        "{% block content %}{% endblock %}\n"
        "{% block scripts %}{% endblock %}\n",
        encoding="utf-8",
    )
    (root / "mvc" / "routes.py").parent.mkdir(parents=True, exist_ok=True)
    (root / "mvc" / "routes.py").write_text(
        "from core.http.router import Router\n\nrouter = Router()\n",
        encoding="utf-8",
    )
    return root / "mvc" / "entities"


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


# --- public_form_fields ---

def test_public_form_fields_extrait_champs_non_sensibles():
    fields = public_form_fields(DEMANDE_JSON)

    names = [f.name for f in fields]
    assert "prenom" in names
    assert "nom" in names
    assert "email" in names
    assert "message" in names


def test_public_form_fields_ignore_primary_key():
    fields = public_form_fields(DEMANDE_JSON)

    names = [f.name for f in fields]
    assert "id" not in names


def test_public_form_fields_ignore_champs_sensibles():
    fields = public_form_fields(DEMANDE_JSON)

    names = [f.name for f in fields]
    assert "password_hash" not in names
    assert "created_at" not in names
    assert "updated_at" not in names


def test_public_form_fields_ignore_cles_etrangeres():
    fields = public_form_fields(DEMANDE_JSON)

    names = [f.name for f in fields]
    assert "commune_id" not in names


def test_public_form_fields_vide_si_que_champs_sensibles():
    fields = public_form_fields(SENSITIVE_ONLY_JSON)

    assert fields == []


def test_public_form_fields_input_type_textarea_pour_text():
    fields = public_form_fields(DEMANDE_JSON)

    message_field = next(f for f in fields if f.name == "message")
    assert message_field.input_type == "textarea"


def test_public_form_fields_input_type_email_detecte_par_nom():
    fields = public_form_fields(DEMANDE_JSON)

    email_field = next(f for f in fields if f.name == "email")
    assert email_field.input_type == "email"


def test_public_form_fields_input_types_varies():
    fields = public_form_fields(BOOL_JSON)

    by_name = {f.name: f for f in fields}
    assert by_name["accepte_cgu"].input_type == "checkbox"
    assert by_name["age"].input_type == "number"
    assert by_name["date_naissance"].input_type == "date"
    assert by_name["rdv_at"].input_type == "datetime-local"
    assert by_name["site_web"].input_type == "url"
    assert by_name["phone_number"].input_type == "tel"


def test_public_form_fields_required_si_non_nullable():
    fields = public_form_fields(DEMANDE_JSON)

    # All test fields have nullable=False → required=True
    for f in fields:
        assert f.required is True


# --- build_public_form_spec ---

def test_build_public_form_spec_route_path():
    spec = build_public_form_spec(DEMANDE_JSON)

    assert spec.route_path == "/demandes"
    assert spec.route_new_name == "public_demandes-new"
    assert spec.route_create_name == "public_demandes-create"


def test_build_public_form_spec_class_name():
    spec = build_public_form_spec(DEMANDE_JSON)

    assert spec.class_name == "PublicDemandesController"


def test_build_public_form_spec_template_name():
    spec = build_public_form_spec(DEMANDE_JSON)

    assert spec.template_name == "public/demandes/form.html"
    assert spec.template_path == Path("mvc/views/public/demandes/form.html")


def test_build_public_form_spec_controller_path():
    spec = build_public_form_spec(DEMANDE_JSON)

    assert spec.controller_path == Path("mvc/controllers/public_demandes_controller.py")


# --- build_public_form_controller ---

def test_form_controller_contient_insert_constant():
    spec = build_public_form_spec(DEMANDE_JSON)
    controller = build_public_form_controller(spec)

    assert "INSERT_PUBLIC_FORM" in controller
    assert "INSERT INTO demande" in controller
    assert "Prenom, Nom, Email, Message" in controller


def test_form_controller_contient_form_fields():
    spec = build_public_form_spec(DEMANDE_JSON)
    controller = build_public_form_controller(spec)

    assert "FORM_FIELDS" in controller
    assert '"name": "prenom"' in controller
    assert '"input_type": "email"' in controller
    assert '"input_type": "textarea"' in controller


def test_form_controller_importe_get_connection():
    spec = build_public_form_spec(DEMANDE_JSON)
    controller = build_public_form_controller(spec)

    assert "from core.database.connection import get_connection, close_connection" in controller


def test_form_controller_importe_render_flash_html():
    spec = build_public_form_spec(DEMANDE_JSON)
    controller = build_public_form_controller(spec)

    assert "from mvc.helpers.flash import render_flash_html" in controller


def test_form_controller_contient_methode_new():
    spec = build_public_form_spec(DEMANDE_JSON)
    controller = build_public_form_controller(spec)

    assert "def new(request: Request) -> Response:" in controller
    assert "FORM_FIELDS" in controller
    assert "render_flash_html(request)" in controller


def test_form_controller_contient_methode_create():
    spec = build_public_form_spec(DEMANDE_JSON)
    controller = build_public_form_controller(spec)

    assert "def create(request: Request) -> Response:" in controller
    assert "cursor.execute(INSERT_PUBLIC_FORM" in controller
    assert "connection.commit()" in controller
    assert "redirect_with_flash" in controller


def test_form_controller_validation_champs_requis():
    spec = build_public_form_spec(DEMANDE_JSON)
    method = build_public_form_create_method(spec)

    assert '_field["required"]' in method
    assert "est requis" in method


def test_form_controller_gere_checkbox():
    spec = build_public_form_spec(BOOL_JSON)
    method = build_public_form_create_method(spec)

    assert '"checkbox"' in method
    assert "1 if _raw else 0" in method


def _request_attrs_used(source: str) -> set[str]:
    """Collecte les accesseurs `request.<x>` utilisés dans un source généré."""
    used: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "request"
        ):
            used.add(node.attr)
    return used


def test_form_controller_compile_sans_erreur():
    """Le contrôleur généré doit au minimum compiler (garde anti-syntaxe)."""
    for definition in (DEMANDE_JSON, BOOL_JSON):
        spec = build_public_form_spec(definition)
        compile(build_public_form_controller(spec), "<generated>", "exec")


def test_form_controller_n_utilise_que_des_accesseurs_request_reels():
    """Garde-fou B1 : tout `request.<x>` du contrôleur généré doit exister
    réellement sur `Request` (post_data, supprimé, aurait été détecté ici)."""
    request_api = set(dir(Request))
    for definition in (DEMANDE_JSON, BOOL_JSON):
        spec = build_public_form_spec(definition)
        used = _request_attrs_used(build_public_form_controller(spec))
        assert used, "le contrôleur généré devrait lire au moins un champ de requête"
        unknown = used - request_api
        assert not unknown, (
            f"accesseur(s) Request inexistant(s) dans le contrôleur généré : {unknown}"
        )


def test_form_controller_lit_les_champs_via_request_form():
    """Le contrôleur lit les champs via l'accesseur canonique `request.form`,
    jamais via un attribut `post_data` (inexistant)."""
    spec = build_public_form_spec(DEMANDE_JSON)
    controller = build_public_form_controller(spec)

    assert "request.form(" in controller
    assert "post_data" not in controller


def test_form_controller_redirect_vers_new_apres_succes():
    spec = build_public_form_spec(DEMANDE_JSON)
    method = build_public_form_create_method(spec)

    assert '"/demandes/new"' in method


# --- build_public_form_template ---

def test_form_template_contient_form_post():
    spec = build_public_form_spec(DEMANDE_JSON)
    template = build_public_form_template(spec)

    assert 'method="post"' in template
    assert 'action="/demandes"' in template


def test_form_template_contient_csrf_token():
    spec = build_public_form_spec(DEMANDE_JSON)
    template = build_public_form_template(spec)

    assert 'name="csrf_token"' in template
    assert "{{ csrf_token }}" in template


def test_form_template_contient_boucle_fields():
    spec = build_public_form_spec(DEMANDE_JSON)
    template = build_public_form_template(spec)

    assert "{% for field in fields %}" in template
    assert "{{ field.label }}" in template
    assert "{{ field.name }}" in template


def test_form_template_contient_textarea_conditionnel():
    spec = build_public_form_spec(DEMANDE_JSON)
    template = build_public_form_template(spec)

    assert '{% if field.input_type == "textarea" %}' in template
    assert "<textarea" in template


def test_form_template_contient_checkbox_conditionnel():
    spec = build_public_form_spec(BOOL_JSON)
    template = build_public_form_template(spec)

    assert '{% elif field.input_type == "checkbox" %}' in template
    assert 'type="checkbox"' in template


def test_form_template_affiche_erreurs():
    spec = build_public_form_spec(DEMANDE_JSON)
    template = build_public_form_template(spec)

    assert "{% if field.name in errors %}" in template
    assert "{{ errors[field.name] }}" in template


def test_form_template_affiche_flash():
    spec = build_public_form_spec(DEMANDE_JSON)
    template = build_public_form_template(spec)

    assert "flash_html" in template
    assert "flash_html | safe" in template


def test_form_template_pas_htmx_ni_alpine():
    spec = build_public_form_spec(DEMANDE_JSON)
    template = build_public_form_template(spec)

    assert "htmx" not in template.lower()
    assert "hx-" not in template
    assert "alpine" not in template.lower()
    assert "<script" not in template


def test_form_template_pas_liens_admin():
    spec = build_public_form_spec(DEMANDE_JSON)
    template = build_public_form_template(spec)

    assert "/edit" not in template
    assert "/delete" not in template
    assert "layouts/admin.html" not in template


# --- build_form_route_block ---

def test_build_form_route_block_contient_get_new_et_post():
    spec = build_public_form_spec(DEMANDE_JSON)
    block = build_form_route_block(spec)

    assert '"GET"' in block
    assert '"/demandes/new"' in block
    assert '"POST"' in block
    assert '"/demandes"' in block
    assert 'name="public_demandes-new"' in block
    assert 'name="public_demandes-create"' in block


# --- Intégration make_public_form ---

def test_make_public_form_cree_template(tmp_path):
    _prepare_form_project(tmp_path, DEMANDE_JSON)

    make_public_form("Demande", output_root=tmp_path)

    template = _read(tmp_path, "mvc/views/public/demandes/form.html")
    assert 'method="post"' in template
    assert "csrf_token" in template


def test_make_public_form_cree_controleur(tmp_path):
    _prepare_form_project(tmp_path, DEMANDE_JSON)

    make_public_form("Demande", output_root=tmp_path)

    controller = _read(tmp_path, "mvc/controllers/public_demandes_controller.py")
    assert "INSERT_PUBLIC_FORM" in controller
    assert "FORM_FIELDS" in controller
    assert "def new(request: Request) -> Response:" in controller
    assert "def create(request: Request) -> Response:" in controller


def test_make_public_form_cree_routes(tmp_path):
    _prepare_form_project(tmp_path, DEMANDE_JSON)

    make_public_form("Demande", output_root=tmp_path)

    routes = _read(tmp_path, "mvc/routes.py")
    assert "PublicDemandesController" in routes
    assert '"/demandes/new"' in routes
    assert '"/demandes"' in routes


def test_make_public_form_preserve_template_existant(tmp_path):
    _prepare_form_project(tmp_path, DEMANDE_JSON)
    template_path = tmp_path / "mvc/views/public/demandes/form.html"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text("EXISTING", encoding="utf-8")

    result = make_public_form("Demande", output_root=tmp_path)

    assert template_path.read_text(encoding="utf-8") == "EXISTING"
    assert "mvc/views/public/demandes/form.html" in result.preserved


def test_make_public_form_apres_make_list_ajoute_methodes(tmp_path):
    from forge_cli.public_list import make_public_list
    _prepare_form_project(tmp_path, DEMANDE_JSON)
    make_public_list("Demande", output_root=tmp_path)

    make_public_form("Demande", output_root=tmp_path)

    controller = _read(tmp_path, "mvc/controllers/public_demandes_controller.py")
    assert "def index(request: Request) -> Response:" in controller
    assert "def new(request: Request) -> Response:" in controller
    assert "def create(request: Request) -> Response:" in controller
    assert "INSERT_PUBLIC_FORM" in controller
    assert "FORM_FIELDS" in controller


def test_make_public_form_idempotent(tmp_path):
    _prepare_form_project(tmp_path, DEMANDE_JSON)
    make_public_form("Demande", output_root=tmp_path)

    result2 = make_public_form("Demande", output_root=tmp_path)

    assert "mvc/controllers/public_demandes_controller.py" in result2.preserved
    assert "mvc/views/public/demandes/form.html" in result2.preserved


def test_make_public_form_avertit_si_aucun_champ(tmp_path):
    _prepare_form_project(tmp_path, SENSITIVE_ONLY_JSON)

    result = make_public_form("Secret", output_root=tmp_path)

    assert any("Aucun champ" in w for w in result.warnings)
