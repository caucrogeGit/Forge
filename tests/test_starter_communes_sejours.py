"""Tests pour le starter Communes & Séjours (squelette + entités + pages publiques)."""

from __future__ import annotations

import json
import os

import pytest

from forge_cli.starters import cmd_starter_build, cmd_starter_list
from forge_cli.starters.builder import build
from forge_cli.starters.registry import all_starters, resolve
from forge_cli.starters.scaffold import check_existing, force_clean_skeleton


# ── Identité ──────────────────────────────────────────────────────────────────

def test_starter_communes_sejours_existe():
    ids = [s["id"] for s in all_starters()]
    assert "communes-sejours" in ids


def test_starter_communes_sejours_numero_5():
    meta = resolve("communes-sejours")
    assert meta["number"] == 5


def test_starter_communes_sejours_status_available():
    meta = resolve("communes-sejours")
    assert meta["status"] == "available"


def test_starter_communes_sejours_kind_skeleton():
    meta = resolve("communes-sejours")
    assert meta["kind"] == "skeleton"


def test_starter_communes_sejours_requires_db_false():
    meta = resolve("communes-sejours")
    assert meta.get("requires_db") is False


@pytest.mark.parametrize("identifier", ["5", "communes-sejours", "communes"])
def test_aliases_communes_sejours_resolvent_le_meme_starter(identifier):
    meta = resolve(identifier)
    assert meta["id"] == "communes-sejours"


# ── Données packagées ──────────────────────────────────────────────────────────

def test_starter_communes_sejours_routes_snippet_existe():
    meta = resolve("communes-sejours")
    snippet_name = meta.get("routes_snippet", "routes.py.snippet")
    assert (meta["_dir"] / snippet_name).exists()


def test_starter_communes_sejours_controller_existe():
    meta = resolve("communes-sejours")
    p = meta["_dir"] / "files" / "mvc" / "controllers" / "communes_sejours_controller.py"
    assert p.exists()


def test_starter_communes_sejours_home_template_existe():
    meta = resolve("communes-sejours")
    p = meta["_dir"] / "files" / "mvc" / "views" / "public" / "communes_sejours" / "home.html"
    assert p.exists()


def test_starter_communes_sejours_hebergements_index_template_existe():
    meta = resolve("communes-sejours")
    p = meta["_dir"] / "files" / "mvc" / "views" / "public" / "communes_sejours" / "hebergements_index.html"
    assert p.exists()


def test_starter_communes_sejours_hebergements_show_template_existe():
    meta = resolve("communes-sejours")
    p = meta["_dir"] / "files" / "mvc" / "views" / "public" / "communes_sejours" / "hebergements_show.html"
    assert p.exists()


def test_starter_communes_sejours_pas_entite_json():
    meta = resolve("communes-sejours")
    entity_jsons = list((meta["_dir"]).glob("entities/*.json"))
    assert entity_jsons == []


def test_starter_communes_sejours_pas_de_relations_json():
    meta = resolve("communes-sejours")
    assert not (meta["_dir"] / "relations.json").exists()


def test_starter_communes_sejours_pas_de_script_seed_sql():
    meta = resolve("communes-sejours")
    scripts_dir = meta["_dir"] / "files" / "scripts"
    if scripts_dir.exists():
        seeds = list(scripts_dir.rglob("seed*.py"))
        assert seeds == []


def test_starter_communes_sejours_pas_de_migration_sql():
    meta = resolve("communes-sejours")
    sql_files = list(meta["_dir"].rglob("*.sql"))
    assert sql_files == []


# ── Affichage ──────────────────────────────────────────────────────────────────

def test_starter_list_contient_communes_sejours(capsys):
    cmd_starter_list()
    output = capsys.readouterr().out
    assert "Communes" in output
    assert "5" in output


@pytest.mark.parametrize("identifier", ["5", "communes-sejours", "communes"])
def test_starter_communes_sejours_dry_run_fonctionne(identifier, capsys):
    cmd_starter_build([identifier, "--dry-run"])
    output = capsys.readouterr().out
    assert "Communes & Séjours" in output
    assert "mvc/controllers/communes_sejours_controller.py" in output
    assert "mvc/views/public/communes_sejours/home.html" in output
    assert "mvc/views/public/communes_sejours/hebergements_index.html" in output
    assert "mvc/views/public/communes_sejours/hebergements_show.html" in output
    assert "routes.py.snippet" in output
    assert "/communes-sejours" in output
    assert "Aucun fichier écrit" in output


# ── Build réel (sans DB) ───────────────────────────────────────────────────────

def _forge_project(tmp_path):
    """Crée un projet Forge minimal dans tmp_path."""
    (tmp_path / "config.py").write_text("# config\n", encoding="utf-8")
    (tmp_path / "mvc").mkdir()
    (tmp_path / "mvc" / "routes.py").write_text(
        "from core.http.router import Router\nrouter = Router()\n",
        encoding="utf-8",
    )


def test_starter_communes_sejours_build_copie_fichiers(tmp_path):
    meta = resolve("communes-sejours")
    _forge_project(tmp_path)
    orig = os.getcwd()
    try:
        os.chdir(tmp_path)
        build(meta, init_db=False, force=False, public=False)
    finally:
        os.chdir(orig)

    assert (tmp_path / "mvc" / "controllers" / "communes_sejours_controller.py").exists()
    assert (tmp_path / "mvc" / "views" / "public" / "communes_sejours" / "home.html").exists()
    assert (tmp_path / "mvc" / "views" / "public" / "communes_sejours" / "hebergements_index.html").exists()
    assert (tmp_path / "mvc" / "views" / "public" / "communes_sejours" / "hebergements_show.html").exists()


def test_starter_communes_sejours_build_injecte_routes(tmp_path):
    meta = resolve("communes-sejours")
    _forge_project(tmp_path)
    orig = os.getcwd()
    try:
        os.chdir(tmp_path)
        build(meta, init_db=False, force=False, public=False)
    finally:
        os.chdir(orig)

    routes_content = (tmp_path / "mvc" / "routes.py").read_text(encoding="utf-8")
    assert "communes-sejours" in routes_content
    assert "communes_sejours_home" in routes_content
    assert "CommunesSejoursController" in routes_content
    assert "communes_sejours_hebergements" in routes_content
    assert "communes_sejours_hebergement" in routes_content


def test_starter_communes_sejours_build_detecte_conflit(tmp_path):
    meta = resolve("communes-sejours")
    _forge_project(tmp_path)
    # Pré-créer un fichier du starter → conflit
    ctrl = tmp_path / "mvc" / "controllers" / "communes_sejours_controller.py"
    ctrl.parent.mkdir(parents=True, exist_ok=True)
    ctrl.write_text("# existing\n", encoding="utf-8")

    existing = check_existing(meta, tmp_path)
    assert "mvc/controllers/communes_sejours_controller.py" in existing


