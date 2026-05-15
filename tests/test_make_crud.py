"""Tests de forge make:crud — V1.0.

Garantit que make:crud :
- génère contrôleur, model, form, layout, vues index/show/form ;
- ne jamais écraser les fichiers existants ([PRÉSERVÉ]) ;
- --dry-run n'écrit rien mais calcule le rapport complet ;
- affiche le bloc de routes avec /new avant /{id} ;
- lève SystemExit si l'entité est absente ou le JSON invalide ;
- exclut la PK du formulaire ;
- génère les champs non-PK dans form.html ;
- génère la fonction de conversion colonnes SQL → noms champs formulaire ;
- utilise des requêtes SQL paramétrées avec ? ;
- lit table name et primary key depuis le JSON ;
- émet [WARN] pour DATE/DATETIME (type approximatif).
"""
import json
from pathlib import Path

import pytest

from forge_cli.entities.make_crud import (
    MakeCrudResult,
    build_controller,
    build_form,
    build_form_view,
    build_index_view,
    build_layout,
    build_model,
    build_pagination_partial,
    build_show_view,
    build_table_partial,
    make_crud,
    _to_snake,
)


# ── Fixtures JSON (format normalisé — tel que retourné par validate_entity_definition) ──

def _field(name, sql_type, *, python_type, primary_key=False, auto_increment=False,
           nullable=False, constraints=None, unique=False):
    col = "".join(p.capitalize() for p in name.split("_") if p)
    return {
        "name": name, "column": col, "python_type": python_type,
        "sql_type": sql_type, "nullable": nullable, "primary_key": primary_key,
        "auto_increment": auto_increment, "constraints": constraints or {}, "unique": unique,
    }


_CONTACT_JSON = {
    "format_version": 1,
    "entity": "Contact",
    "table": "contact",
    "description": "",
    "fields": [
        _field("id",    "INT",          python_type="int", primary_key=True, auto_increment=True),
        _field("nom",   "VARCHAR(100)", python_type="str", constraints={"not_empty": True, "max_length": 100}),
        _field("email", "VARCHAR(150)", python_type="str", nullable=True),
    ],
}

_CONTACT_WITH_VILLE_JSON = {
    "format_version": 1,
    "entity": "Contact",
    "table": "contact",
    "description": "",
    "fields": [
        _field("id",       "INT",          python_type="int", primary_key=True, auto_increment=True),
        _field("nom",      "VARCHAR(100)", python_type="str", constraints={"not_empty": True, "max_length": 100}),
        _field("ville_id", "INT",          python_type="int", nullable=True),
    ],
}

_VILLE_JSON = {
    "format_version": 1,
    "entity": "Ville",
    "table": "ville",
    "description": "",
    "fields": [
        _field("id",  "INT",          python_type="int", primary_key=True, auto_increment=True),
        _field("nom", "VARCHAR(100)", python_type="str"),
    ],
}

_VILLE_PK_ONLY_JSON = {
    "format_version": 1,
    "entity": "Ville",
    "table": "ville",
    "description": "",
    "fields": [
        _field("id", "INT", python_type="int", primary_key=True, auto_increment=True),
    ],
}

_CONTACT_VILLE_RELATIONS_JSON = {
    "format_version": 1,
    "relations": [
        {
            "name": "contact_ville",
            "type": "many_to_one",
            "from_entity": "Contact",
            "to_entity": "Ville",
            "from_field": "ville_id",
            "to_field": "id",
            "foreign_key_name": "fk_contact_ville",
            "on_delete": "SET NULL",
            "on_update": "CASCADE",
        }
    ],
}

_EVENEMENT_JSON = {
    "format_version": 1,
    "entity": "Evenement",
    "table": "evenement",
    "description": "",
    "fields": [
        _field("id",         "INT",  python_type="int", primary_key=True, auto_increment=True),
        _field("date_debut", "DATE", python_type="date"),
    ],
}

_PRODUIT_JSON = {
    "format_version": 1,
    "entity": "Produit",
    "table": "produit",
    "description": "",
    "fields": [
        _field("id",          "INT",          python_type="int",   primary_key=True, auto_increment=True),
        _field("libelle",     "VARCHAR(80)",  python_type="str"),
        _field("prix",        "DECIMAL(10,2)", python_type="float"),
        _field("description", "TEXT",         python_type="str",  nullable=True),
    ],
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_entity(tmp_path: Path, data: dict) -> Path:
    entity = data["entity"]
    snake = _to_snake(entity)
    entity_dir = tmp_path / "mvc" / "entities" / snake
    entity_dir.mkdir(parents=True, exist_ok=True)
    json_path = entity_dir / f"{snake}.json"
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return tmp_path / "mvc" / "entities"


def _make_entities(tmp_path: Path, *definitions: dict, relations: dict | None = None) -> Path:
    entities_root = tmp_path / "mvc" / "entities"
    for definition in definitions:
        _make_entity(tmp_path, definition)
    if relations is not None:
        entities_root.mkdir(parents=True, exist_ok=True)
        (entities_root / "relations.json").write_text(json.dumps(relations), encoding="utf-8")
    return entities_root


def _run(entity_name: str, tmp_path: Path, data: dict = None, dry_run: bool = False) -> MakeCrudResult:
    d = data if data is not None else _CONTACT_JSON
    entities_root = _make_entity(tmp_path, d)
    return make_crud(
        entity_name,
        entities_root=entities_root,
        output_root=tmp_path,
        dry_run=dry_run,
    )


# ── Génération des fichiers ────────────────────────────────────────────────────

def test_controller_genere(tmp_path):
    _run("Contact", tmp_path)
    assert (tmp_path / "mvc" / "controllers" / "contact_controller.py").exists()


def test_model_genere(tmp_path):
    _run("Contact", tmp_path)
    assert (tmp_path / "mvc" / "models" / "contact_model.py").exists()


def test_form_genere(tmp_path):
    _run("Contact", tmp_path)
    assert (tmp_path / "mvc" / "forms" / "contact_form.py").exists()


def test_layout_genere(tmp_path):
    _run("Contact", tmp_path)
    assert (tmp_path / "mvc" / "views" / "layouts" / "app.html").exists()


def test_index_html_genere(tmp_path):
    _run("Contact", tmp_path)
    assert (tmp_path / "mvc" / "views" / "contact" / "index.html").exists()


def test_show_html_genere(tmp_path):
    _run("Contact", tmp_path)
    assert (tmp_path / "mvc" / "views" / "contact" / "show.html").exists()


def test_form_html_genere(tmp_path):
    _run("Contact", tmp_path)
    assert (tmp_path / "mvc" / "views" / "contact" / "form.html").exists()


def test_make_crud_sans_relations_json_continue_de_fonctionner(tmp_path):
    result = _run("Contact", tmp_path, data=_CONTACT_WITH_VILLE_JSON)

    form_code = (tmp_path / "mvc" / "forms" / "contact_form.py").read_text(encoding="utf-8")
    form_html = (tmp_path / "mvc" / "views" / "contact" / "form.html").read_text(encoding="utf-8")
    assert len(result.created) == 13
    assert "ChoiceField" not in form_code
    assert "<select" not in form_html


def test_make_crud_avec_relations_json_vide_continue_de_fonctionner(tmp_path):
    entities_root = _make_entities(
        tmp_path,
        _CONTACT_WITH_VILLE_JSON,
        relations={"format_version": 1, "relations": []},
    )

    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)

    form_code = (tmp_path / "mvc" / "forms" / "contact_form.py").read_text(encoding="utf-8")
    assert "ChoiceField" not in form_code


