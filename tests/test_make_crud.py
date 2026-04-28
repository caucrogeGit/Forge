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
    build_show_view,
    make_crud,
    _route_block,
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
    assert len(result.created) == 7


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
    html = build_index_view(_CONTACT_JSON)
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
    assert 'cursor.execute' in code


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

def test_warn_pour_champ_date(tmp_path):
    _, warnings = build_form(_EVENEMENT_JSON)
    assert len(warnings) == 1
    assert "DATE" in warnings[0]
    assert "StringField" in warnings[0]


def test_warn_dans_resultat_make_crud(tmp_path):
    result = _run("Evenement", tmp_path, data=_EVENEMENT_JSON)
    assert len(result.warnings) == 1
    assert "DATE" in result.warnings[0]


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
    result = _run("Contact", tmp_path)
    form_html = (tmp_path / "mvc" / "views" / "contact" / "form.html").read_text(encoding="utf-8")
    lines = form_html.splitlines()
    for i, line in enumerate(lines):
        if 'value="' in line and "{{" in line:
            assert "class=" not in line, (
                f"ligne {i+1} : value= et class= sur la même ligne : {line!r}"
            )


def test_form_html_csrf_token_present(tmp_path):
    result = _run("Contact", tmp_path)
    form_html = (tmp_path / "mvc" / "views" / "contact" / "form.html").read_text(encoding="utf-8")
    assert "csrf_token" in form_html


def test_route_block_commentaire_test_local(tmp_path):
    result = _run("Contact", tmp_path)
    assert "public=True" in result.route_block
    assert "csrf=False" in result.route_block