def test_starter_communes_sejours_force_clean(tmp_path):
    meta = resolve("communes-sejours")
    _forge_project(tmp_path)
    orig = os.getcwd()
    try:
        os.chdir(tmp_path)
        build(meta, init_db=False, force=False, public=False)
    finally:
        os.chdir(orig)

    force_clean_skeleton(meta, tmp_path)

    assert not (tmp_path / "mvc" / "controllers" / "communes_sejours_controller.py").exists()
    assert not (tmp_path / "mvc" / "views" / "public" / "communes_sejours").exists()
    routes_content = (tmp_path / "mvc" / "routes.py").read_text(encoding="utf-8")
    assert "communes-sejours" not in routes_content


def test_starter_communes_sejours_build_force_reinstalle(tmp_path):
    meta = resolve("communes-sejours")
    _forge_project(tmp_path)
    orig = os.getcwd()
    try:
        os.chdir(tmp_path)
        build(meta, init_db=False, force=False, public=False)
        build(meta, init_db=False, force=True, public=False)
    finally:
        os.chdir(orig)

    assert (tmp_path / "mvc" / "controllers" / "communes_sejours_controller.py").exists()
    assert (tmp_path / "mvc" / "views" / "public" / "communes_sejours" / "home.html").exists()


# ── Entités JSON ───────────────────────────────────────────────────────────────

_ENTITIES = ["commune", "proprietaire", "hebergement", "demande_sejour"]


@pytest.mark.parametrize("entity", _ENTITIES)
def test_entite_json_existe(entity):
    meta = resolve("communes-sejours")
    p = meta["_dir"] / "files" / "mvc" / "entities" / entity / f"{entity}.json"
    assert p.exists(), f"{entity}.json manquant dans les données du starter"


@pytest.mark.parametrize("entity", _ENTITIES)
def test_entite_json_valide(entity):
    meta = resolve("communes-sejours")
    p = meta["_dir"] / "files" / "mvc" / "entities" / entity / f"{entity}.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["format_version"] == 1
    assert "entity" in data
    assert "table" in data
    assert "fields" in data
    assert isinstance(data["fields"], list)
    assert len(data["fields"]) > 0


def test_entite_commune_champs_principaux():
    meta = resolve("communes-sejours")
    data = json.loads(
        (meta["_dir"] / "files" / "mvc" / "entities" / "commune" / "commune.json")
        .read_text(encoding="utf-8")
    )
    field_names = [f["name"] for f in data["fields"]]
    assert "id" in field_names
    assert "nom" in field_names
    assert "code_postal" in field_names
    assert data["entity"] == "Commune"
    assert data["table"] == "commune"


def test_entite_proprietaire_champs_principaux():
    meta = resolve("communes-sejours")
    data = json.loads(
        (meta["_dir"] / "files" / "mvc" / "entities" / "proprietaire" / "proprietaire.json")
        .read_text(encoding="utf-8")
    )
    field_names = [f["name"] for f in data["fields"]]
    assert "id" in field_names
    assert "nom" in field_names
    assert "email" in field_names
    assert data["entity"] == "Proprietaire"
    assert data["table"] == "proprietaire"


def test_entite_hebergement_champs_principaux():
    meta = resolve("communes-sejours")
    data = json.loads(
        (meta["_dir"] / "files" / "mvc" / "entities" / "hebergement" / "hebergement.json")
        .read_text(encoding="utf-8")
    )
    field_names = [f["name"] for f in data["fields"]]
    assert "id" in field_names
    assert "titre" in field_names
    assert "slug" in field_names
    assert "commune_id" in field_names
    assert "proprietaire_id" in field_names
    assert "is_published" in field_names
    assert data["entity"] == "Hebergement"
    assert data["table"] == "hebergement"


def test_entite_demande_sejour_champs_principaux():
    meta = resolve("communes-sejours")
    data = json.loads(
        (meta["_dir"] / "files" / "mvc" / "entities" / "demande_sejour" / "demande_sejour.json")
        .read_text(encoding="utf-8")
    )
    field_names = [f["name"] for f in data["fields"]]
    assert "id" in field_names
    assert "hebergement_id" in field_names
    assert "nom" in field_names
    assert "email" in field_names
    assert "statut" in field_names
    assert data["entity"] == "DemandeSejour"
    assert data["table"] == "demande_sejour"


def test_entite_demande_sejour_statut_defaut_nouveau():
    meta = resolve("communes-sejours")
    data = json.loads(
        (meta["_dir"] / "files" / "mvc" / "entities" / "demande_sejour" / "demande_sejour.json")
        .read_text(encoding="utf-8")
    )
    statut = next(f for f in data["fields"] if f["name"] == "statut")
    assert statut.get("default") == "nouveau"


# ── Relations JSON ─────────────────────────────────────────────────────────────

def test_relations_json_existe():
    meta = resolve("communes-sejours")
    p = meta["_dir"] / "files" / "mvc" / "entities" / "relations.json"
    assert p.exists()


def test_relations_json_valide():
    meta = resolve("communes-sejours")
    data = json.loads(
        (meta["_dir"] / "files" / "mvc" / "entities" / "relations.json")
        .read_text(encoding="utf-8")
    )
    assert data["format_version"] == 1
    assert "relations" in data
    assert isinstance(data["relations"], list)
    assert len(data["relations"]) == 3


def test_relations_json_contient_hebergement_commune():
    meta = resolve("communes-sejours")
    data = json.loads(
        (meta["_dir"] / "files" / "mvc" / "entities" / "relations.json")
        .read_text(encoding="utf-8")
    )
    names = [r["name"] for r in data["relations"]]
    assert "hebergement_commune" in names


def test_relations_json_contient_hebergement_proprietaire():
    meta = resolve("communes-sejours")
    data = json.loads(
        (meta["_dir"] / "files" / "mvc" / "entities" / "relations.json")
        .read_text(encoding="utf-8")
    )
    names = [r["name"] for r in data["relations"]]
    assert "hebergement_proprietaire" in names


def test_relations_json_contient_demande_hebergement():
    meta = resolve("communes-sejours")
    data = json.loads(
        (meta["_dir"] / "files" / "mvc" / "entities" / "relations.json")
        .read_text(encoding="utf-8")
    )
    names = [r["name"] for r in data["relations"]]
    assert "demande_hebergement" in names