# ── Non-écrasement ─────────────────────────────────────────────────────────────

def test_non_ecrasement_controller(tmp_path):
    entities_root = _make_entity(tmp_path, _CONTACT_JSON)
    ctrl_path = tmp_path / "mvc" / "controllers" / "contact_controller.py"
    ctrl_path.parent.mkdir(parents=True, exist_ok=True)
    ctrl_path.write_text("# existant", encoding="utf-8")

    result = make_crud("Contact", entities_root=entities_root, output_root=tmp_path)

    assert ctrl_path in result.preserved
    assert ctrl_path.read_text(encoding="utf-8") == "# existant"


def test_non_ecrasement_form(tmp_path):
    entities_root = _make_entity(tmp_path, _CONTACT_JSON)
    form_path = tmp_path / "mvc" / "forms" / "contact_form.py"
    form_path.parent.mkdir(parents=True, exist_ok=True)
    form_path.write_text("# existant", encoding="utf-8")

    result = make_crud("Contact", entities_root=entities_root, output_root=tmp_path)

    assert form_path in result.preserved
    assert form_path.read_text(encoding="utf-8") == "# existant"


def test_non_ecrasement_layout(tmp_path):
    entities_root = _make_entity(tmp_path, _CONTACT_JSON)
    layout_path = tmp_path / "mvc" / "views" / "layouts" / "app.html"
    layout_path.parent.mkdir(parents=True, exist_ok=True)
    layout_path.write_text("<!-- existant -->", encoding="utf-8")

    result = make_crud("Contact", entities_root=entities_root, output_root=tmp_path)

    assert layout_path in result.preserved
    assert layout_path.read_text(encoding="utf-8") == "<!-- existant -->"


def test_non_ecrasement_vue_index(tmp_path):
    entities_root = _make_entity(tmp_path, _CONTACT_JSON)
    index_path = tmp_path / "mvc" / "views" / "contact" / "index.html"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("<!-- existant -->", encoding="utf-8")

    result = make_crud("Contact", entities_root=entities_root, output_root=tmp_path)

    assert index_path in result.preserved
    assert index_path.read_text(encoding="utf-8") == "<!-- existant -->"


# ── Dry-run ────────────────────────────────────────────────────────────────────

def test_dry_run_necrit_rien(tmp_path):
    _run("Contact", tmp_path, dry_run=True)
    assert not (tmp_path / "mvc" / "controllers" / "contact_controller.py").exists()
    assert not (tmp_path / "mvc" / "models" / "contact_model.py").exists()
    assert not (tmp_path / "mvc" / "forms" / "contact_form.py").exists()
    assert not (tmp_path / "mvc" / "views" / "layouts" / "app.html").exists()
    assert not (tmp_path / "mvc" / "views" / "contact" / "index.html").exists()


def test_dry_run_rapporte_les_fichiers_prevus(tmp_path):
    result = _run("Contact", tmp_path, dry_run=True)
    assert result.dry_run is True
    assert len(result.created) == 13


def test_dry_run_sans_existants_tout_cree(tmp_path):
    result = _run("Contact", tmp_path, dry_run=True)
    assert len(result.preserved) == 0


# ── Bloc de routes ─────────────────────────────────────────────────────────────

def test_bloc_routes_dans_resultat(tmp_path):
    result = _run("Contact", tmp_path)
    assert "router.group" in result.route_block
    assert "ContactController" in result.route_block


def test_new_avant_id_dans_bloc_routes(tmp_path):
    result = _run("Contact", tmp_path)
    pos_new = result.route_block.index("/new")
    pos_id = result.route_block.index("/{id}")
    assert pos_new < pos_id, "/new doit apparaître avant /{id} dans le bloc routes"


def test_toutes_les_routes_presentes(tmp_path):
    result = _run("Contact", tmp_path)
    for expected in ("contact_index", "contact_new", "contact_create",
                     "contact_show", "contact_edit", "contact_update", "contact_destroy"):
        assert expected in result.route_block, f"Route {expected!r} absente du bloc"


# ── Erreurs d'entrée ───────────────────────────────────────────────────────────

def test_entite_absente_exit(tmp_path):
    entities_root = tmp_path / "mvc" / "entities"
    entities_root.mkdir(parents=True)
    with pytest.raises(SystemExit):
        make_crud("Inconnu", entities_root=entities_root, output_root=tmp_path)


def test_json_invalide_exit(tmp_path):
    entities_root = tmp_path / "mvc" / "entities"
    bad_dir = entities_root / "mauvais"
    bad_dir.mkdir(parents=True)
    (bad_dir / "mauvais.json").write_text("{not valid json", encoding="utf-8")
    with pytest.raises(SystemExit):
        make_crud("Mauvais", entities_root=entities_root, output_root=tmp_path)


def test_json_entite_invalide_exit(tmp_path):
    """JSON valide syntaxiquement mais invalide selon la spec Forge."""
    entities_root = tmp_path / "mvc" / "entities"
    bad_dir = entities_root / "erreur"
    bad_dir.mkdir(parents=True)
    (bad_dir / "erreur.json").write_text(
        json.dumps({"entity": "Erreur", "fields": []}),  # fields vide
        encoding="utf-8",
    )
    with pytest.raises(SystemExit):
        make_crud("Erreur", entities_root=entities_root, output_root=tmp_path)


# ── PK exclue du formulaire ────────────────────────────────────────────────────

def test_pk_exclue_du_form_code(tmp_path):
    code, _ = build_form(_CONTACT_JSON)
    # Le champ 'id' (PK) ne doit pas apparaître dans le formulaire
    assert "id = " not in code


def test_pk_exclue_du_form_html(tmp_path):
    html = build_form_view(_CONTACT_JSON)
    # La PK ne doit pas être un champ de saisie dans form.html
    assert 'name="id"' not in html


# ── Champs non-PK dans les fichiers générés ────────────────────────────────────

def test_champs_non_pk_dans_form_html(tmp_path):
    html = build_form_view(_CONTACT_JSON)
    assert 'name="nom"' in html
    assert 'name="email"' in html


def test_champs_non_pk_dans_index_html(tmp_path):
    html = build_table_partial(_CONTACT_JSON)
    assert "Nom" in html
    assert "Email" in html


def test_champs_non_pk_dans_show_html(tmp_path):
    html = build_show_view(_CONTACT_JSON)
    assert "Nom" in html
    assert "Email" in html


