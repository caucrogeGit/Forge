from __future__ import annotations

import json
from pathlib import Path


from cli.public_list import (
    PublicMediaEntry,
    build_public_list_controller,
    build_public_list_spec,
    build_public_list_template,
    build_public_show_controller,
    build_public_show_method,
    build_public_show_template,
    make_public_list,
    make_public_show,
    public_media_entries,
)
from tests.test_make_public_list import HEBERGEMENT_JSON, _field, _prepare_project, _read


HEBERGEMENT_COVER_JSON = {
    "entity": "Hebergement",
    "table": "hebergement",
    "description": "",
    "fields": [
        _field("id", "INT", column="Id", python_type="int", primary_key=True, auto_increment=True),
        _field("nom", "VARCHAR(120)", column="Nom"),
        _field("prix", "DECIMAL(10,2)", column="Prix", python_type="float"),
    ],
    "media": [
        {
            "name": "cover",
            "field": "image",
            "role": "cover",
            "label": "Image de couverture",
            "variants": True,
            "multiple": False,
        }
    ],
}

HEBERGEMENT_GALLERY_JSON = {
    "entity": "Hebergement",
    "table": "hebergement",
    "description": "",
    "fields": [
        _field("id", "INT", column="Id", python_type="int", primary_key=True, auto_increment=True),
        _field("nom", "VARCHAR(120)", column="Nom"),
    ],
    "media": [
        {
            "name": "photos",
            "field": "image",
            "role": "photos",
            "label": "Galerie photos",
            "multiple": True,
        }
    ],
}

HEBERGEMENT_BROCHURE_JSON = {
    "entity": "Hebergement",
    "table": "hebergement",
    "description": "",
    "fields": [
        _field("id", "INT", column="Id", python_type="int", primary_key=True, auto_increment=True),
        _field("nom", "VARCHAR(120)", column="Nom"),
    ],
    "media": [
        {
            "name": "brochure",
            "field": "file",
            "role": "brochure",
            "label": "Brochure PDF",
            "multiple": False,
        }
    ],
}

HEBERGEMENT_ALL_MEDIA_JSON = {
    "entity": "Hebergement",
    "table": "hebergement",
    "description": "",
    "fields": [
        _field("id", "INT", column="Id", python_type="int", primary_key=True, auto_increment=True),
        _field("nom", "VARCHAR(120)", column="Nom"),
    ],
    "media": [
        {"name": "cover", "field": "image", "role": "cover", "label": "Couverture", "multiple": False},
        {"name": "photos", "field": "image", "role": "photos", "label": "Galerie", "multiple": True},
        {"name": "brochure", "field": "file", "role": "brochure", "label": "Brochure", "multiple": False},
        {"name": "docs", "field": "file", "role": "docs", "label": "Documents", "multiple": True},
    ],
}


def _prepare_media_project(root: Path, definition: dict) -> Path:
    snake = definition["entity"].lower()
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


# --- public_media_entries ---

def test_public_media_entries_extraits_de_definition():
    entries = public_media_entries(HEBERGEMENT_COVER_JSON)

    assert len(entries) == 1
    assert entries[0].name == "cover"
    assert entries[0].role == "cover"
    assert entries[0].field_type == "image"
    assert entries[0].label == "Image de couverture"
    assert entries[0].multiple is False


def test_public_media_entries_vide_si_pas_de_media():
    assert public_media_entries(HEBERGEMENT_JSON) == []


def test_public_media_entries_retourne_toutes_les_entrees():
    entries = public_media_entries(HEBERGEMENT_ALL_MEDIA_JSON)

    assert len(entries) == 4
    names = [e.name for e in entries]
    assert names == ["cover", "photos", "brochure", "docs"]


def test_public_media_entries_multiple_correctement_parse():
    entries = public_media_entries(HEBERGEMENT_GALLERY_JSON)

    assert len(entries) == 1
    assert entries[0].multiple is True
    assert entries[0].field_type == "image"


# --- PublicListSpec ---

def test_build_public_list_spec_inclut_media_entries():
    spec = build_public_list_spec(HEBERGEMENT_COVER_JSON)

    assert len(spec.media_entries) == 1
    assert isinstance(spec.media_entries[0], PublicMediaEntry)
    assert spec.media_entries[0].name == "cover"


def test_build_public_list_spec_sans_media_entries_vide():
    spec = build_public_list_spec(HEBERGEMENT_JSON)

    assert spec.media_entries == []


# --- Liste controller avec image cover ---

def test_list_controller_avec_cover_image_ajoute_entity_id_dans_select():
    spec = build_public_list_spec(HEBERGEMENT_COVER_JSON)
    controller = build_public_list_controller(spec)

    assert "Id AS _entity_id" in controller
    assert "SELECT_PUBLIC_LIST" in controller