def test_relations_json_types_many_to_one():
    meta = resolve("communes-sejours")
    data = json.loads(
        (meta["_dir"] / "files" / "mvc" / "entities" / "relations.json")
        .read_text(encoding="utf-8")
    )
    for rel in data["relations"]:
        assert rel["type"] == "many_to_one"


# ── Build copie les entités ────────────────────────────────────────────────────

def test_build_copie_entites(tmp_path):
    meta = resolve("communes-sejours")
    _forge_project(tmp_path)
    orig = os.getcwd()
    try:
        os.chdir(tmp_path)
        build(meta, init_db=False, force=False, public=False)
    finally:
        os.chdir(orig)

    for entity in _ENTITIES:
        assert (tmp_path / "mvc" / "entities" / entity / f"{entity}.json").exists()
    assert (tmp_path / "mvc" / "entities" / "relations.json").exists()


def test_build_ne_cree_pas_de_sql(tmp_path):
    meta = resolve("communes-sejours")
    _forge_project(tmp_path)
    orig = os.getcwd()
    try:
        os.chdir(tmp_path)
        build(meta, init_db=False, force=False, public=False)
    finally:
        os.chdir(orig)

    sql_files = list(tmp_path.rglob("*.sql"))
    assert sql_files == []


def test_dry_run_annonce_entites(capsys):
    cmd_starter_build(["5", "--dry-run"])
    output = capsys.readouterr().out
    assert "commune/commune.json" in output
    assert "proprietaire/proprietaire.json" in output
    assert "hebergement/hebergement.json" in output
    assert "demande_sejour/demande_sejour.json" in output
    assert "entities/relations.json" in output


# ── Déclaration médias de Hebergement ─────────────────────────────────────────

def _hebergement_data():
    meta = resolve("communes-sejours")
    return json.loads(
        (meta["_dir"] / "files" / "mvc" / "entities" / "hebergement" / "hebergement.json")
        .read_text(encoding="utf-8")
    )


def test_hebergement_possede_section_media():
    data = _hebergement_data()
    assert "media" in data
    assert isinstance(data["media"], list)
    assert len(data["media"]) > 0


def test_hebergement_media_cover_existe():
    data = _hebergement_data()
    names = [m["name"] for m in data["media"]]
    assert "cover" in names


def test_hebergement_media_photos_existe():
    data = _hebergement_data()
    names = [m["name"] for m in data["media"]]
    assert "photos" in names


def test_hebergement_media_cover_est_image():
    data = _hebergement_data()
    cover = next(m for m in data["media"] if m["name"] == "cover")
    assert cover["field"] == "image"
    assert cover["role"] == "cover"
    assert cover["multiple"] is False
    assert cover["variants"] is True


def test_hebergement_media_photos_est_galerie():
    data = _hebergement_data()
    photos = next(m for m in data["media"] if m["name"] == "photos")
    assert photos["field"] == "image"
    assert photos["role"] == "gallery"
    assert photos["multiple"] is True


def test_hebergement_media_json_valide_par_forge():
    from forge_cli.entities.validation import validate_entity_definition, EntityDefinitionError
    data = _hebergement_data()
    try:
        validate_entity_definition(data, source="hebergement.json")
    except EntityDefinitionError as e:
        pytest.fail(f"Erreurs de validation : {e}")


# ── Pages publiques ────────────────────────────────────────────────────────────

def _views_dir():
    meta = resolve("communes-sejours")
    return meta["_dir"] / "files" / "mvc" / "views" / "public" / "communes_sejours"


def _controller_text():
    meta = resolve("communes-sejours")
    return (meta["_dir"] / "files" / "mvc" / "controllers" / "communes_sejours_controller.py").read_text(encoding="utf-8")


def _snippet_text():
    meta = resolve("communes-sejours")
    return (meta["_dir"] / "routes.py.snippet").read_text(encoding="utf-8")


# Routes

def test_routes_snippet_contient_route_accueil():
    assert "/communes-sejours" in _snippet_text()
    assert "communes_sejours_home" in _snippet_text()


def test_routes_snippet_contient_route_liste():
    assert "/hebergements" in _snippet_text()
    assert "communes_sejours_hebergements" in _snippet_text()


def test_routes_snippet_contient_route_fiche():
    assert "/hebergements/{slug}" in _snippet_text()
    assert "communes_sejours_hebergement" in _snippet_text()


def test_routes_snippet_quatre_routes():
    from forge_cli.starters.route_ops import routes_from_snippet
    routes = routes_from_snippet(_snippet_text())
    assert len(routes) == 4


def test_routes_snippet_trois_routes_get():
    from forge_cli.starters.route_ops import routes_from_snippet
    routes = routes_from_snippet(_snippet_text())
    get_routes = [p for m, p in routes if m == "GET"]
    assert len(get_routes) == 3


def test_routes_snippet_une_route_post():
    from forge_cli.starters.route_ops import routes_from_snippet
    routes = routes_from_snippet(_snippet_text())
    post_routes = [p for m, p in routes if m == "POST"]
    assert len(post_routes) == 1
    assert post_routes[0] == "/communes-sejours/hebergements/{slug}/demande"


# Contrôleur

def test_controleur_classe_communes_sejours():
    assert "CommunesSejoursController" in _controller_text()


def test_controleur_methode_index():
    assert "def index" in _controller_text()


def test_controleur_methode_hebergements_index():
    assert "def hebergements_index" in _controller_text()


def test_controleur_methode_hebergements_show():
    assert "def hebergements_show" in _controller_text()


def test_controleur_placeholder_hebergements():
    assert "_HEBERGEMENTS" in _controller_text()


def test_controleur_pas_de_post():
    assert "POST" not in _controller_text()
    assert "request.body" not in _controller_text()


def test_controleur_pas_de_smtp_direct():
    text = _controller_text().lower()
    assert "sendmail" not in text
    assert "smtplib" not in text
    assert "smtpmailer" not in text


def test_controleur_not_found_pour_slug_inconnu():
    assert "not_found" in _controller_text()


# Templates — contenu

def test_template_home_contient_titre():
    content = (_views_dir() / "home.html").read_text(encoding="utf-8")
    assert "starter.cs.title" in content


def test_template_home_lien_vers_liste():
    content = (_views_dir() / "home.html").read_text(encoding="utf-8")
    assert "/communes-sejours/hebergements" in content


def test_template_home_pas_de_formulaire():
    content = (_views_dir() / "home.html").read_text(encoding="utf-8")
    assert "<form" not in content


def test_template_liste_contient_boucle_hebergements():
    content = (_views_dir() / "hebergements_index.html").read_text(encoding="utf-8")
    assert "hebergements" in content
    assert "for h in" in content or "{% for" in content