# ── Conversion colonnes SQL → champs formulaire ────────────────────────────────

def test_fonction_conversion_dans_controller(tmp_path):
    code = build_controller(_CONTACT_JSON)
    assert "_form_data_from_contact" in code


def test_conversion_utilise_noms_colonnes_sql(tmp_path):
    code = build_controller(_CONTACT_JSON)
    # Les clés du dict retourné utilisent les noms de colonnes SQL (PascalCase)
    assert 'record.get("Nom")' in code
    assert 'record.get("Email")' in code


def test_conversion_utilise_noms_champs_python(tmp_path):
    code = build_controller(_CONTACT_JSON)
    # Les clés du dict retourné utilisent les noms Python (snake_case)
    assert '"nom"' in code
    assert '"email"' in code


def test_edit_utilise_form_data_from(tmp_path):
    code = build_controller(_CONTACT_JSON)
    assert "_form_data_from_contact(contact)" in code


# ── Requêtes SQL paramétrées ───────────────────────────────────────────────────

def test_requetes_sql_parametrees(tmp_path):
    code = build_model(_CONTACT_JSON)
    # Les valeurs ne sont jamais interpolées directement
    assert "?" in code
    assert 'execute(' in code or 'fetch_one(' in code or 'fetch_all(' in code


def test_pas_dinterpolation_directe_sql(tmp_path):
    code = build_model(_CONTACT_JSON)
    # Pas de f-string ou format() sur les SQL avec des valeurs
    assert 'f"INSERT' not in code
    assert 'f"UPDATE' not in code
    assert 'f"DELETE' not in code


# ── Table name et PK depuis le JSON ───────────────────────────────────────────

def test_table_name_depuis_json(tmp_path):
    code = build_model(_CONTACT_JSON)
    assert "FROM contact" in code or "INTO contact" in code


def test_pk_column_dans_where(tmp_path):
    code = build_model(_CONTACT_JSON)
    assert "WHERE Id = ?" in code


def test_pk_exclue_de_insert_si_auto_increment(tmp_path):
    code = build_model(_CONTACT_JSON)
    # La colonne Id (PK auto-incrément) n'apparaît pas dans l'INSERT
    assert "INSERT INTO contact (Nom" in code  # commence par les non-PK
    assert "INSERT INTO contact (Id" not in code


# ── Warn pour types SQL approchés ─────────────────────────────────────────────

def test_pas_de_warn_pour_champ_date(tmp_path):
    _, warnings = build_form(_EVENEMENT_JSON)
    assert len(warnings) == 0


def test_pas_de_warn_dans_resultat_make_crud(tmp_path):
    result = _run("Evenement", tmp_path, data=_EVENEMENT_JSON)
    assert len(result.warnings) == 0


def test_pas_de_warn_pour_varchar_et_int(tmp_path):
    _, warnings = build_form(_CONTACT_JSON)
    assert len(warnings) == 0


# ── Mappage des types SQL → Form field ────────────────────────────────────────

def test_varchar_devient_stringfield(tmp_path):
    code, _ = build_form(_CONTACT_JSON)
    assert "StringField" in code


def test_decimal_devient_decimalfield(tmp_path):
    code, _ = build_form(_PRODUIT_JSON)
    assert "DecimalField" in code


def test_decimal_field_signale_decimal_vs_float(tmp_path):
    _, warnings = build_form(_PRODUIT_JSON)
    assert any("cleaned_data retourne Decimal" in warning for warning in warnings)


def test_text_reste_stringfield(tmp_path):
    code, _ = build_form(_PRODUIT_JSON)
    # TEXT → StringField (avec textarea dans le template)
    assert "StringField" in code


def test_date_devient_datefield(tmp_path):
    code, warnings = build_form(_EVENEMENT_JSON)
    assert "DateField" in code
    assert "StringField" not in code
    assert warnings == []


def test_date_dans_imports(tmp_path):
    from forge_cli.entities.make_crud import _form_imports, _non_pk_fields
    fields = _non_pk_fields(_EVENEMENT_JSON)
    imports = _form_imports(fields)
    assert "DateField" in imports


_LOG_JSON = {
    "format_version": 1, "entity": "Log", "table": "log", "description": "",
    "fields": [
        _field("id",         "INT",      python_type="int",      primary_key=True, auto_increment=True),
        _field("created_at", "DATETIME", python_type="datetime"),
    ],
}


def test_datetime_devient_datetimefield(tmp_path):
    code, warnings = build_form(_LOG_JSON)
    assert "DateTimeField" in code
    assert "StringField" not in code
    assert warnings == []


def test_text_est_textarea_dans_form_html(tmp_path):
    html = build_form_view(_PRODUIT_JSON)
    assert "<textarea" in html


def test_max_length_dans_form_varchar(tmp_path):
    code, _ = build_form(_CONTACT_JSON)
    assert "max_length=100" in code


# ── Layout Jinja2 ──────────────────────────────────────────────────────────────

def test_layout_contient_extends_block(tmp_path):
    layout = build_layout()
    assert "{% block content %}" in layout
    assert "{% endblock %}" in layout


def test_vues_etendent_layout(tmp_path):
    for builder in (build_index_view, build_show_view, build_form_view):
        html = builder(_CONTACT_JSON)
        assert '{% extends "layouts/app.html" %}' in html, (
            f"{builder.__name__} ne contient pas l'extension de layout"
        )


def test_layout_contient_csrf_logout(tmp_path):
    layout = build_layout()
    assert "csrf_token" in layout
    assert "/logout" in layout


def test_vues_utilisent_block_content_coherent_avec_layout(tmp_path):
    block_content = "{% block content %}"
    block_contenu = "{% block contenu %}"
    layout = build_layout()
    assert block_content in layout, "Le layout généré doit déclarer block content"
    assert block_contenu not in layout, "Le layout ne doit pas utiliser l'ancien bloc 'contenu'"
    for builder in (build_index_view, build_show_view, build_form_view):
        html = builder(_CONTACT_JSON)
        assert block_content in html, f"{builder.__name__} doit redéfinir block content"
        assert block_contenu not in html, f"{builder.__name__} ne doit pas utiliser l'ancien bloc 'contenu'"


def test_base_html_utilise_block_content(tmp_path):
    from pathlib import Path
    base = Path(__file__).parent.parent / "mvc" / "views" / "layouts" / "base.html"
    raw = base.read_text()
    assert "{% block content %}" in raw, "base.html doit déclarer block content"
    assert "{% block contenu %}" not in raw, "base.html ne doit plus utiliser l'ancien bloc 'contenu'"


# ── Contenu du controller ──────────────────────────────────────────────────────

def test_controller_importe_flash(tmp_path):
    code = build_controller(_CONTACT_JSON)
    assert "from mvc.helpers.flash import render_flash_html" in code


def test_controller_importe_form(tmp_path):
    code = build_controller(_CONTACT_JSON)
    assert "from mvc.forms.contact_form import ContactForm" in code