def test_list_controller_avec_cover_image_enrichit_rows_avec_get_cover_media():
    spec = build_public_list_spec(HEBERGEMENT_COVER_JSON)
    controller = build_public_list_controller(spec)

    assert 'for _row in rows' in controller
    assert '_row["_cover_media"] = get_cover_media("hebergement", _row["_entity_id"], role="cover")' in controller


def test_list_controller_avec_cover_image_importe_get_cover_media():
    spec = build_public_list_spec(HEBERGEMENT_COVER_JSON)
    controller = build_public_list_controller(spec)

    assert "from forge_mvc_images import get_cover_media" in controller


def test_list_controller_sans_media_inchange():
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    controller = build_public_list_controller(spec)

    assert "_entity_id" not in controller
    assert "get_cover_media" not in controller
    assert "core.uploads" not in controller


def test_list_controller_avec_fichier_seul_nexpose_pas_entity_id():
    spec = build_public_list_spec(HEBERGEMENT_BROCHURE_JSON)
    controller = build_public_list_controller(spec)

    assert "_entity_id" not in controller
    assert "get_cover_media" not in controller


# --- Liste template avec image cover ---

def test_list_template_avec_cover_image_affiche_colonne_image():
    spec = build_public_list_spec(HEBERGEMENT_COVER_JSON)
    template = build_public_list_template(spec)

    assert "Image de couverture" in template
    assert "_cover_media" in template
    assert "<img src=" in template
    assert "thumbnail_url or" in template


def test_list_template_avec_cover_image_lien_vers_url_media():
    spec = build_public_list_spec(HEBERGEMENT_COVER_JSON)
    template = build_public_list_template(spec)

    assert "row._cover_media.thumbnail_url or row._cover_media.url" in template


def test_list_template_sans_media_pas_dimage():
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    template = build_public_list_template(spec)

    assert "<img" not in template
    assert "_cover_media" not in template


def test_list_template_avec_fichier_seul_pas_dimage():
    spec = build_public_list_spec(HEBERGEMENT_BROCHURE_JSON)
    template = build_public_list_template(spec)

    assert "<img" not in template
    assert "_cover_media" not in template


# --- Show method avec médias ---

def test_show_method_avec_cover_charge_get_cover_media():
    spec = build_public_list_spec(HEBERGEMENT_COVER_JSON)
    method = build_public_show_method(spec)

    assert 'get_cover_media("hebergement", int(public_id), role="cover")' in method
    assert "cover_media" in method


def test_show_method_avec_gallery_charge_list_media_for_entity():
    spec = build_public_list_spec(HEBERGEMENT_GALLERY_JSON)
    method = build_public_show_method(spec)

    assert 'list_media_for_entity("hebergement", int(public_id), role="photos")' in method
    assert "photos_media_list" in method


def test_show_method_passe_variables_media_au_contexte():
    spec = build_public_list_spec(HEBERGEMENT_COVER_JSON)
    method = build_public_show_method(spec)

    assert '"cover_media": cover_media' in method


def test_show_method_passe_liste_media_au_contexte():
    spec = build_public_list_spec(HEBERGEMENT_GALLERY_JSON)
    method = build_public_show_method(spec)

    assert '"photos_media_list": photos_media_list' in method


def test_show_method_sans_media_inchange():
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    method = build_public_show_method(spec)

    assert "get_cover_media" not in method
    assert "list_media_for_entity" not in method
    assert "core.uploads" not in method


def test_show_method_tous_les_medias_charges():
    spec = build_public_list_spec(HEBERGEMENT_ALL_MEDIA_JSON)
    method = build_public_show_method(spec)

    assert 'get_cover_media("hebergement", int(public_id), role="cover")' in method
    assert 'list_media_for_entity("hebergement", int(public_id), role="photos")' in method
    assert 'get_cover_media("hebergement", int(public_id), role="brochure")' in method
    assert 'list_media_for_entity("hebergement", int(public_id), role="docs")' in method


# --- Show controller avec médias ---

def test_show_controller_avec_cover_importe_get_cover_media():
    spec = build_public_list_spec(HEBERGEMENT_COVER_JSON)
    controller = build_public_show_controller(spec)

    assert "from forge_mvc_images import get_cover_media" in controller


def test_show_controller_avec_gallery_importe_list_media_for_entity():
    spec = build_public_list_spec(HEBERGEMENT_GALLERY_JSON)
    controller = build_public_show_controller(spec)

    assert "from forge_mvc_images import list_media_for_entity" in controller


def test_show_controller_avec_cover_et_gallery_importe_les_deux():
    spec = build_public_list_spec(HEBERGEMENT_ALL_MEDIA_JSON)
    controller = build_public_show_controller(spec)

    assert "from forge_mvc_images import get_cover_media, list_media_for_entity" in controller


def test_show_controller_sans_media_pas_dimport_uploads():
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    controller = build_public_show_controller(spec)

    assert "core.uploads" not in controller


# --- Show template avec médias ---