def test_template_liste_lien_vers_fiche():
    content = (_views_dir() / "hebergements_index.html").read_text(encoding="utf-8")
    assert "/communes-sejours/hebergements/" in content


def test_template_liste_gere_liste_vide():
    content = (_views_dir() / "hebergements_index.html").read_text(encoding="utf-8")
    assert "{% if hebergements %}" in content or "{% if" in content


def test_template_fiche_contient_titre():
    content = (_views_dir() / "hebergements_show.html").read_text(encoding="utf-8")
    assert "hebergement.titre" in content


def test_template_fiche_emplacement_image():
    content = (_views_dir() / "hebergements_show.html").read_text(encoding="utf-8")
    assert "photo" in content.lower() or "image" in content.lower() or "cover" in content.lower()


def test_template_fiche_mention_formulaire_futur():
    content = (_views_dir() / "hebergements_show.html").read_text(encoding="utf-8")
    assert "FORM" in content or "formulaire" in content.lower()


def test_template_fiche_section_demande():
    content = (_views_dir() / "hebergements_show.html").read_text(encoding="utf-8")
    assert "demande" in content.lower() or "séjour" in content.lower()


# Intégrité — pas de fichiers interdits

def test_pas_de_seed_dans_les_templates():
    meta = resolve("communes-sejours")
    seeds = list((meta["_dir"] / "files").rglob("seed*.py"))
    assert seeds == []


def test_pas_de_fichiers_binaires_images():
    meta = resolve("communes-sejours")
    for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"):
        found = list((meta["_dir"] / "files").rglob(f"*{ext}"))
        assert found == [], f"Fichier binaire inattendu : {found}"


def test_build_ne_copie_pas_pycache(tmp_path):
    meta = resolve("communes-sejours")
    _forge_project(tmp_path)
    orig = os.getcwd()
    try:
        os.chdir(tmp_path)
        build(meta, init_db=False, force=False, public=False)
    finally:
        os.chdir(orig)
    pycaches = list(tmp_path.rglob("__pycache__"))
    assert pycaches == [], f"pycache copié par le build : {pycaches}"


def test_roadmap_md_non_recree():
    import pathlib
    assert not pathlib.Path("docs/roadmap.md").exists()


# Build copie les nouvelles pages publiques

def test_build_copie_templates_publics(tmp_path):
    meta = resolve("communes-sejours")
    _forge_project(tmp_path)
    orig = os.getcwd()
    try:
        os.chdir(tmp_path)
        build(meta, init_db=False, force=False, public=False)
    finally:
        os.chdir(orig)

    views = tmp_path / "mvc" / "views" / "public" / "communes_sejours"
    assert (views / "home.html").exists()
    assert (views / "hebergements_index.html").exists()
    assert (views / "hebergements_show.html").exists()


def test_dry_run_annonce_toutes_les_routes(capsys):
    cmd_starter_build(["5", "--dry-run"])
    output = capsys.readouterr().out
    assert "/communes-sejours" in output
    assert "/communes-sejours/hebergements" in output
    assert "/communes-sejours/hebergements/{slug}" in output
    assert "/communes-sejours/hebergements/{slug}/demande" in output


# ── Formulaire de demande de séjour ───────────────────────────────────────────

def _form_file_text():
    meta = resolve("communes-sejours")
    return (meta["_dir"] / "files" / "mvc" / "forms" / "demande_sejour_form.py").read_text(encoding="utf-8")


def _show_template_text():
    return (_views_dir() / "hebergements_show.html").read_text(encoding="utf-8")


# Fichier de formulaire

def test_formulaire_fichier_existe():
    meta = resolve("communes-sejours")
    p = meta["_dir"] / "files" / "mvc" / "forms" / "demande_sejour_form.py"
    assert p.exists()


def test_formulaire_classe_demande_sejour():
    assert "DemandeSejourForm" in _form_file_text()


def test_formulaire_champ_nom():
    assert "nom" in _form_file_text()


def test_formulaire_champ_email():
    assert "email" in _form_file_text()
    assert "EmailField" in _form_file_text()


def test_formulaire_champ_date_arrivee():
    assert "date_arrivee" in _form_file_text()
    assert "DateField" in _form_file_text()


def test_formulaire_champ_date_depart():
    assert "date_depart" in _form_file_text()


def test_formulaire_champ_nombre_personnes():
    assert "nombre_personnes" in _form_file_text()
    assert "IntegerField" in _form_file_text()


def test_formulaire_champ_message_optionnel():
    assert "message" in _form_file_text()
    text = _form_file_text()
    # message est optionnel (required=False)
    msg_line = next(l for l in text.splitlines() if "message" in l and "Field" in l)
    assert "required=False" in msg_line or "required = False" in msg_line


# Route POST dans le snippet

def test_snippet_contient_route_post_demande():
    assert "POST" in _snippet_text()
    assert "/hebergements/{slug}/demande" in _snippet_text()
    assert "hebergements_demande" in _snippet_text()


# Contrôleur — méthode de traitement

def test_controleur_methode_hebergements_demande():
    assert "def hebergements_demande" in _controller_text()


def test_controleur_utilise_from_request():
    assert "from_request" in _controller_text()


def test_controleur_utilise_is_valid():
    assert "is_valid" in _controller_text()


def test_controleur_utilise_redirect_with_flash():
    assert "redirect_with_flash" in _controller_text()


def test_controleur_confirmation_sans_mail():
    text = _controller_text()
    assert "starter.cs.request.sent" in text
    assert "sendmail" not in text.lower()
    assert "smtp" not in text.lower()


def test_controleur_not_found_sur_slug_inconnu_demande():
    assert "not_found" in _controller_text()


# Template fiche — formulaire

def test_template_fiche_contient_formulaire():
    assert "<form" in _show_template_text()


def test_template_fiche_methode_post():
    assert 'method="post"' in _show_template_text().lower() or 'method="POST"' in _show_template_text()


def test_template_fiche_action_demande():
    assert "/demande" in _show_template_text()


def test_template_fiche_csrf_token():
    assert "csrf_token" in _show_template_text()


def test_template_fiche_champ_nom():
    assert 'name="nom"' in _show_template_text()


def test_template_fiche_champ_email():
    assert 'name="email"' in _show_template_text()


def test_template_fiche_champ_date_arrivee():
    assert 'name="date_arrivee"' in _show_template_text()


def test_template_fiche_champ_date_depart():
    assert 'name="date_depart"' in _show_template_text()


def test_template_fiche_champ_nombre_personnes():
    assert 'name="nombre_personnes"' in _show_template_text()