def test_controller_importe_model(tmp_path):
    code = build_controller(_CONTACT_JSON)
    assert "from mvc.models.contact_model import" in code


def test_controller_methodes_crud(tmp_path):
    code = build_controller(_CONTACT_JSON)
    for methode in ("def index", "def new", "def create", "def show", "def edit",
                    "def update", "def destroy"):
        assert methode in code, f"Méthode {methode!r} absente du contrôleur"


def test_redirect_with_flash_apres_create(tmp_path):
    code = build_controller(_CONTACT_JSON)
    assert "redirect_with_flash" in code


def test_not_found_si_id_absent(tmp_path):
    code = build_controller(_CONTACT_JSON)
    assert "not_found()" in code


def test_controller_parse_id_invalides(tmp_path):
    code = build_controller(_CONTACT_JSON)
    assert "def _parse_id(value):" in code
    assert "except (TypeError, ValueError):" in code
    assert 'request.route_params.get("id")' in code
    assert 'int(request.route_params["id"])' not in code


def test_controller_verifie_id_invalide_avant_model(tmp_path):
    code = build_controller(_CONTACT_JSON)
    assert "if id is None:" in code
    assert "return BaseController.not_found()" in code


# ── Entité PK-only (aucun champ métier) ───────────────────────────────────────

_PK_ONLY_JSON = {
    "format_version": 1,
    "entity": "Token",
    "table": "token",
    "description": "",
    "fields": [
        _field("id", "INT", python_type="int", primary_key=True, auto_increment=True),
    ],
}


def test_pk_only_model_syntaxiquement_valide():
    """build_model sur PK-only génère du Python sans SyntaxError."""
    import ast
    code = build_model(_PK_ONLY_JSON)
    ast.parse(code)  # lève SyntaxError si le code est invalide


def test_pk_only_update_sql_pas_vide():
    """build_model sur PK-only ne génère pas de SET vide (SQL invalide)."""
    code = build_model(_PK_ONLY_JSON)
    assert "SET  WHERE" not in code


def test_pk_only_update_none():
    """build_model sur PK-only génère UPDATE = None."""
    code = build_model(_PK_ONLY_JSON)
    assert "UPDATE       = None" in code


def test_pk_only_warn_dans_make_crud(tmp_path):
    """make_crud sur entité PK-only émet un [WARN] dans result.warnings."""
    (tmp_path / "mvc" / "entities" / "token").mkdir(parents=True)
    (tmp_path / "mvc" / "entities" / "token" / "token.json").write_text(
        json.dumps({
            "format_version": 1, "entity": "Token", "table": "token",
            "fields": [{"name": "id", "sql_type": "INT",
                        "primary_key": True, "auto_increment": True}],
        }),
        encoding="utf-8",
    )
    result = make_crud(
        "Token",
        entities_root=tmp_path / "mvc" / "entities",
        output_root=tmp_path,
        dry_run=True,
    )
    assert any("champ" in w.lower() for w in result.warnings)


# ── main : BaseController, HTML multiline, bloc routes ──────────────────────

def test_base_controller_importable():
    from core.mvc.controller import BaseController  # noqa: F401


def test_form_html_input_value_et_class_sur_lignes_separees(tmp_path):
    _run("Contact", tmp_path)
    form_html = (tmp_path / "mvc" / "views" / "contact" / "form.html").read_text(encoding="utf-8")
    lines = form_html.splitlines()
    for i, line in enumerate(lines):
        if 'value="' in line and "{{" in line:
            assert "class=" not in line, (
                f"ligne {i+1} : value= et class= sur la même ligne : {line!r}"
            )


def test_form_html_csrf_token_present(tmp_path):
    _run("Contact", tmp_path)
    form_html = (tmp_path / "mvc" / "views" / "contact" / "form.html").read_text(encoding="utf-8")
    assert "csrf_token" in form_html


def test_route_block_commentaire_test_local(tmp_path):
    result = _run("Contact", tmp_path)
    assert "public=True" in result.route_block
    assert "csrf=False" in result.route_block


# ── Pagination ─────────────────────────────────────────────────────────────────

def test_modele_genere_count_function(tmp_path):
    code = build_model(_CONTACT_JSON)
    assert "def count_contacts" in code


def test_modele_genere_find_paginated_function(tmp_path):
    code = build_model(_CONTACT_JSON)
    assert "def find_contacts_paginated" in code


def test_modele_paginated_utilise_limit_offset(tmp_path):
    code = build_model(_CONTACT_JSON)
    assert "LIMIT ? OFFSET ?" in code


def test_controller_index_parse_page(tmp_path):
    code = build_controller(_CONTACT_JSON)
    assert "Pagination(request, total, limit)" in code
    assert "request.query" not in code


def test_controller_index_parse_q(tmp_path):
    code = build_controller(_CONTACT_JSON)
    assert '_query_param(request, "q")' in code


def test_controller_index_parse_sort(tmp_path):
    code = build_controller(_CONTACT_JSON)
    assert '_query_param(request, "sort")' in code


def test_controller_utilise_params_parse_qs_forge(tmp_path):
    code = build_controller(_CONTACT_JSON)
    assert "def _query_param(request, name" in code
    assert "request.params.get(name, [default])" in code


def test_controller_pagination_dans_contexte(tmp_path):
    code = build_controller(_CONTACT_JSON)
    assert '"pagination": pagination' in code


def test_controller_page_invalide_defaut_1(tmp_path):
    code = build_controller(_CONTACT_JSON)
    assert "from core.mvc.view.pagination import Pagination" in code
    assert "Pagination(request, total, limit)" in code


def test_controller_direction_validee(tmp_path):
    code = build_controller(_CONTACT_JSON)
    assert 'direction not in ("asc", "desc")' in code


def test_controller_sort_valide_avant_contexte(tmp_path):
    code = build_controller(_CONTACT_JSON)
    assert 'if sort not in {"nom", "email", "id"}:' in code
    assert 'sort = ""' in code


def test_controller_page_bornee_au_nombre_de_pages(tmp_path):
    code = build_controller(_CONTACT_JSON)
    assert "pagination_state = Pagination(request, total, limit)" in code
    assert code.index("total    = count_contacts") < code.index("pagination_state = Pagination") < code.index("offset = pagination_state.offset")


def test_controller_importe_count_et_paginated(tmp_path):
    code = build_controller(_CONTACT_JSON)
    assert "count_contacts" in code
    assert "find_contacts_paginated" in code


# ── Recherche ──────────────────────────────────────────────────────────────────

def test_search_cols_seulement_champs_texte(tmp_path):
    code = build_model(_PRODUIT_JSON)
    # DECIMAL et INT ne doivent pas être dans _SEARCH_COLS
    assert '"Prix"' not in code.split("_SEARCH_COLS")[1].split("\n")[0]
    assert '"Id"' not in code.split("_SEARCH_COLS")[1].split("\n")[0]