def test_show_template_avec_image_single_affiche_img():
    spec = build_public_list_spec(HEBERGEMENT_COVER_JSON)
    template = build_public_show_template(spec)

    assert "<img src=" in template
    assert "cover_media.thumbnail_url or cover_media.url" in template
    assert "Image de couverture" in template


def test_show_template_avec_galerie_image_affiche_boucle():
    spec = build_public_list_spec(HEBERGEMENT_GALLERY_JSON)
    template = build_public_show_template(spec)

    assert "{% for _m in photos_media_list %}" in template
    assert "<img src=" in template
    assert "_m.thumbnail_url or _m.url" in template


def test_show_template_avec_fichier_single_affiche_lien():
    spec = build_public_list_spec(HEBERGEMENT_BROCHURE_JSON)
    template = build_public_show_template(spec)

    assert '<a href="{{ brochure_media.url }}"' in template
    assert "Brochure PDF" in template


def test_show_template_avec_fichiers_multiples_affiche_liste():
    definition = {
        "entity": "Hebergement",
        "table": "hebergement",
        "description": "",
        "fields": [
            _field("id", "INT", column="Id", python_type="int", primary_key=True, auto_increment=True),
            _field("nom", "VARCHAR(120)", column="Nom"),
        ],
        "media": [
            {"name": "docs", "field": "file", "role": "docs", "label": "Documents", "multiple": True},
        ],
    }
    spec = build_public_list_spec(definition)
    template = build_public_show_template(spec)

    assert "{% for _m in docs_media_list %}" in template
    assert '<a href="{{ _m.url }}"' in template


def test_show_template_sans_media_pas_dimage():
    spec = build_public_list_spec(HEBERGEMENT_JSON)
    template = build_public_show_template(spec)

    assert "<img" not in template
    assert "media" not in template.lower().replace("aucun media", "")


def test_show_template_avec_tous_les_medias_contient_toutes_sections():
    spec = build_public_list_spec(HEBERGEMENT_ALL_MEDIA_JSON)
    template = build_public_show_template(spec)

    assert "cover_media" in template
    assert "photos_media_list" in template
    assert "brochure_media" in template
    assert "docs_media_list" in template


# --- Tests d'intégration (make_public_list + make_public_show) ---

def test_make_public_list_avec_media_genere_controleur_complet(tmp_path):
    _prepare_media_project(tmp_path, HEBERGEMENT_COVER_JSON)

    make_public_list("Hebergement", output_root=tmp_path)

    controller = _read(tmp_path, "mvc/controllers/public_hebergements_controller.py")
    assert "from forge_mvc_images import get_cover_media" in controller
    assert "_entity_id" in controller
    assert "_cover_media" in controller


def test_make_public_show_avec_media_genere_controleur_complet(tmp_path):
    _prepare_media_project(tmp_path, HEBERGEMENT_COVER_JSON)

    make_public_show("Hebergement", output_root=tmp_path)

    controller = _read(tmp_path, "mvc/controllers/public_hebergements_controller.py")
    assert "from forge_mvc_images import get_cover_media" in controller
    assert "get_cover_media" in controller
    assert "cover_media" in controller


def test_make_public_show_complete_controleur_list_avec_media(tmp_path):
    _prepare_media_project(tmp_path, HEBERGEMENT_COVER_JSON)
    make_public_list("Hebergement", output_root=tmp_path)

    make_public_show("Hebergement", output_root=tmp_path)

    controller = _read(tmp_path, "mvc/controllers/public_hebergements_controller.py")
    assert "def index(request: Request) -> Response:" in controller
    assert "def show(request: Request) -> Response:" in controller
    assert "SELECT_PUBLIC_LIST" in controller
    assert "SELECT_PUBLIC_DETAIL" in controller
    assert "get_cover_media" in controller


def test_make_public_list_sans_media_reste_identique(tmp_path):
    _prepare_project(tmp_path)

    make_public_list("Hebergement", output_root=tmp_path)

    controller = _read(tmp_path, "mvc/controllers/public_hebergements_controller.py")
    assert "core.uploads" not in controller
    assert "_entity_id" not in controller


# --- Pas de dépendances optionnelles dans les médias publics ---

def test_media_public_nexpose_aucun_lien_crud_admin():
    spec = build_public_list_spec(HEBERGEMENT_COVER_JSON)
    generated = (
        build_public_list_template(spec)
        + build_public_show_template(spec)
        + build_public_list_controller(spec)
        + build_public_show_controller(spec)
    )

    assert "/hebergements/new" not in generated
    assert "/edit" not in generated
    assert "/delete" not in generated
    assert "layouts/admin.html" not in generated


def test_media_public_najoute_pas_htmx_ni_alpine():
    spec = build_public_list_spec(HEBERGEMENT_COVER_JSON)
    generated = (
        build_public_list_template(spec)
        + build_public_show_template(spec)
    )

    assert "htmx" not in generated.lower()
    assert "hx-" not in generated
    assert "alpine" not in generated.lower()
    assert "<script" not in generated