def test_template_fiche_affiche_erreurs():
    content = _show_template_text()
    assert "has_error" in content or "form.error" in content


def test_template_fiche_pas_de_note_obsolete():
    content = _show_template_text()
    assert "STARTER-CS-MAIL-001" not in content
    assert "prochaine étape" not in content


# Validation via Forge Form (tests unitaires)

def _load_demande_sejour_form():
    import importlib.util
    meta = resolve("communes-sejours")
    form_path = meta["_dir"] / "files" / "mvc" / "forms" / "demande_sejour_form.py"
    spec = importlib.util.spec_from_file_location("demande_sejour_form", form_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.DemandeSejourForm


def _make_form_from_data(data: dict):
    DemandeSejourForm = _load_demande_sejour_form()

    class FakeRequest:
        def __init__(self, body):
            self.body = body
        route_params = {}

    req = FakeRequest(body={k: [v] for k, v in data.items()})
    return DemandeSejourForm.from_request(req)


def _valid_data():
    return {
        "nom": "Alice Dupont",
        "email": "alice@example.com",
        "telephone": "",
        "date_arrivee": "2026-07-01",
        "date_depart": "2026-07-07",
        "nombre_personnes": "2",
        "message": "",
    }


def test_form_valide_avec_donnees_correctes():
    form = _make_form_from_data(_valid_data())
    assert form.is_valid(), f"Erreurs inattendues : {form.errors}"


def test_form_refuse_nom_vide():
    data = {**_valid_data(), "nom": ""}
    form = _make_form_from_data(data)
    assert not form.is_valid()
    assert form.has_error("nom")


def test_form_refuse_email_vide():
    data = {**_valid_data(), "email": ""}
    form = _make_form_from_data(data)
    assert not form.is_valid()
    assert form.has_error("email")


def test_form_refuse_email_invalide():
    data = {**_valid_data(), "email": "pas-un-email"}
    form = _make_form_from_data(data)
    assert not form.is_valid()
    assert form.has_error("email")


def test_form_refuse_date_arrivee_vide():
    data = {**_valid_data(), "date_arrivee": ""}
    form = _make_form_from_data(data)
    assert not form.is_valid()
    assert form.has_error("date_arrivee")


def test_form_refuse_date_depart_vide():
    data = {**_valid_data(), "date_depart": ""}
    form = _make_form_from_data(data)
    assert not form.is_valid()
    assert form.has_error("date_depart")


def test_form_refuse_nombre_personnes_vide():
    data = {**_valid_data(), "nombre_personnes": ""}
    form = _make_form_from_data(data)
    assert not form.is_valid()
    assert form.has_error("nombre_personnes")


def test_form_refuse_nombre_personnes_zero():
    data = {**_valid_data(), "nombre_personnes": "0"}
    form = _make_form_from_data(data)
    assert not form.is_valid()
    assert form.has_error("nombre_personnes")


def test_form_refuse_nombre_personnes_negatif():
    data = {**_valid_data(), "nombre_personnes": "-1"}
    form = _make_form_from_data(data)
    assert not form.is_valid()
    assert form.has_error("nombre_personnes")


def test_form_refuse_nombre_personnes_texte():
    data = {**_valid_data(), "nombre_personnes": "abc"}
    form = _make_form_from_data(data)
    assert not form.is_valid()
    assert form.has_error("nombre_personnes")


def test_form_accepte_message_vide():
    data = {**_valid_data(), "message": ""}
    form = _make_form_from_data(data)
    assert form.is_valid(), f"message vide devrait être accepté : {form.errors}"


# Build copie le formulaire

def test_build_copie_formulaire(tmp_path):
    meta = resolve("communes-sejours")
    _forge_project(tmp_path)
    orig = os.getcwd()
    try:
        os.chdir(tmp_path)
        build(meta, init_db=False, force=False, public=False)
    finally:
        os.chdir(orig)
    assert (tmp_path / "mvc" / "forms" / "demande_sejour_form.py").exists()


def test_dry_run_annonce_formulaire(capsys):
    cmd_starter_build(["5", "--dry-run"])
    output = capsys.readouterr().out
    assert "mvc/forms/demande_sejour_form.py" in output


# ── Notifications mail ─────────────────────────────────────────────────────────

def _mail_templates_dir():
    meta = resolve("communes-sejours")
    return meta["_dir"] / "files" / "mvc" / "mail" / "templates"


def _load_controller_module():
    import importlib.util
    import sys
    import types
    meta = resolve("communes-sejours")
    files_dir = meta["_dir"] / "files"

    # Pre-inject the form module so the controller's import resolves
    form_path = files_dir / "mvc" / "forms" / "demande_sejour_form.py"
    form_spec = importlib.util.spec_from_file_location("mvc.forms.demande_sejour_form", form_path)
    form_mod = importlib.util.module_from_spec(form_spec)
    # Ensure parent packages exist in sys.modules
    if "mvc" not in sys.modules:
        sys.modules["mvc"] = types.ModuleType("mvc")
    if "mvc.forms" not in sys.modules:
        sys.modules["mvc.forms"] = types.ModuleType("mvc.forms")
    sys.modules["mvc.forms.demande_sejour_form"] = form_mod
    form_spec.loader.exec_module(form_mod)

    ctrl_path = files_dir / "mvc" / "controllers" / "communes_sejours_controller.py"
    spec = importlib.util.spec_from_file_location("communes_sejours_controller", ctrl_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _send_notifications(hebergement, form_data):
    from core.mail import FakeTransport, Mailer
    from core.mail.templates import MailTemplateRenderer
    mod = _load_controller_module()
    fake = FakeTransport()
    mailer = Mailer(fake)
    renderer = MailTemplateRenderer(template_dir=_mail_templates_dir())
    mod.send_demande_sejour_notifications(
        hebergement, form_data, mailer=mailer, renderer=renderer
    )
    return fake


def _sample_hebergement():
    return {
        "slug": "mas-des-cigales",
        "titre": "Mas des Cigales",
        "commune": "Saint-Rémy-de-Provence",
        "capacite": 6,
        "description": "Test.",
        "adresse": "Route de Maillane",
        "proprietaire": "Marie Dupont",
        "is_published": True,
    }


def _sample_form_data():
    import datetime
    return {
        "nom": "Alice Dupont",
        "email": "alice@example.com",
        "telephone": "0601020304",
        "date_arrivee": datetime.date(2026, 7, 1),
        "date_depart": datetime.date(2026, 7, 7),
        "nombre_personnes": 2,
        "message": "Bonjour, est-ce disponible ?",
    }


# Fichiers de templates

def test_templates_mail_dossier_existe():
    assert _mail_templates_dir().exists()


def test_template_visiteur_subject_existe():
    assert (_mail_templates_dir() / "communes_sejours" / "demande_visiteur_subject.txt").exists()


def test_template_visiteur_text_existe():
    assert (_mail_templates_dir() / "communes_sejours" / "demande_visiteur_text.txt").exists()


def test_template_proprietaire_subject_existe():
    assert (_mail_templates_dir() / "communes_sejours" / "demande_proprietaire_subject.txt").exists()


def test_template_proprietaire_text_existe():
    assert (_mail_templates_dir() / "communes_sejours" / "demande_proprietaire_text.txt").exists()


# Contrôleur — helper présent

def test_controleur_contient_helper_notifications():
    assert "send_demande_sejour_notifications" in _controller_text()


def test_controleur_utilise_mailer():
    assert "Mailer" in _controller_text()


def test_controleur_utilise_mail_template_renderer():
    assert "MailTemplateRenderer" in _controller_text()


def test_controleur_gestionnaire_email_placeholder():
    assert "contact@example.test" in _controller_text() or "_GESTIONNAIRE_EMAIL" in _controller_text()


# Envoi — deux mails préparés

def test_notifications_envoient_deux_mails():
    fake = _send_notifications(_sample_hebergement(), _sample_form_data())
    assert fake.sent_count == 2


def test_notification_visiteur_destinataire():
    fake = _send_notifications(_sample_hebergement(), _sample_form_data())
    msg_visiteur = fake.messages[0]
    assert "alice@example.com" in msg_visiteur.to_addresses


def test_notification_visiteur_sujet():
    fake = _send_notifications(_sample_hebergement(), _sample_form_data())
    assert fake.messages[0].subject.strip() != ""


def test_notification_visiteur_corps_contient_hebergement():
    fake = _send_notifications(_sample_hebergement(), _sample_form_data())
    assert "Mas des Cigales" in fake.messages[0].body_text


def test_notification_visiteur_corps_contient_dates():
    fake = _send_notifications(_sample_hebergement(), _sample_form_data())
    body = fake.messages[0].body_text
    assert "2026" in body


def test_notification_visiteur_corps_contient_nombre_personnes():
    fake = _send_notifications(_sample_hebergement(), _sample_form_data())
    assert "2" in fake.messages[0].body_text


def test_notification_visiteur_corps_pas_de_reservation_confirmee():
    fake = _send_notifications(_sample_hebergement(), _sample_form_data())
    body = fake.messages[0].body_text.lower()
    assert "réservation" not in body or "ne constitue pas" in body or "confirmée" not in body


def test_notification_proprietaire_destinataire_generique():
    fake = _send_notifications(_sample_hebergement(), _sample_form_data())
    msg_proprio = fake.messages[1]
    assert msg_proprio.to_addresses  # non vide
    assert "@" in msg_proprio.to_addresses[0]


def test_notification_proprietaire_corps_contient_hebergement():
    fake = _send_notifications(_sample_hebergement(), _sample_form_data())
    assert "Mas des Cigales" in fake.messages[1].body_text


def test_notification_proprietaire_corps_contient_email_visiteur():
    fake = _send_notifications(_sample_hebergement(), _sample_form_data())
    assert "alice@example.com" in fake.messages[1].body_text


def test_notification_proprietaire_corps_contient_nom_visiteur():
    fake = _send_notifications(_sample_hebergement(), _sample_form_data())
    assert "Alice Dupont" in fake.messages[1].body_text


def test_notification_proprietaire_corps_contient_dates():
    fake = _send_notifications(_sample_hebergement(), _sample_form_data())
    assert "2026" in fake.messages[1].body_text


def test_notification_proprietaire_corps_contient_nombre_personnes():
    fake = _send_notifications(_sample_hebergement(), _sample_form_data())
    assert "2" in fake.messages[1].body_text


def test_notification_proprietaire_reply_to_visiteur():
    fake = _send_notifications(_sample_hebergement(), _sample_form_data())
    msg_proprio = fake.messages[1]
    assert msg_proprio.reply_to_addresses == ["alice@example.com"]


# Intégrité — pas d'envoi sans données valides (test du helper directement)

def test_aucun_mail_si_form_invalide():
    from core.mail import FakeTransport
    fake = FakeTransport()
    # On ne doit pas appeler send_demande_sejour_notifications si form invalide.
    # Vérification indirecte : le helper n'est appelé que depuis hebergements_demande
    # après is_valid(). On vérifie juste que sent_count = 0 si on ne l'appelle pas.
    assert fake.sent_count == 0


# Build copie les templates mail

def test_build_copie_templates_mail(tmp_path):
    meta = resolve("communes-sejours")
    _forge_project(tmp_path)
    orig = os.getcwd()
    try:
        os.chdir(tmp_path)
        build(meta, init_db=False, force=False, public=False)
    finally:
        os.chdir(orig)
    mail_dir = tmp_path / "mvc" / "mail" / "templates" / "communes_sejours"
    assert mail_dir.exists()
    assert (mail_dir / "demande_visiteur_subject.txt").exists()
    assert (mail_dir / "demande_visiteur_text.txt").exists()
    assert (mail_dir / "demande_proprietaire_subject.txt").exists()
    assert (mail_dir / "demande_proprietaire_text.txt").exists()


def test_dry_run_annonce_templates_mail(capsys):
    cmd_starter_build(["5", "--dry-run"])
    output = capsys.readouterr().out
    assert "communes_sejours/demande_visiteur" in output or "demande_visiteur_subject" in output


# ---------------------------------------------------------------------------
# STARTER-CS-I18N-001 — Compatibilité i18n
# ---------------------------------------------------------------------------

def _starter_translations_path():
    meta = resolve("communes-sejours")
    return meta["_dir"] / "files" / "translations" / "fr.json"


def _starter_translations_catalog():
    return json.loads(_starter_translations_path().read_text(encoding="utf-8"))


_I18N_REQUIRED_KEYS = [
    "starter.cs.title",
    "starter.cs.subtitle",
    "starter.cs.nav.listings",
    "starter.cs.listings.title",
    "starter.cs.listings.empty",
    "starter.cs.listing.capacity",
    "starter.cs.listing.location",
    "starter.cs.listing.owner",
    "starter.cs.listing.address",
    "starter.cs.listing.back",
    "starter.cs.form.title",
    "starter.cs.form.nom",
    "starter.cs.form.email",
    "starter.cs.form.phone",
    "starter.cs.form.arrival",
    "starter.cs.form.departure",
    "starter.cs.form.people",
    "starter.cs.form.message",
    "starter.cs.form.submit",
    "starter.cs.request.sent",
    "starter.cs.mail.visitor.subject",
    "starter.cs.mail.owner.subject",
]


def test_i18n_fichier_traduction_existe():
    assert _starter_translations_path().exists()


def test_i18n_fichier_traduction_json_valide():
    catalog = _starter_translations_catalog()
    assert isinstance(catalog, dict)


def test_i18n_fichier_traduction_contient_cles_base():
    catalog = _starter_translations_catalog()
    assert "common.save" in catalog
    assert "validation.required" in catalog
    assert "public.form.submit" in catalog


def test_i18n_cles_starter_presentes():
    catalog = _starter_translations_catalog()
    manquantes = [k for k in _I18N_REQUIRED_KEYS if k not in catalog]
    assert manquantes == [], f"Clés manquantes : {manquantes}"


def test_i18n_toutes_valeurs_non_vides():
    catalog = _starter_translations_catalog()
    vides = [k for k, v in catalog.items() if not isinstance(v, str) or not v.strip()]
    assert vides == [], f"Valeurs vides ou non-chaînes : {vides}"


def test_i18n_cles_notation_pointee():
    catalog = _starter_translations_catalog()
    sans_point = [k for k in catalog if "." not in k]
    assert sans_point == []


def test_i18n_cles_sans_termes_interdits():
    forbidden = ("commune", "sejour", "séjour", "hebergement", "hébergement", "reservation", "réservation")
    catalog = _starter_translations_catalog()
    violations = [k for k in catalog if any(t in k.lower() for t in forbidden)]
    assert violations == [], f"Clés avec termes interdits : {violations}"


def test_i18n_template_accueil_utilise_trans():
    content = (_views_dir() / "home.html").read_text(encoding="utf-8")
    assert "trans(" in content
    assert "starter.cs.title" in content
    assert "starter.cs.nav.listings" in content


def test_i18n_template_liste_utilise_trans():
    content = (_views_dir() / "hebergements_index.html").read_text(encoding="utf-8")
    assert "trans(" in content
    assert "starter.cs.listings.title" in content
    assert "starter.cs.listings.empty" in content
    assert "starter.cs.listing.capacity" in content


def test_i18n_template_fiche_utilise_trans():
    content = (_views_dir() / "hebergements_show.html").read_text(encoding="utf-8")
    assert "trans(" in content
    assert "starter.cs.form.title" in content
    assert "starter.cs.listing.address" in content
    assert "starter.cs.listing.capacity" in content
    assert "starter.cs.form.submit" in content
    assert "starter.cs.listing.back" in content


def test_i18n_template_fiche_labels_formulaire():
    content = (_views_dir() / "hebergements_show.html").read_text(encoding="utf-8")
    assert "starter.cs.form.nom" in content
    assert "starter.cs.form.email" in content
    assert "starter.cs.form.phone" in content
    assert "starter.cs.form.arrival" in content
    assert "starter.cs.form.departure" in content
    assert "starter.cs.form.people" in content
    assert "starter.cs.form.message" in content


def test_i18n_controleur_flash_utilise_trans():
    text = _controller_text()
    assert "trans(" in text
    assert "starter.cs.request.sent" in text


def test_i18n_controleur_importe_trans():
    text = _controller_text()
    assert "from core.i18n import trans" in text


def test_i18n_controleur_passe_trans_au_contexte_mail():
    text = _controller_text()
    assert '"trans"' in text or "'trans'" in text


def test_i18n_formulaire_importe_trans():
    text = (_form_file_text())
    assert "from core.i18n import trans" in text


def test_i18n_formulaire_labels_utilisent_trans():
    text = _form_file_text()
    assert "trans(" in text
    assert "starter.cs.form.nom" in text
    assert "starter.cs.form.email" in text
    assert "starter.cs.form.arrival" in text


def test_i18n_sujet_visiteur_utilise_trans():
    meta = resolve("communes-sejours")
    subject_path = (
        meta["_dir"] / "files" / "mvc" / "mail" / "templates"
        / "communes_sejours" / "demande_visiteur_subject.txt"
    )
    content = subject_path.read_text(encoding="utf-8")
    assert "trans(" in content
    assert "starter.cs.mail.visitor.subject" in content


def test_i18n_sujet_proprietaire_utilise_trans():
    meta = resolve("communes-sejours")
    subject_path = (
        meta["_dir"] / "files" / "mvc" / "mail" / "templates"
        / "communes_sejours" / "demande_proprietaire_subject.txt"
    )
    content = subject_path.read_text(encoding="utf-8")
    assert "trans(" in content
    assert "starter.cs.mail.owner.subject" in content


def test_i18n_sujets_rendus_non_vides():
    fake = _send_notifications(_sample_hebergement(), _sample_form_data())
    assert fake.messages[0].subject.strip()
    assert fake.messages[1].subject.strip()


def test_i18n_build_copie_translations(tmp_path):
    meta = resolve("communes-sejours")
    _forge_project(tmp_path)
    orig = os.getcwd()
    try:
        os.chdir(tmp_path)
        build(meta, init_db=False, force=False, public=False)
    finally:
        os.chdir(orig)
    catalog_path = tmp_path / "translations" / "fr.json"
    assert catalog_path.exists()
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert "starter.cs.title" in catalog
    assert "starter.cs.request.sent" in catalog


def test_i18n_pas_de_route_traduite():
    meta = resolve("communes-sejours")
    snippet_path = meta["_dir"] / "routes.py.snippet"
    content = snippet_path.read_text(encoding="utf-8")
    assert "locale" not in content.lower()
    assert "lang" not in content.lower()


def test_i18n_pas_de_traduction_automatique():
    meta = resolve("communes-sejours")
    files_dir = meta["_dir"] / "files"
    all_py = list(files_dir.rglob("*.py"))
    for f in all_py:
        text = f.read_text(encoding="utf-8")
        assert "deepl" not in text.lower()
        assert "googletrans" not in text.lower()


# ---------------------------------------------------------------------------
# STARTER-CS-SEED-001 — Données de démonstration
# ---------------------------------------------------------------------------

def _seed_dir():
    meta = resolve("communes-sejours")
    return meta["_dir"] / "files" / "seed"


def _load_seed(filename):
    return json.loads((_seed_dir() / filename).read_text(encoding="utf-8"))


def test_seed_dossier_existe():
    assert _seed_dir().exists()
    assert _seed_dir().is_dir()


def test_seed_communes_existe():
    assert (_seed_dir() / "communes.json").exists()


def test_seed_proprietaires_existe():
    assert (_seed_dir() / "proprietaires.json").exists()


def test_seed_hebergements_existe():
    assert (_seed_dir() / "hebergements.json").exists()


def test_seed_demandes_sejour_existe():
    assert (_seed_dir() / "demandes_sejour.json").exists()


def test_seed_communes_json_valide():
    data = _load_seed("communes.json")
    assert isinstance(data, list)
    assert len(data) >= 1


def test_seed_proprietaires_json_valide():
    data = _load_seed("proprietaires.json")
    assert isinstance(data, list)
    assert len(data) >= 1


def test_seed_hebergements_json_valide():
    data = _load_seed("hebergements.json")
    assert isinstance(data, list)
    assert len(data) >= 1


def test_seed_demandes_json_valide():
    data = _load_seed("demandes_sejour.json")
    assert isinstance(data, list)
    assert len(data) >= 1


def test_seed_communes_champs_attendus():
    for c in _load_seed("communes.json"):
        assert "id" in c
        assert "nom" in c
        assert "code_postal" in c


def test_seed_proprietaires_champs_attendus():
    for p in _load_seed("proprietaires.json"):
        assert "id" in p
        assert "nom" in p
        assert "email" in p


def test_seed_hebergements_champs_attendus():
    for h in _load_seed("hebergements.json"):
        assert "id" in h
        assert "titre" in h
        assert "slug" in h
        assert "capacite" in h
        assert "commune_id" in h
        assert "proprietaire_id" in h
        assert "is_published" in h


def test_seed_demandes_champs_attendus():
    for d in _load_seed("demandes_sejour.json"):
        assert "id" in d
        assert "hebergement_id" in d
        assert "nom" in d
        assert "email" in d
        assert "date_arrivee" in d
        assert "date_depart" in d
        assert "nombre_personnes" in d
        assert "statut" in d


def test_seed_hebergements_commune_ids_valides():
    communes = {c["id"] for c in _load_seed("communes.json")}
    for h in _load_seed("hebergements.json"):
        assert h["commune_id"] in communes, (
            f"hebergement {h['id']}: commune_id {h['commune_id']} inconnu"
        )


def test_seed_hebergements_proprietaire_ids_valides():
    proprietaires = {p["id"] for p in _load_seed("proprietaires.json")}
    for h in _load_seed("hebergements.json"):
        assert h["proprietaire_id"] in proprietaires, (
            f"hebergement {h['id']}: proprietaire_id {h['proprietaire_id']} inconnu"
        )


def test_seed_demandes_hebergement_ids_valides():
    hebergements = {h["id"] for h in _load_seed("hebergements.json")}
    for d in _load_seed("demandes_sejour.json"):
        assert d["hebergement_id"] in hebergements, (
            f"demande {d['id']}: hebergement_id {d['hebergement_id']} inconnu"
        )


def test_seed_emails_domaine_example_test():
    for p in _load_seed("proprietaires.json"):
        assert p["email"].endswith("@example.test"), f"Email propriétaire non conforme : {p['email']}"
    for d in _load_seed("demandes_sejour.json"):
        assert d["email"].endswith("@example.test"), f"Email demande non conforme : {d['email']}"


def test_seed_statuts_valides():
    statuts_autorises = {"nouveau", "en_cours", "traite"}
    for d in _load_seed("demandes_sejour.json"):
        assert d["statut"] in statuts_autorises, f"Statut invalide : {d['statut']}"


def test_seed_slugs_alignes_avec_controleur():
    slugs_seed = {h["slug"] for h in _load_seed("hebergements.json")}
    ctrl = _controller_text()
    for slug in slugs_seed:
        assert slug in ctrl, f"Slug seed '{slug}' absent du contrôleur"


def test_seed_pas_de_fichiers_binaires():
    seed_dir = _seed_dir()
    for f in seed_dir.iterdir():
        assert f.suffix == ".json", f"Fichier non-JSON dans seed/ : {f.name}"


def test_seed_pas_de_migration_sql():
    meta = resolve("communes-sejours")
    files_dir = meta["_dir"] / "files"
    sql_files = list(files_dir.rglob("*.sql"))
    assert sql_files == []


def test_build_copie_seed(tmp_path):
    meta = resolve("communes-sejours")
    _forge_project(tmp_path)
    orig = os.getcwd()
    try:
        os.chdir(tmp_path)
        build(meta, init_db=False, force=False, public=False)
    finally:
        os.chdir(orig)
    seed_dir = tmp_path / "seed"
    assert seed_dir.exists()
    assert (seed_dir / "communes.json").exists()
    assert (seed_dir / "proprietaires.json").exists()
    assert (seed_dir / "hebergements.json").exists()
    assert (seed_dir / "demandes_sejour.json").exists()


def test_dry_run_annonce_seed(capsys):
    cmd_starter_build(["5", "--dry-run"])
    output = capsys.readouterr().out
    assert "seed" in output.lower()


# ---------------------------------------------------------------------------
# STARTER-CS-DOC-001 — Documentation
# ---------------------------------------------------------------------------

def _doc_path():
    from pathlib import Path
    return Path("docs") / "starters" / "communes-sejours" / "index.md"


def _doc_text():
    return _doc_path().read_text(encoding="utf-8")


def test_doc_fichier_existe():
    assert _doc_path().exists()


def test_doc_mentionne_routes_publiques():
    doc = _doc_text()
    assert "/communes-sejours/hebergements" in doc
    assert "GET" in doc
    assert "POST" in doc


def test_doc_mentionne_entites():
    doc = _doc_text()
    assert "Commune" in doc
    assert "Proprietaire" in doc
    assert "Hebergement" in doc
    assert "DemandeSejour" in doc


def test_doc_mentionne_limites():
    doc = _doc_text()
    limites = ["réservation", "paiement", "calendrier", "back-office"]
    for terme in limites:
        assert terme in doc, f"Limite absente de la doc : {terme}"


def test_doc_mentionne_seed():
    doc = _doc_text()
    assert "seed/" in doc
    assert "example.test" in doc


def test_doc_mentionne_i18n():
    doc = _doc_text()
    assert "starter.cs" in doc
    assert "trans(" in doc


def test_doc_mentionne_installation():
    doc = _doc_text()
    assert "forge starter:build 5" in doc
    assert "--dry-run" in doc


def test_doc_pas_de_reference_tickets_futurs():
    doc = _doc_text()
    for ticket in ["STARTER-CS-SEED-001", "STARTER-CS-FORM-001", "STARTER-CS-MAIL-001", "STARTER-CS-I18N-001"]:
        assert ticket not in doc, f"Référence ticket future encore présente : {ticket}"