def test_search_cols_inclut_varchar(tmp_path):
    code = build_model(_CONTACT_JSON)
    search_line = [l for l in code.splitlines() if "_SEARCH_COLS" in l][0]
    assert "Nom" in search_line
    assert "Email" in search_line


def test_search_cols_vides_si_aucun_texte(tmp_path):
    """Entité sans champ texte → _SEARCH_COLS = []."""
    D = {
        "format_version": 1, "entity": "Score", "table": "score", "description": "",
        "fields": [
            _field("id",     "INT", python_type="int", primary_key=True, auto_increment=True),
            _field("valeur", "INT", python_type="int"),
        ],
    }
    code = build_model(D)
    search_line = [l for l in code.splitlines() if "_SEARCH_COLS" in l][0]
    assert "[]" in search_line


def test_count_utilise_like_parametrique(tmp_path):
    code = build_model(_CONTACT_JSON)
    assert 'LIKE ?"' in code or "LIKE ?" in code


def test_search_cols_inclut_champ_text(tmp_path):
    """Un champ TEXT doit être inclus dans _SEARCH_COLS."""
    code = build_model(_PRODUIT_JSON)
    search_line = [l for l in code.splitlines() if "_SEARCH_COLS" in l][0]
    assert "Description" in search_line


def test_search_cols_exclut_champ_int_non_pk(tmp_path):
    """Un champ INT non-PK (ex: une FK) ne doit pas être dans _SEARCH_COLS."""
    D = {
        "format_version": 1, "entity": "Commande", "table": "commande", "description": "",
        "fields": [
            _field("id",         "INT",          python_type="int", primary_key=True, auto_increment=True),
            _field("reference",  "VARCHAR(20)",  python_type="str"),
            _field("client_id",  "INT",          python_type="int", nullable=True),
        ],
    }
    code = build_model(D)
    search_line = [l for l in code.splitlines() if "_SEARCH_COLS" in l][0]
    assert "ClientId" not in search_line
    assert "Reference" in search_line


def test_search_cols_exclut_fk_relationnelle(tmp_path):
    """La FK many_to_one (INT) ne doit pas figurer dans _SEARCH_COLS."""
    entities_root = _make_entities(
        tmp_path,
        _CONTACT_WITH_VILLE_JSON,
        _VILLE_JSON,
        relations=_CONTACT_VILLE_RELATIONS_JSON,
    )
    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)
    code = (tmp_path / "mvc" / "models" / "contact_model.py").read_text(encoding="utf-8")
    search_line = [l for l in code.splitlines() if "_SEARCH_COLS" in l][0]
    assert "VilleId" not in search_line


def test_controller_per_page_est_20(tmp_path):
    """Le per_page fixe doit valoir 20 dans le controller généré."""
    code = build_controller(_CONTACT_JSON)
    assert "limit  = 20" in code


def test_controller_sans_q_comportement_actuel(tmp_path):
    """Sans paramètre q, on appelle find_paginated avec q=None."""
    code = build_controller(_CONTACT_JSON)
    assert "q=q or None" in code


def test_index_html_valeur_q_conservee(tmp_path):
    """L'input q doit avoir value="{{ pagination.q }}" pour conserver la recherche."""
    html = build_index_view(_CONTACT_JSON)
    assert 'value="{{ pagination.q }}"' in html


def test_index_html_formulaire_methode_get(tmp_path):
    """Le formulaire de recherche doit utiliser method=get."""
    html = build_index_view(_CONTACT_JSON)
    assert 'method="get"' in html


def test_index_html_has_prev_avec_q(tmp_path):
    """Le lien précédent doit conserver q."""
    html = build_pagination_partial(_CONTACT_JSON)
    assert "has_prev" in html
    assert "pagination.q | urlencode" in html


def test_index_html_has_next_avec_q(tmp_path):
    """Le lien suivant doit conserver q."""
    html = build_pagination_partial(_CONTACT_JSON)
    assert "has_next" in html
    assert "pagination.q | urlencode" in html


# ── Tri ────────────────────────────────────────────────────────────────────────

def test_allowed_sort_contient_champs_entite(tmp_path):
    code = build_model(_CONTACT_JSON)
    sort_line = [l for l in code.splitlines() if "_ALLOWED_SORT" in l][0]
    assert '"nom"' in sort_line
    assert '"email"' in sort_line
    assert '"id"' in sort_line


def test_allowed_sort_ne_contient_pas_champs_arbitraires(tmp_path):
    code = build_model(_CONTACT_JSON)
    sort_line = [l for l in code.splitlines() if "_ALLOWED_SORT" in l][0]
    assert '"ville"' not in sort_line
    assert '"password"' not in sort_line


def test_tri_utilise_whitelist(tmp_path):
    code = build_model(_CONTACT_JSON)
    assert "_ALLOWED_SORT.get(sort, _DEFAULT_SORT)" in code


def test_direction_invalide_ne_devient_pas_desc_par_defaut(tmp_path):
    code = build_model(_CONTACT_JSON)
    assert 'sort_dir = "DESC" if direction == "desc" else "ASC"' in code


# ── Types HTML formulaire ──────────────────────────────────────────────────────

_RESERVATION_JSON = {
    "format_version": 1,
    "entity": "Reservation",
    "table": "reservation",
    "description": "",
    "fields": [
        _field("id",          "INT",          python_type="int",  primary_key=True, auto_increment=True),
        _field("email",       "VARCHAR(120)", python_type="str",  nullable=True),
        _field("telephone",   "VARCHAR(20)",  python_type="str",  nullable=True),
        _field("site_web",    "VARCHAR(200)", python_type="str",  nullable=True),
        _field("date_arrivee","DATE",         python_type="date", nullable=True),
        _field("commentaire", "TEXT",         python_type="str",  nullable=True),
    ],
}


def test_form_html_email_type_email(tmp_path):
    html = build_form_view(_RESERVATION_JSON)
    assert 'type="email"' in html


def test_form_html_telephone_type_tel(tmp_path):
    html = build_form_view(_RESERVATION_JSON)
    assert 'type="tel"' in html


def test_form_html_mobile_type_tel(tmp_path):
    """Le champ 'mobile' doit aussi produire type=tel."""
    from forge_cli.entities.make_crud import _html_input_type
    def _f(name):
        return {"name": name, "column": name.capitalize(), "python_type": "str",
                "sql_type": "VARCHAR(20)", "nullable": True, "primary_key": False,
                "auto_increment": False, "constraints": {}, "unique": False}
    for nom in ("mobile", "gsm", "fax", "tel_fixe", "portable"):
        assert _html_input_type(_f(nom)) == "tel", f"{nom!r} devrait produire type=tel"


def test_form_html_url_type_url(tmp_path):
    html = build_form_view(_RESERVATION_JSON)
    assert 'type="url"' in html


def test_form_html_date_type_date(tmp_path):
    html = build_form_view(_RESERVATION_JSON)
    assert 'type="date"' in html


def test_form_html_text_long_textarea(tmp_path):
    html = build_form_view(_RESERVATION_JSON)
    assert "<textarea" in html


def test_form_html_int_type_number(tmp_path):
    html = build_form_view(_PRODUIT_JSON)
    assert 'type="number"' in html


# ── Relations many_to_one dans le CRUD généré ─────────────────────────────────

def test_many_to_one_genere_relationfield(tmp_path):
    entities_root = _make_entities(
        tmp_path,
        _CONTACT_WITH_VILLE_JSON,
        _VILLE_JSON,
        relations=_CONTACT_VILLE_RELATIONS_JSON,
    )

    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)

    form_code = (tmp_path / "mvc" / "forms" / "contact_form.py").read_text(encoding="utf-8")
    assert "RelationField" in form_code
    assert 'ville_id = RelationField(label="Ville id", target="Ville", required=False, choices_key="ville_id_choices", empty_value=None)' in form_code


def test_many_to_one_genere_select_dans_form_html(tmp_path):
    entities_root = _make_entities(
        tmp_path,
        _CONTACT_WITH_VILLE_JSON,
        _VILLE_JSON,
        relations=_CONTACT_VILLE_RELATIONS_JSON,
    )

    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)

    html = (tmp_path / "mvc" / "views" / "contact" / "form.html").read_text(encoding="utf-8")
    assert "<select" in html
    assert 'name="ville_id"' in html
    assert "form.options.ville_id_choices" in html


def test_many_to_one_controller_passe_les_choix_au_formulaire(tmp_path):
    entities_root = _make_entities(
        tmp_path,
        _CONTACT_WITH_VILLE_JSON,
        _VILLE_JSON,
        relations=_CONTACT_VILLE_RELATIONS_JSON,
    )

    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)

    code = (tmp_path / "mvc" / "controllers" / "contact_controller.py").read_text(encoding="utf-8")
    assert "get_ville_choices" in code
    assert "def _contact_form_options():" in code
    assert '"ville_id_choices": get_ville_choices(),' in code
    assert "ContactForm(**_contact_form_options())" in code
    assert "ContactForm.from_request(request, **_contact_form_options())" in code
    assert "ContactForm(_form_data_from_contact(contact), **_contact_form_options())" in code


def test_many_to_one_controller_passe_options_de_filtre_relationnel_index(tmp_path):
    entities_root = _make_entities(
        tmp_path,
        _CONTACT_WITH_VILLE_JSON,
        _VILLE_JSON,
        relations=_CONTACT_VILLE_RELATIONS_JSON,
    )

    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)

    code = (tmp_path / "mvc" / "controllers" / "contact_controller.py").read_text(encoding="utf-8")
    assert 'relation_filters["ville_id"]' in code
    assert '"options": [{"id": value, "label": label} for value, label in get_ville_choices()]' in code
    assert '"relation_filters": relation_filters' in code


def test_many_to_one_modele_genere_fonction_de_choix(tmp_path):
    entities_root = _make_entities(
        tmp_path,
        _CONTACT_WITH_VILLE_JSON,
        _VILLE_JSON,
        relations=_CONTACT_VILLE_RELATIONS_JSON,
    )

    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)

    code = (tmp_path / "mvc" / "models" / "contact_model.py").read_text(encoding="utf-8")
    assert "def get_ville_choices():" in code
    assert 'fetch_all("SELECT Id, Nom FROM ville ORDER BY Nom")' in code
    assert 'return [(row["Id"], row["Nom"]) for row in rows]' in code


def test_many_to_one_fichiers_python_generes_syntaxiquement_valides(tmp_path):
    import ast

    entities_root = _make_entities(
        tmp_path,
        _CONTACT_WITH_VILLE_JSON,
        _VILLE_JSON,
        relations=_CONTACT_VILLE_RELATIONS_JSON,
    )

    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)

    for path in (
        tmp_path / "mvc" / "forms" / "contact_form.py",
        tmp_path / "mvc" / "models" / "contact_model.py",
        tmp_path / "mvc" / "controllers" / "contact_controller.py",
    ):
        ast.parse(path.read_text(encoding="utf-8"))


def test_many_to_one_label_utilise_premier_champ_texte_non_pk(tmp_path):
    entities_root = _make_entities(
        tmp_path,
        _CONTACT_WITH_VILLE_JSON,
        _VILLE_JSON,
        relations=_CONTACT_VILLE_RELATIONS_JSON,
    )

    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)

    code = (tmp_path / "mvc" / "models" / "contact_model.py").read_text(encoding="utf-8")
    assert "ORDER BY Nom" in code


def test_many_to_one_label_fallback_sur_pk_si_aucun_champ_texte(tmp_path):
    entities_root = _make_entities(
        tmp_path,
        _CONTACT_WITH_VILLE_JSON,
        _VILLE_PK_ONLY_JSON,
        relations=_CONTACT_VILLE_RELATIONS_JSON,
    )

    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)

    code = (tmp_path / "mvc" / "models" / "contact_model.py").read_text(encoding="utf-8")
    assert 'fetch_all("SELECT Id FROM ville ORDER BY Id")' in code
    assert 'return [(row["Id"], row["Id"]) for row in rows]' in code


def test_many_to_one_index_filtre_relationnel_est_select(tmp_path):
    entities_root = _make_entities(
        tmp_path,
        _CONTACT_WITH_VILLE_JSON,
        _VILLE_JSON,
        relations=_CONTACT_VILLE_RELATIONS_JSON,
    )

    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)

    html = (tmp_path / "mvc" / "views" / "contact" / "index.html").read_text(encoding="utf-8")
    assert "<select" in html
    assert 'name="ville_id"' in html
    assert 'type="number"' not in html
    assert "relation_filters.ville_id.options" in html
    assert "pagination.filters.ville_id|string == option.id|string" in html


# ── Vue index enrichie ─────────────────────────────────────────────────────────

def test_index_html_barre_recherche(tmp_path):
    html = build_index_view(_CONTACT_JSON)
    assert 'type="search"' in html
    assert 'name="q"' in html


def test_index_html_liens_tri(tmp_path):
    html = build_table_partial(_CONTACT_JSON)
    assert "sort=nom" in html
    assert "sort=email" in html
    assert "pagination.q | urlencode" in html
    # Le tri réinitialise la page (pas de conservation de page dans les liens de tri)
    assert "pagination.page > 1" not in html.split("?sort=nom")[1].split("</th>")[0]


def test_index_html_pagination(tmp_path):
    html = build_pagination_partial(_CONTACT_JSON)
    assert "pagination.nb_pages" in html
    assert "pagination.page" in html
    assert "has_prev" in html
    assert "has_next" in html
    assert "pagination.sort | urlencode" in html


# ── CRUD-002 : affichage relationnel dans la liste ─────────────────────────────

def test_many_to_one_select_all_contient_left_join(tmp_path):
    entities_root = _make_entities(
        tmp_path,
        _CONTACT_WITH_VILLE_JSON,
        _VILLE_JSON,
        relations=_CONTACT_VILLE_RELATIONS_JSON,
    )
    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)
    code = (tmp_path / "mvc" / "models" / "contact_model.py").read_text(encoding="utf-8")
    assert "LEFT JOIN ville" in code
    assert "SELECT contact.*" in code


def test_many_to_one_select_all_alias_stable(tmp_path):
    entities_root = _make_entities(
        tmp_path,
        _CONTACT_WITH_VILLE_JSON,
        _VILLE_JSON,
        relations=_CONTACT_VILLE_RELATIONS_JSON,
    )
    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)
    code = (tmp_path / "mvc" / "models" / "contact_model.py").read_text(encoding="utf-8")
    assert "ville.Nom AS ville_id_label" in code


def test_many_to_one_find_paginated_base_contient_left_join(tmp_path):
    entities_root = _make_entities(
        tmp_path,
        _CONTACT_WITH_VILLE_JSON,
        _VILLE_JSON,
        relations=_CONTACT_VILLE_RELATIONS_JSON,
    )
    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)
    code = (tmp_path / "mvc" / "models" / "contact_model.py").read_text(encoding="utf-8")
    assert 'base = "SELECT contact.*' in code
    assert "LEFT JOIN ville ON contact.VilleId = ville.Id" in code


def test_many_to_one_colonnes_qualifiees_avec_prefixe_table(tmp_path):
    entities_root = _make_entities(
        tmp_path,
        _CONTACT_WITH_VILLE_JSON,
        _VILLE_JSON,
        relations=_CONTACT_VILLE_RELATIONS_JSON,
    )
    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)
    code = (tmp_path / "mvc" / "models" / "contact_model.py").read_text(encoding="utf-8")
    assert '_DEFAULT_SORT = "contact.Id"' in code
    assert '"nom": "contact.Nom"' in code
    assert '"ville_id": "contact.VilleId"' in code


def test_many_to_one_search_cols_qualifiees(tmp_path):
    entities_root = _make_entities(
        tmp_path,
        _CONTACT_WITH_VILLE_JSON,
        _VILLE_JSON,
        relations=_CONTACT_VILLE_RELATIONS_JSON,
    )
    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)
    code = (tmp_path / "mvc" / "models" / "contact_model.py").read_text(encoding="utf-8")
    assert "'contact.Nom'" in code


def test_many_to_one_index_affiche_label_alias(tmp_path):
    entities_root = _make_entities(
        tmp_path,
        _CONTACT_WITH_VILLE_JSON,
        _VILLE_JSON,
        relations=_CONTACT_VILLE_RELATIONS_JSON,
    )
    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)
    html = (tmp_path / "mvc" / "views" / "contact" / "_table.html").read_text(encoding="utf-8")
    assert "contact.ville_id_label" in html
    assert "contact.VilleId" not in html


def test_many_to_one_index_titre_colonne_est_entite_cible(tmp_path):
    entities_root = _make_entities(
        tmp_path,
        _CONTACT_WITH_VILLE_JSON,
        _VILLE_JSON,
        relations=_CONTACT_VILLE_RELATIONS_JSON,
    )
    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)
    html = (tmp_path / "mvc" / "views" / "contact" / "_table.html").read_text(encoding="utf-8")
    assert '">Ville{%' in html  # label "Ville" suivi du template de tri (pas "Ville id")
    assert "Ville id" not in html


def test_sans_relation_pas_de_left_join(tmp_path):
    entities_root = _make_entity(tmp_path, _CONTACT_JSON)
    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)
    code = (tmp_path / "mvc" / "models" / "contact_model.py").read_text(encoding="utf-8")
    assert "LEFT JOIN" not in code
    assert 'SELECT_ALL   = "SELECT * FROM contact' in code


def test_sans_relation_colonnes_non_qualifiees(tmp_path):
    entities_root = _make_entity(tmp_path, _CONTACT_JSON)
    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)
    code = (tmp_path / "mvc" / "models" / "contact_model.py").read_text(encoding="utf-8")
    assert '_DEFAULT_SORT = "Id"' in code
    assert '"nom": "Nom"' in code


def test_many_to_one_fallback_alias_sur_pk_si_cible_sans_champ_texte(tmp_path):
    entities_root = _make_entities(
        tmp_path,
        _CONTACT_WITH_VILLE_JSON,
        _VILLE_PK_ONLY_JSON,
        relations=_CONTACT_VILLE_RELATIONS_JSON,
    )
    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)
    code = (tmp_path / "mvc" / "models" / "contact_model.py").read_text(encoding="utf-8")
    assert "ville.Id AS ville_id_label" in code


def test_many_to_one_champs_non_relationnels_non_modifies(tmp_path):
    entities_root = _make_entities(
        tmp_path,
        _CONTACT_WITH_VILLE_JSON,
        _VILLE_JSON,
        relations=_CONTACT_VILLE_RELATIONS_JSON,
    )
    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)
    html = (tmp_path / "mvc" / "views" / "contact" / "_table.html").read_text(encoding="utf-8")
    assert "contact.Nom" in html


def test_many_to_one_relation_field_formulaire_inchange(tmp_path):
    entities_root = _make_entities(
        tmp_path,
        _CONTACT_WITH_VILLE_JSON,
        _VILLE_JSON,
        relations=_CONTACT_VILLE_RELATIONS_JSON,
    )
    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)
    form = (tmp_path / "mvc" / "forms" / "contact_form.py").read_text(encoding="utf-8")
    assert "RelationField" in form
    assert 'choices_key="ville_id_choices"' in form


# ── I18N — appels trans() dans les vues générées ──────────────────────────────


def test_index_contient_trans_crud_show():
    html = build_table_partial(_CONTACT_JSON)
    assert "trans('crud.show')" in html


def test_index_contient_trans_crud_edit():
    html = build_table_partial(_CONTACT_JSON)
    assert "trans('crud.edit')" in html


def test_index_contient_trans_crud_delete():
    html = build_table_partial(_CONTACT_JSON)
    assert "trans('crud.delete')" in html


def test_index_contient_trans_crud_empty():
    html = build_table_partial(_CONTACT_JSON)
    assert "trans('crud.empty')" in html


def test_index_contient_trans_common_search():
    html = build_index_view(_CONTACT_JSON)
    assert "trans('common.search')" in html


def test_index_contient_trans_crud_actions():
    html = build_table_partial(_CONTACT_JSON)
    assert "trans('crud.actions')" in html


def test_show_contient_trans_crud_edit():
    html = build_show_view(_CONTACT_JSON)
    assert "trans('crud.edit')" in html


def test_show_contient_trans_crud_delete():
    html = build_show_view(_CONTACT_JSON)
    assert "trans('crud.delete')" in html


def test_show_contient_trans_common_back():
    html = build_show_view(_CONTACT_JSON)
    assert "trans('common.back')" in html


def test_form_contient_trans_common_save():
    html = build_form_view(_CONTACT_JSON)
    assert "trans('common.save')" in html


def test_form_contient_trans_common_cancel():
    html = build_form_view(_CONTACT_JSON)
    assert "trans('common.cancel')" in html


def test_form_contient_trans_common_back():
    html = build_form_view(_CONTACT_JSON)
    assert "trans('common.back')" in html


def test_noms_champs_non_remplaces_par_cles_i18n():
    html = build_form_view(_CONTACT_JSON)
    # Les labels de champs restent humanisés, pas des clés i18n inventées
    assert "Nom" in html
    assert "Email" in html
    assert "trans('contact." not in html
    assert "trans('nom')" not in html
    assert "trans('email')" not in html


def test_aucune_cle_metier_dans_catalogue():
    import json
    from pathlib import Path
    catalog = json.loads(Path("translations/fr.json").read_text(encoding="utf-8"))
    forbidden = ("commune", "sejour", "hébergement", "hebergement", "reservation", "réservation")
    for key in catalog:
        assert not any(term in key.lower() for term in forbidden)


# ---------------------------------------------------------------------------
# TPL-003 — Boutons standardisés
# ---------------------------------------------------------------------------


def test_index_bouton_creer_utilise_composant():
    html = build_index_view(_CONTACT_JSON)
    assert "components/button.html" in html
    assert "variant='primary'" in html


def test_index_bouton_creer_label_entity_specifique():
    html = build_index_view(_CONTACT_JSON)
    assert "Nouveau contact" in html


def test_show_bouton_modifier_utilise_composant():
    html = build_show_view(_CONTACT_JSON)
    assert "components/button.html" in html
    assert "variant='primary'" in html


def test_show_bouton_supprimer_utilise_composant_danger():
    html = build_show_view(_CONTACT_JSON)
    assert "variant='danger'" in html


def test_form_bouton_enregistrer_utilise_composant_primary():
    html = build_form_view(_CONTACT_JSON)
    assert "variant='primary'" in html
    assert "type='submit'" in html


def test_form_bouton_annuler_utilise_composant_secondary():
    html = build_form_view(_CONTACT_JSON)
    assert "variant='secondary'" in html


def test_index_row_supprimer_est_danger_text():
    html = build_table_partial(_CONTACT_JSON)
    assert "text-red-600" in html
    assert "font-medium" in html


def test_boutons_sans_htmx():
    for html in [build_show_view(_CONTACT_JSON), build_form_view(_CONTACT_JSON)]:
        assert "hx-" not in html
        assert "htmx" not in html


def test_boutons_sans_alpine():
    for html in [build_index_view(_CONTACT_JSON), build_show_view(_CONTACT_JSON), build_form_view(_CONTACT_JSON)]:
        assert "x-data" not in html
        assert "alpine" not in html


def test_index_retour_reste_text_link():
    # La page index n'a pas de lien retour — le lien retour est dans show et form
    html = build_show_view(_CONTACT_JSON)
    assert "← {{ trans('common.back') }}" in html
    assert "text-gray-600 hover:underline" in html


def test_form_retour_reste_text_link():
    html = build_form_view(_CONTACT_JSON)
    assert "← {{ trans('common.back') }}" in html
    assert "text-gray-600 hover:underline" in html


# ---------------------------------------------------------------------------
# TPL-005 — États vides CRUD
# ---------------------------------------------------------------------------


def test_index_etat_vide_utilise_div_style():
    html = build_table_partial(_CONTACT_JSON)
    assert "border-dashed" in html
    assert "text-center" in html


def test_index_etat_vide_contient_trans_crud_empty():
    html = build_table_partial(_CONTACT_JSON)
    assert "trans('crud.empty')" in html


def test_index_etat_vide_est_dans_else():
    html = build_table_partial(_CONTACT_JSON)
    empty_div_idx = html.index("border-dashed")
    else_idx = html.rfind("{% else %}", 0, empty_div_idx)
    empty_idx = html.index("trans('crud.empty')")
    endif_idx = html.rfind("{% endif %}")
    assert else_idx < empty_idx < endif_idx


def test_index_etat_vide_sans_p_tag():
    html = build_table_partial(_CONTACT_JSON)
    # L'état vide est désormais un div, pas un <p>
    empty_div_idx = html.index("border-dashed")
    endif_idx = html.rfind("{% endif %}")
    empty_section = html[empty_div_idx:endif_idx]
    assert "<p " not in empty_section


def test_show_sans_etat_vide():
    html = build_show_view(_CONTACT_JSON)
    assert "border-dashed" not in html
    assert "trans('crud.empty')" not in html


def test_form_sans_etat_vide():
    html = build_form_view(_CONTACT_JSON)
    assert "border-dashed" not in html
    assert "trans('crud.empty')" not in html


def test_index_etat_vide_sans_htmx():
    html = build_table_partial(_CONTACT_JSON)
    empty_div_idx = html.index("border-dashed")
    endif_idx = html.rfind("{% endif %}")
    empty_section = html[empty_div_idx:endif_idx]
    assert "hx-" not in empty_section
    assert "htmx" not in empty_section


def test_index_etat_vide_sans_alpine():
    html = build_table_partial(_CONTACT_JSON)
    empty_div_idx = html.index("border-dashed")
    endif_idx = html.rfind("{% endif %}")
    empty_section = html[empty_div_idx:endif_idx]
    assert "x-data" not in empty_section
    assert "alpine" not in empty_section


def test_aucune_nouvelle_cle_metier_i18n_tpl005():
    import json
    from pathlib import Path
    catalog = json.loads(Path("translations/fr.json").read_text(encoding="utf-8"))
    # crud.empty existait déjà avant TPL-005 — aucune nouvelle clé
    assert "crud.empty" in catalog  # clé existante conservée


# --- TPL-006 : confirmation de suppression ---


def test_index_delete_form_contient_onsubmit():
    html = build_table_partial(_CONTACT_JSON)
    assert "onsubmit" in html


def test_index_delete_form_confirm_natif():
    html = build_table_partial(_CONTACT_JSON)
    assert "return confirm(" in html


def test_index_delete_form_confirm_utilise_trans():
    html = build_table_partial(_CONTACT_JSON)
    assert "trans(\"crud.confirm_delete\")" in html


def test_show_delete_form_contient_onsubmit():
    html = build_show_view(_CONTACT_JSON)
    assert "onsubmit" in html


def test_show_delete_form_confirm_natif():
    html = build_show_view(_CONTACT_JSON)
    assert "return confirm(" in html


def test_show_delete_form_confirm_utilise_trans():
    html = build_show_view(_CONTACT_JSON)
    assert "trans(\"crud.confirm_delete\")" in html


def test_form_view_sans_onsubmit_confirm():
    html = build_form_view(_CONTACT_JSON)
    assert "confirm(" not in html


def test_cle_i18n_confirm_delete_dans_catalog():
    import json
    from pathlib import Path
    catalog = json.loads(Path("translations/fr.json").read_text(encoding="utf-8"))
    assert "crud.confirm_delete" in catalog
    assert catalog["crud.confirm_delete"] == "Confirmer la suppression ?"
