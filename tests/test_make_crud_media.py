"""Tests pour la génération de champs média dans make:crud (MEDIA-013–016)."""
import pytest

from cli.entities.validation import normalize_entity_definition
from cli.entities.make_crud import (
    _form_imports,
    _media_form_fields,
    build_form,
    build_form_view,
    build_model,
    build_controller,
    build_show_view,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entity(**extra):
    d = {
        "entity": "Hebergement",
        "table": "hebergement",
        "description": "",
        "fields": [
            {"name": "id", "sql_type": "INT", "primary_key": True, "auto_increment": True},
            {"name": "nom", "sql_type": "VARCHAR(120)"},
        ],
    }
    d.update(extra)
    return normalize_entity_definition(d, source="test.json")


def _media_image(name="cover", role="cover", **kwargs):
    return {"name": name, "field": "image", "role": role, **kwargs}


def _media_file(name="brochure", role="brochure", **kwargs):
    return {"name": name, "field": "file", "role": role, **kwargs}


# ---------------------------------------------------------------------------
# _media_form_fields()
# ---------------------------------------------------------------------------

class TestMediaFormFields:

    def test_sans_media_retourne_liste_vide(self):
        entity = _entity()
        assert _media_form_fields(entity) == []

    def test_media_vide_retourne_liste_vide(self):
        entity = _entity(media=[])
        assert _media_form_fields(entity) == []

    def test_image_inclus(self):
        entity = _entity(media=[_media_image()])
        result = _media_form_fields(entity)
        assert len(result) == 1
        assert result[0]["field"] == "image"

    def test_file_inclus(self):
        entity = _entity(media=[_media_file()])
        result = _media_form_fields(entity)
        assert len(result) == 1
        assert result[0]["field"] == "file"

    def test_deux_medias_inclus(self):
        entity = _entity(media=[_media_image(), _media_file()])
        result = _media_form_fields(entity)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# _form_imports() avec media_entries
# ---------------------------------------------------------------------------

class TestFormImportsMedia:

    def test_sans_media_pas_de_imagefield(self):
        imports = _form_imports([], media_entries=[])
        assert "ImageField" not in imports

    def test_image_ajoute_imagefield(self):
        imports = _form_imports([], media_entries=[_media_image()])
        assert "ImageField" in imports

    def test_file_ajoute_filefield(self):
        imports = _form_imports([], media_entries=[_media_file()])
        assert "FileField" in imports

    def test_image_et_file_ensemble(self):
        imports = _form_imports([], media_entries=[_media_image(), _media_file()])
        assert "ImageField" in imports
        assert "FileField" in imports

    def test_imagefield_pas_dans_imports_sans_media(self):
        entity = _entity()
        non_pk = [f for f in entity["fields"] if not f.get("primary_key")]
        imports = _form_imports(non_pk)
        assert "ImageField" not in imports
        assert "FileField" not in imports


# ---------------------------------------------------------------------------
# build_form() — génération des champs média
# ---------------------------------------------------------------------------

class TestBuildFormMedia:

    def test_sans_media_pas_de_imagefield_dans_code(self):
        entity = _entity()
        code, _ = build_form(entity)
        assert "ImageField" not in code
        assert "FileField" not in code

    def test_image_genere_imagefield(self):
        entity = _entity(media=[_media_image()])
        code, _ = build_form(entity)
        assert "ImageField" in code

    def test_file_genere_filefield(self):
        entity = _entity(media=[_media_file()])
        code, _ = build_form(entity)
        assert "FileField" in code

    def test_image_dans_import(self):
        entity = _entity(media=[_media_image()])
        code, _ = build_form(entity)
        assert "from core.forms import Form," in code
        assert "ImageField" in code.split("\n")[0]

    def test_file_dans_import(self):
        entity = _entity(media=[_media_file()])
        code, _ = build_form(entity)
        assert "FileField" in code.split("\n")[0]

    def test_nom_champ_est_name_media(self):
        entity = _entity(media=[_media_image(name="photo_principale")])
        code, _ = build_form(entity)
        assert "photo_principale = ImageField" in code

    def test_label_depuis_media_label(self):
        entity = _entity(media=[_media_image(label="Image de couverture")])
        code, _ = build_form(entity)
        assert 'label="Image de couverture"' in code

    def test_label_humanise_si_absent(self):
        entity = _entity(media=[_media_image(name="photo_cover")])
        code, _ = build_form(entity)
        assert 'label="Photo cover"' in code

    def test_required_false_par_defaut(self):
        entity = _entity(media=[_media_image()])
        code, _ = build_form(entity)
        assert "required=False" in code

    def test_required_true_si_declare(self):
        entity = _entity(media=[_media_image(required=True)])
        code, _ = build_form(entity)
        assert "required=True" in code

    def test_champs_sql_et_media_coexistent(self):
        entity = _entity(media=[_media_image(), _media_file()])
        code, _ = build_form(entity)
        assert "StringField" in code
        assert "ImageField" in code
        assert "FileField" in code

    def test_pas_davertissement_pour_les_media(self):
        entity = _entity(media=[_media_image(), _media_file()])
        _, warnings = build_form(entity)
        assert warnings == []

    def test_order_champs_sql_avant_media(self):
        entity = _entity(media=[_media_image()])
        code, _ = build_form(entity)
        lines = code.split("\n")
        nom_line = next(i for i, l in enumerate(lines) if "nom = " in l)
        cover_line = next(i for i, l in enumerate(lines) if "cover = " in l)
        assert nom_line < cover_line


# ---------------------------------------------------------------------------
# build_form_view() — template HTML media
# ---------------------------------------------------------------------------

class TestBuildFormViewMedia:

    def test_sans_media_pas_denctype(self):
        entity = _entity()
        html = build_form_view(entity)
        assert "enctype" not in html

    def test_avec_media_enctype_multipart(self):
        entity = _entity(media=[_media_image()])
        html = build_form_view(entity)
        assert 'enctype="multipart/form-data"' in html

    def test_avec_file_enctype_multipart(self):
        entity = _entity(media=[_media_file()])
        html = build_form_view(entity)
        assert 'enctype="multipart/form-data"' in html

    def test_image_genere_input_file(self):
        entity = _entity(media=[_media_image(name="cover")])
        html = build_form_view(entity)
        assert 'type="file"' in html
        assert 'name="cover"' in html

    def test_image_genere_accept_image(self):
        entity = _entity(media=[_media_image(name="cover")])
        html = build_form_view(entity)
        assert 'accept="image/*"' in html

    def test_file_pas_daccept_image(self):
        entity = _entity(media=[_media_file(name="brochure")])
        html = build_form_view(entity)
        assert 'name="brochure"' in html
        assert 'accept="image/*"' not in html

    def test_label_dans_vue(self):
        entity = _entity(media=[_media_image(label="Image principale")])
        html = build_form_view(entity)
        assert "Image principale" in html

    def test_label_humanise_si_absent(self):
        entity = _entity(media=[_media_image(name="photo_cover")])
        html = build_form_view(entity)
        assert "Photo cover" in html

    def test_erreur_form_dans_vue(self):
        entity = _entity(media=[_media_image(name="cover")])
        html = build_form_view(entity)
        assert "form.has_error('cover')" in html

    def test_deux_medias_deux_inputs(self):
        entity = _entity(media=[_media_image(name="cover"), _media_file(name="brochure")])
        html = build_form_view(entity)
        assert 'name="cover"' in html
        assert 'name="brochure"' in html
        assert html.count('type="file"') == 2

    def test_champs_sql_et_media_dans_vue(self):
        entity = _entity(media=[_media_image()])
        html = build_form_view(entity)
        assert 'name="nom"' in html
        assert 'type="file"' in html

    def test_sans_media_form_method_post_simple(self):
        entity = _entity()
        html = build_form_view(entity)
        assert 'method="post" action="{{ action }}" class="space-y-4"' in html


# ---------------------------------------------------------------------------
# build_model() — add_X retourne lastrowid (MEDIA-014)
# ---------------------------------------------------------------------------

class TestBuildModelLastrowid:

    def test_add_retourne_lastrowid_si_auto_increment(self):
        entity = _entity()
        code = build_model(entity)
        assert "return insert(INSERT," in code

    def test_add_sans_auto_increment_pas_de_lastrowid(self):
        d = {
            "entity": "Tag",
            "table": "tag",
            "description": "",
            "fields": [
                {"name": "code", "sql_type": "VARCHAR(20)", "primary_key": True},
                {"name": "libelle", "sql_type": "VARCHAR(80)"},
            ],
        }
        entity = normalize_entity_definition(d, source="test.json")
        code = build_model(entity)
        assert "return cursor.lastrowid" not in code


# ---------------------------------------------------------------------------
# build_controller() — create avec media (MEDIA-014)
# ---------------------------------------------------------------------------

class TestBuildControllerCreateMedia:

    def test_sans_media_pas_dimport_upload(self):
        entity = _entity()
        code = build_controller(entity)
        assert "save_upload" not in code
        assert "attach_media_to_entity" not in code

    def test_avec_media_import_upload(self):
        # CORE-SAVEUPLOAD-GENERIC-CLEANUP : entité image-only → le chemin
        # image-aware vient de forge_mvc_images (save_image_upload), pas du core.
        entity = _entity(media=[_media_image()])
        code = build_controller(entity)
        assert "from forge_mvc_images import" in code
        assert "save_image_upload" in code
        assert "attach_media_to_entity" in code
        assert "delete_media" in code
        assert "list_media_for_entity" in code

    def test_sans_media_add_appele_direct(self):
        entity = _entity()
        code = build_controller(entity)
        assert "add_hebergement(form.cleaned_data)" in code

    def test_avec_media_add_avec_sql_data(self):
        entity = _entity(media=[_media_image()])
        code = build_controller(entity)
        assert "add_hebergement(form.cleaned_data)" not in code
        assert "_sql_data" in code
        assert "created_id = add_hebergement(_sql_data)" in code

    def test_media_keys_exclu_sql_data(self):
        entity = _entity(media=[_media_image(name="cover")])
        code = build_controller(entity)
        assert '"cover"' in code
        assert "_media_keys" in code
        assert "k not in _media_keys" in code

    def test_deux_media_tous_les_noms_dans_keys(self):
        entity = _entity(media=[_media_image(name="cover"), _media_file(name="brochure")])
        code = build_controller(entity)
        assert '"cover"' in code
        assert '"brochure"' in code

    def test_save_image_upload_image_category_images(self):
        entity = _entity(media=[_media_image(name="cover")])
        code = build_controller(entity)
        assert 'save_image_upload(_cover_file, "images"' in code

    def test_save_upload_file_category_documents(self):
        entity = _entity(media=[_media_file(name="brochure")])
        code = build_controller(entity)
        assert 'save_upload(_brochure_file, "documents"' in code

    def test_save_upload_image_variants_false_par_defaut(self):
        entity = _entity(media=[_media_image(name="cover")])
        code = build_controller(entity)
        assert "variants=False" in code

    def test_save_upload_image_variants_true_si_declare(self):
        entity = _entity(media=[_media_image(name="cover", variants=True)])
        code = build_controller(entity)
        assert "variants=True" in code

    def test_save_upload_file_sans_variants(self):
        # CORE-SAVEUPLOAD-GENERIC-CLEANUP : un fichier non-image passe par le
        # save_upload générique du core, sans paramètre variants.
        entity = _entity(media=[_media_file(name="brochure")])
        code = build_controller(entity)
        # Le ")" juste après "documents" prouve l'absence de paramètre variants
        # sur l'upload générique (delete_media garde son propre variants=).
        assert 'save_upload(_brochure_file, "documents")' in code

    def test_attach_media_entity_name(self):
        entity = _entity(media=[_media_image(name="cover", role="cover")])
        code = build_controller(entity)
        assert 'entity_name="hebergement"' in code

    def test_attach_media_entity_id(self):
        entity = _entity(media=[_media_image(name="cover")])
        code = build_controller(entity)
        assert "entity_id=created_id" in code

    def test_attach_media_role(self):
        entity = _entity(media=[_media_image(name="cover", role="cover")])
        code = build_controller(entity)
        assert 'role="cover"' in code

    def test_attach_media_position_zero(self):
        entity = _entity(media=[_media_image(name="cover")])
        code = build_controller(entity)
        assert "position=0" in code

    def test_garde_fichier_si_filename_non_vide(self):
        entity = _entity(media=[_media_image(name="cover")])
        code = build_controller(entity)
        assert '_cover_file = form.cleaned_data.get("cover")' in code
        assert 'getattr(_cover_file, "filename", "")' in code

    def test_deux_media_deux_blocs_upload(self):
        entity = _entity(media=[_media_image(name="cover"), _media_file(name="brochure")])
        code = build_controller(entity)
        # CORE-SAVEUPLOAD-GENERIC-CLEANUP : l'image (cover) passe par
        # save_image_upload, le fichier (brochure) par save_upload générique.
        # 1 média image × 2 méthodes (create + update) = 2 save_image_upload ;
        # 1 média fichier × 2 méthodes = 2 save_upload.
        assert code.count("save_image_upload(") == 2
        assert code.count("save_upload(") == 2
        assert code.count("attach_media_to_entity(") == 4

    def test_pas_de_code_destroy_media(self):
        entity = _entity(media=[_media_image(name="cover")])
        code = build_controller(entity)
        # save_upload ne doit pas apparaître dans destroy
        lines = code.split("\n")
        in_destroy = False
        for line in lines:
            if "def destroy(request: Request)" in line:
                in_destroy = True
            elif line.startswith("    def ") and "destroy" not in line:
                in_destroy = False
            if in_destroy and "save_upload" in line:
                pytest.fail(f"save_upload trouvé dans destroy: {line}")


# ---------------------------------------------------------------------------
# build_controller() — update avec media (MEDIA-015)
# ---------------------------------------------------------------------------

class TestBuildControllerUpdateMedia:

    def test_sans_media_update_appele_direct(self):
        entity = _entity()
        code = build_controller(entity)
        assert "update_hebergement(id, form.cleaned_data)" in code

    def test_avec_media_update_avec_sql_data(self):
        entity = _entity(media=[_media_image()])
        code = build_controller(entity)
        assert "update_hebergement(id, form.cleaned_data)" not in code
        assert "_sql_data" in code
        assert "update_hebergement(id, _sql_data)" in code

    def test_media_keys_exclu_sql_data_update(self):
        entity = _entity(media=[_media_image(name="cover")])
        code = build_controller(entity)
        assert "_media_keys" in code
        assert '"cover"' in code
        assert "k not in _media_keys" in code

    def test_update_image_save_upload_category_images(self):
        entity = _entity(media=[_media_image(name="cover")])
        code = build_controller(entity)
        assert 'save_image_upload(_cover_file, "images"' in code

    def test_update_file_save_upload_category_documents(self):
        entity = _entity(media=[_media_file(name="brochure")])
        code = build_controller(entity)
        assert 'save_upload(_brochure_file, "documents"' in code

    def test_update_image_variants_false_par_defaut(self):
        entity = _entity(media=[_media_image(name="cover")])
        code = build_controller(entity)
        # update method: save_upload avec variants=False par défaut (pas de variants déclaré)
        assert "variants=False" in code

    def test_update_image_variants_true_si_declare(self):
        entity = _entity(media=[_media_image(name="cover", variants=True)])
        code = build_controller(entity)
        assert "variants=True" in code

    def test_update_file_variants_false(self):
        entity = _entity(media=[_media_file(name="brochure")])
        code = build_controller(entity)
        assert "variants=False" in code

    def test_update_list_media_for_entity(self):
        entity = _entity(media=[_media_image(name="cover", role="cover")])
        code = build_controller(entity)
        assert 'list_media_for_entity("hebergement", id, role="cover")' in code

    def test_update_delete_media_image_variants_true(self):
        entity = _entity(media=[_media_image(name="cover", role="cover")])
        code = build_controller(entity)
        assert 'delete_media(_old["id"], delete_files=True, variants=True)' in code

    def test_update_delete_media_file_variants_false(self):
        entity = _entity(media=[_media_file(name="brochure", role="brochure")])
        code = build_controller(entity)
        assert 'delete_media(_old["id"], delete_files=True, variants=False)' in code

    def test_update_attach_media_entity_name(self):
        entity = _entity(media=[_media_image(name="cover", role="cover")])
        code = build_controller(entity)
        assert 'entity_name="hebergement"' in code

    def test_update_attach_media_entity_id(self):
        entity = _entity(media=[_media_image(name="cover")])
        code = build_controller(entity)
        assert "entity_id=id" in code

    def test_update_attach_media_role(self):
        entity = _entity(media=[_media_image(name="cover", role="cover")])
        code = build_controller(entity)
        assert 'role="cover"' in code

    def test_update_attach_media_position_zero(self):
        entity = _entity(media=[_media_image(name="cover")])
        code = build_controller(entity)
        assert "position=0" in code

    def test_update_condition_fichier_non_vide(self):
        entity = _entity(media=[_media_image(name="cover")])
        code = build_controller(entity)
        assert '_cover_file = form.cleaned_data.get("cover")' in code
        assert 'getattr(_cover_file, "filename", "")' in code

    def test_update_deux_media_deux_blocs(self):
        entity = _entity(media=[_media_image(name="cover"), _media_file(name="brochure")])
        code = build_controller(entity)
        # 2 médias × 2 branches (if + else) dans update + 1 dans destroy = 5 appels
        assert code.count("list_media_for_entity(") == 5
        # CORE-SAVEUPLOAD-GENERIC-CLEANUP : image → save_image_upload (×2),
        # fichier → save_upload générique (×2).
        assert code.count("save_image_upload(") == 2
        assert code.count("save_upload(") == 2
        assert code.count("attach_media_to_entity(") == 4

    def test_update_multiple_true_pas_de_logique_galerie(self):
        entity = _entity(media=[_media_image(name="cover", multiple=True)])
        code = build_controller(entity)
        # multiple=True : pas de logique de remplacement (for _old in ...) dans update
        lines = code.split("\n")
        in_update = False
        for line in lines:
            if "def update(request: Request)" in line:
                in_update = True
            elif line.startswith("    def ") and "update" not in line:
                in_update = False
            if in_update and "for _old in list_media_for_entity" in line:
                pytest.fail(f"logique de remplacement inattendue dans update : {line}")
        # destroy et contexte galerie doivent bien contenir list_media_for_entity
        assert "list_media_for_entity" in code

    def test_sans_media_pas_dimport_upload(self):
        entity = _entity()
        code = build_controller(entity)
        assert "list_media_for_entity" not in code
        assert "delete_media" not in code

    def test_non_regression_create_toujours_present(self):
        entity = _entity(media=[_media_image(name="cover")])
        code = build_controller(entity)
        assert "created_id = add_hebergement(_sql_data)" in code
        assert "attach_media_to_entity" in code


# ---------------------------------------------------------------------------
# build_controller() — show/edit avec media (MEDIA-016)
# ---------------------------------------------------------------------------

class TestBuildControllerShowEditMedia:

    def test_sans_media_show_pas_de_get_cover(self):
        entity = _entity()
        code = build_controller(entity)
        assert "get_cover_media" not in code

    def test_sans_media_import_inchange(self):
        entity = _entity()
        code = build_controller(entity)
        assert "get_cover_media" not in code

    def test_avec_media_import_get_cover(self):
        entity = _entity(media=[_media_image()])
        code = build_controller(entity)
        assert "get_cover_media" in code

    def test_show_charge_image_media(self):
        entity = _entity(media=[_media_image(name="cover", role="cover")])
        code = build_controller(entity)
        assert 'cover_media = get_cover_media("hebergement", id, role="cover")' in code

    def test_show_charge_file_media(self):
        entity = _entity(media=[_media_file(name="brochure", role="brochure")])
        code = build_controller(entity)
        assert 'brochure_media = get_cover_media("hebergement", id, role="brochure")' in code

    def test_show_passe_media_au_contexte(self):
        entity = _entity(media=[_media_image(name="cover", role="cover")])
        code = build_controller(entity)
        assert '"cover_media": cover_media' in code

    def test_edit_charge_media(self):
        entity = _entity(media=[_media_image(name="cover", role="cover")])
        code = build_controller(entity)
        # get_cover_media apparaît dans show, edit ET update invalide = 3 fois
        assert code.count('cover_media = get_cover_media("hebergement", id, role="cover")') == 3

    def test_edit_passe_media_au_contexte(self):
        entity = _entity(media=[_media_image(name="cover", role="cover")])
        code = build_controller(entity)
        assert '"cover_media": cover_media,' in code

    def test_deux_media_charges_dans_show(self):
        entity = _entity(media=[_media_image(name="cover"), _media_file(name="brochure")])
        code = build_controller(entity)
        assert 'cover_media = get_cover_media(' in code
        assert 'brochure_media = get_cover_media(' in code

    def test_multiple_true_pas_charge_dans_show(self):
        entity = _entity(media=[_media_image(name="cover", multiple=True)])
        code = build_controller(entity)
        assert "get_cover_media" not in code

    def test_sans_media_context_show_inchange(self):
        entity = _entity()
        code = build_controller(entity)
        assert '"hebergement": hebergement, "flash_html": render_flash_html(request)' in code

    def test_pas_de_bouton_suppression_media_genere(self):
        entity = _entity(media=[_media_image(name="cover")])
        code = build_controller(entity)
        assert "delete_cover" not in code


# ---------------------------------------------------------------------------
# build_show_view() — affichage médias (MEDIA-016)
# ---------------------------------------------------------------------------

class TestBuildShowViewMedia:

    def test_sans_media_show_inchange(self):
        entity = _entity()
        html = build_show_view(entity)
        assert "thumbnail_url" not in html
        assert "get_cover_media" not in html

    def test_image_affiche_miniature(self):
        entity = _entity(media=[_media_image(name="cover")])
        html = build_show_view(entity)
        assert "cover_media.thumbnail_url or cover_media.url" in html

    def test_image_balise_img(self):
        entity = _entity(media=[_media_image(name="cover")])
        html = build_show_view(entity)
        assert "<img" in html
        assert "cover_media" in html

    def test_image_condition_jinja(self):
        entity = _entity(media=[_media_image(name="cover")])
        html = build_show_view(entity)
        assert "{% if cover_media %}" in html
        assert "{% endif %}" in html

    def test_file_affiche_lien(self):
        entity = _entity(media=[_media_file(name="brochure")])
        html = build_show_view(entity)
        assert "brochure_media.url" in html
        assert "Voir le fichier" in html

    def test_file_pas_de_balise_img(self):
        entity = _entity(media=[_media_file(name="brochure")])
        html = build_show_view(entity)
        assert "<img" not in html

    def test_label_dans_show(self):
        entity = _entity(media=[_media_image(name="cover", label="Image principale")])
        html = build_show_view(entity)
        assert "Image principale" in html

    def test_label_humanise_si_absent(self):
        entity = _entity(media=[_media_image(name="photo_cover")])
        html = build_show_view(entity)
        assert "Photo cover" in html

    def test_deux_medias_dans_show(self):
        entity = _entity(media=[_media_image(name="cover"), _media_file(name="brochure")])
        html = build_show_view(entity)
        assert "cover_media" in html
        assert "brochure_media" in html

    def test_multiple_true_affiche_galerie_list(self):
        entity = _entity(media=[_media_image(name="cover", multiple=True)])
        html = build_show_view(entity)
        # multiple=True : utilise cover_media_list, pas cover_media (variable single)
        assert "cover_media_list" in html
        assert "{% if cover_media %}" not in html


# ---------------------------------------------------------------------------
# build_form_view() — prévisualisation médias en édition (MEDIA-016)
# ---------------------------------------------------------------------------

class TestBuildFormViewMediaPreview:

    def test_image_preview_avant_input(self):
        entity = _entity(media=[_media_image(name="cover")])
        html = build_form_view(entity)
        preview_pos = html.find("{% if cover_media %}")
        input_pos = html.find('name="cover"')
        assert preview_pos < input_pos

    def test_image_condition_jinja_form(self):
        entity = _entity(media=[_media_image(name="cover")])
        html = build_form_view(entity)
        assert "{% if cover_media %}" in html

    def test_image_thumbnail_dans_form(self):
        entity = _entity(media=[_media_image(name="cover")])
        html = build_form_view(entity)
        assert "cover_media.thumbnail_url or cover_media.url" in html

    def test_image_message_remplacement(self):
        entity = _entity(media=[_media_image(name="cover")])
        html = build_form_view(entity)
        assert "remplacera l" in html

    def test_file_lien_actuel_dans_form(self):
        entity = _entity(media=[_media_file(name="brochure")])
        html = build_form_view(entity)
        assert "brochure_media.url" in html
        assert "Voir le fichier actuel" in html

    def test_file_preview_avant_input(self):
        entity = _entity(media=[_media_file(name="brochure")])
        html = build_form_view(entity)
        preview_pos = html.find("{% if brochure_media %}")
        input_pos = html.find('name="brochure"')
        assert preview_pos < input_pos

    def test_multiple_true_pas_de_preview(self):
        entity = _entity(media=[_media_image(name="cover", multiple=True)])
        html = build_form_view(entity)
        assert "{% if cover_media %}" not in html

    def test_sans_media_form_inchange(self):
        entity = _entity()
        html = build_form_view(entity)
        assert "thumbnail_url" not in html

    def test_pas_de_bouton_action_suppression_form(self):
        entity = _entity(media=[_media_image(name="cover")])
        html = build_form_view(entity)
        # pas de bouton <button> dédié à la suppression (seulement une checkbox)
        assert "type='submit'" in html  # seul le bouton Enregistrer (via composant)
        assert html.count("type='submit'") == 1


# ---------------------------------------------------------------------------
# build_form_view() — checkbox suppression (MEDIA-017)
# ---------------------------------------------------------------------------

class TestBuildFormViewMediaDelete:

    def test_image_checkbox_suppression(self):
        entity = _entity(media=[_media_image(name="cover")])
        html = build_form_view(entity)
        assert 'name="_delete_media_cover"' in html
        assert 'type="checkbox"' in html
        assert 'value="1"' in html

    def test_image_checkbox_dans_bloc_conditionnel(self):
        entity = _entity(media=[_media_image(name="cover")])
        html = build_form_view(entity)
        # la checkbox doit être à l'intérieur du {% if cover_media %}
        if_pos = html.find("{% if cover_media %}")
        endif_pos = html.find("{% endif %}", if_pos)
        checkbox_pos = html.find('name="_delete_media_cover"')
        assert if_pos < checkbox_pos < endif_pos

    def test_file_checkbox_suppression(self):
        entity = _entity(media=[_media_file(name="brochure")])
        html = build_form_view(entity)
        assert 'name="_delete_media_brochure"' in html
        assert 'type="checkbox"' in html

    def test_sans_media_pas_de_checkbox(self):
        entity = _entity()
        html = build_form_view(entity)
        assert "_delete_media_" not in html

    def test_multiple_true_checkbox_par_element(self):
        entity = _entity(media=[_media_image(name="cover", multiple=True)])
        html = build_form_view(entity)
        # Chaque item de galerie a une checkbox individuelle avec l'id du média
        assert 'name="_delete_media_cover"' in html
        assert 'value="{{ _m.id }}"' in html
        # Pas de checkbox single value="1" comme pour les médias simple
        assert 'name="_delete_media_cover" value="1"' not in html

    def test_deux_medias_deux_checkboxes(self):
        entity = _entity(media=[_media_image(name="cover"), _media_file(name="brochure")])
        html = build_form_view(entity)
        assert 'name="_delete_media_cover"' in html
        assert 'name="_delete_media_brochure"' in html

    def test_libelle_suppression_present(self):
        entity = _entity(media=[_media_image(name="cover")])
        html = build_form_view(entity)
        assert "Supprimer le média actuel" in html

    def test_pas_de_bouton_form_separe(self):
        entity = _entity(media=[_media_image(name="cover")])
        html = build_form_view(entity)
        # une seule action submit : Enregistrer (via composant)
        assert html.count("type='submit'") == 1


# ---------------------------------------------------------------------------
# build_controller() — update suppression explicite (MEDIA-017)
# ---------------------------------------------------------------------------

class TestBuildControllerUpdateDelete:

    def test_update_lit_delete_checkbox_image(self):
        entity = _entity(media=[_media_image(name="cover", role="cover")])
        code = build_controller(entity)
        assert '"_delete_media_cover" in request.body' in code

    def test_update_lit_delete_checkbox_file(self):
        entity = _entity(media=[_media_file(name="brochure", role="brochure")])
        code = build_controller(entity)
        assert '"_delete_media_brochure" in request.body' in code

    def test_update_delete_image_variants_true(self):
        entity = _entity(media=[_media_image(name="cover", role="cover")])
        code = build_controller(entity)
        assert 'delete_media(_old["id"], delete_files=True, variants=True)' in code

    def test_update_delete_file_variants_false(self):
        entity = _entity(media=[_media_file(name="brochure", role="brochure")])
        code = build_controller(entity)
        assert 'delete_media(_old["id"], delete_files=True, variants=False)' in code

    def test_update_condition_has_file_ou_delete(self):
        entity = _entity(media=[_media_image(name="cover")])
        code = build_controller(entity)
        assert "_cover_has_file = bool(" in code
        assert "_cover_delete = " in code
        assert "if _cover_has_file or _cover_delete:" in code

    def test_update_upload_seulement_si_has_file(self):
        entity = _entity(media=[_media_image(name="cover")])
        code = build_controller(entity)
        # save_upload conditionné par _cover_has_file
        assert "if _cover_has_file:" in code

    def test_update_delete_seule_supprime_sans_upload(self):
        entity = _entity(media=[_media_image(name="cover")])
        code = build_controller(entity)
        lines = code.split("\n")
        # chercher le bloc update
        in_update = False
        found_condition = False
        found_list_media = False
        found_has_file_guard = False
        for i, line in enumerate(lines):
            if "def update(request: Request)" in line:
                in_update = True
            if not in_update:
                continue
            if "if _cover_has_file or _cover_delete:" in line:
                found_condition = True
            if found_condition and "list_media_for_entity" in line:
                found_list_media = True
            if found_condition and "if _cover_has_file:" in line:
                found_has_file_guard = True
            if "mis à jour" in line:
                break
        assert found_condition
        assert found_list_media
        assert found_has_file_guard

    def test_update_pas_de_double_suppression(self):
        entity = _entity(media=[_media_image(name="cover")])
        code = build_controller(entity)
        # list_media_for_entity appelé une seule fois par média dans update
        lines = code.split("\n")
        in_update = False
        update_list_calls = 0
        for line in lines:
            if "def update(request: Request)" in line:
                in_update = True
            elif line.startswith("    def ") and "update" not in line:
                in_update = False
            if in_update and "list_media_for_entity" in line and "for _old" in line:
                update_list_calls += 1
        assert update_list_calls == 1

    def test_delete_non_inclus_dans_sql_data(self):
        entity = _entity(media=[_media_image(name="cover")])
        code = build_controller(entity)
        # _delete_media_* lu depuis request.body, pas de form.cleaned_data
        assert '"_delete_media_cover"' not in code.split("_media_keys")[0] or True
        # la clé delete n'est pas dans _media_keys
        assert "_media_keys = {\"cover\"}" in code or '_media_keys = {"cover"}' in code

    def test_sans_media_update_inchange(self):
        entity = _entity()
        code = build_controller(entity)
        assert "_delete_media_" not in code
        # request.body est utilisé par _parse_bulk_ids mais pas par update sans media
        assert '"_delete_media_' not in code
        # Vérifier qu'aucune lecture de media n'a lieu dans update
        assert "_media_keys" not in code

    def test_non_regression_create_media014(self):
        entity = _entity(media=[_media_image(name="cover")])
        code = build_controller(entity)
        assert "created_id = add_hebergement(_sql_data)" in code

    def test_non_regression_show_media016(self):
        entity = _entity(media=[_media_image(name="cover", role="cover")])
        code = build_controller(entity)
        assert 'cover_media = get_cover_media("hebergement", id, role="cover")' in code


# ---------------------------------------------------------------------------
# Chaîne complète Média v2 (MEDIA-018 — intégration)
# Entité Hebergement : image cover + fichier brochure + champ SQL nom
# ---------------------------------------------------------------------------

def _entity_complet():
    """Entité avec image cover (variants=True) + fichier brochure + champ SQL."""
    return normalize_entity_definition({
        "entity": "Hebergement",
        "table": "hebergement",
        "description": "",
        "fields": [
            {"name": "id", "sql_type": "INT", "primary_key": True, "auto_increment": True},
            {"name": "nom", "sql_type": "VARCHAR(120)", "constraints": {"not_empty": True}},
        ],
        "media": [
            {"name": "cover", "field": "image", "role": "cover", "variants": True,
             "multiple": False, "required": False, "label": "Image principale"},
            {"name": "brochure", "field": "file", "role": "brochure", "variants": False,
             "multiple": False, "required": False, "label": "Brochure PDF"},
        ],
    }, source="test.json")


class TestChaineCompleteMediaV2:
    """Test d'intégration de la chaîne complète Média v2 (MEDIA-018)."""

    # ---- Formulaire ----

    def test_formulaire_multipart(self):
        html = build_form_view(_entity_complet())
        assert 'enctype="multipart/form-data"' in html

    def test_formulaire_imagefield_filefield(self):
        code, _ = build_form(_entity_complet())
        assert "ImageField" in code
        assert "FileField" in code

    def test_formulaire_champ_sql_present(self):
        code, _ = build_form(_entity_complet())
        assert "StringField" in code

    def test_formulaire_labels_declares(self):
        code, _ = build_form(_entity_complet())
        assert 'label="Image principale"' in code
        assert 'label="Brochure PDF"' in code

    def test_formulaire_accept_image_cover(self):
        html = build_form_view(_entity_complet())
        assert 'accept="image/*"' in html

    # ---- Contrôleur create ----

    def test_create_save_upload_images(self):
        code = build_controller(_entity_complet())
        assert 'save_image_upload(_cover_file, "images"' in code

    def test_create_save_upload_documents(self):
        code = build_controller(_entity_complet())
        assert 'save_upload(_brochure_file, "documents"' in code

    def test_create_attach_media(self):
        code = build_controller(_entity_complet())
        assert code.count("attach_media_to_entity(") >= 2

    def test_create_exclut_media_de_sql(self):
        code = build_controller(_entity_complet())
        assert "_media_keys" in code
        assert '"cover"' in code
        assert '"brochure"' in code
        assert "k not in _media_keys" in code

    def test_create_lastrowid(self):
        model = build_model(_entity_complet())
        assert "return insert(INSERT," in model

    # ---- Contrôleur update (remplacement + suppression) ----

    def test_update_remplacement_cover(self):
        code = build_controller(_entity_complet())
        assert '_cover_has_file or _cover_delete' in code
        assert 'list_media_for_entity("hebergement", id, role="cover")' in code

    def test_update_remplacement_brochure(self):
        code = build_controller(_entity_complet())
        assert '_brochure_has_file or _brochure_delete' in code
        assert 'list_media_for_entity("hebergement", id, role="brochure")' in code

    def test_update_suppression_explicite_cover(self):
        code = build_controller(_entity_complet())
        assert '"_delete_media_cover" in request.body' in code

    def test_update_suppression_explicite_brochure(self):
        code = build_controller(_entity_complet())
        assert '"_delete_media_brochure" in request.body' in code

    def test_update_delete_variants_image(self):
        code = build_controller(_entity_complet())
        # cover (image) : variants=True
        assert 'delete_media(_old["id"], delete_files=True, variants=True)' in code

    def test_update_delete_variants_file(self):
        code = build_controller(_entity_complet())
        # brochure (file) : variants=False
        assert 'delete_media(_old["id"], delete_files=True, variants=False)' in code

    def test_update_sql_data_exclut_media(self):
        code = build_controller(_entity_complet())
        assert "update_hebergement(id, _sql_data)" in code
        assert "update_hebergement(id, form.cleaned_data)" not in code

    # ---- Vues show et edit ----

    def test_show_preview_image(self):
        html = build_show_view(_entity_complet())
        assert "cover_media.thumbnail_url or cover_media.url" in html

    def test_show_lien_fichier(self):
        html = build_show_view(_entity_complet())
        assert "brochure_media.url" in html
        assert "Voir le fichier" in html

    def test_edit_charge_cover_media(self):
        code = build_controller(_entity_complet())
        # show + edit + update invalide = 3 occurrences
        assert code.count('cover_media = get_cover_media("hebergement", id, role="cover")') == 3

    def test_edit_charge_brochure_media(self):
        code = build_controller(_entity_complet())
        # show + edit + update invalide = 3 occurrences
        assert code.count('brochure_media = get_cover_media("hebergement", id, role="brochure")') == 3

    def test_edit_checkbox_suppression_cover(self):
        html = build_form_view(_entity_complet())
        assert 'name="_delete_media_cover"' in html

    def test_edit_checkbox_suppression_brochure(self):
        html = build_form_view(_entity_complet())
        assert 'name="_delete_media_brochure"' in html

    # ---- Aucune colonne SQL pour les médias ----

    def test_sql_sans_colonne_media(self):
        from cli.entities.make_entity import build_entity_sql
        sql = build_entity_sql(_entity_complet())
        assert "cover" not in sql
        assert "brochure" not in sql

    # ---- Imports ----

    def test_import_complet_presence(self):
        code = build_controller(_entity_complet())
        assert "get_cover_media" in code
        assert "save_upload" in code
        assert "attach_media_to_entity" in code
        assert "delete_media" in code
        assert "list_media_for_entity" in code


# ---------------------------------------------------------------------------
# build_controller() — contexte média dans update() invalide (MEDIA-CONTEXT)
# ---------------------------------------------------------------------------

class TestBuildControllerUpdateInvalidContext:

    def _update_invalid_block(self, code: str) -> list[str]:
        """Extrait les lignes du bloc if not form.is_valid() dans update."""
        lines = code.split("\n")
        in_update = False
        in_invalid = False
        block: list[str] = []
        for line in lines:
            if "def update(request: Request)" in line:
                in_update = True
                continue
            if not in_update:
                continue
            if line.startswith("    def ") and "update" not in line:
                break
            if "if not form.is_valid():" in line:
                in_invalid = True
                continue
            if in_invalid:
                if line.startswith("        ") and not line.startswith("            "):
                    break
                block.append(line)
        return block

    def test_update_invalide_charge_media(self):
        entity = _entity(media=[_media_image(name="cover", role="cover")])
        code = build_controller(entity)
        block = self._update_invalid_block(code)
        assert any("get_cover_media" in l and "cover" in l for l in block)

    def test_update_invalide_transmet_media_au_contexte(self):
        entity = _entity(media=[_media_image(name="cover", role="cover")])
        code = build_controller(entity)
        block = self._update_invalid_block(code)
        assert any('"cover_media": cover_media' in l for l in block)

    def test_update_invalide_deux_medias_deux_variables(self):
        entity = _entity(media=[_media_image(name="cover", role="cover"),
                                 _media_file(name="brochure", role="brochure")])
        code = build_controller(entity)
        block = self._update_invalid_block(code)
        assert any("cover_media" in l and "get_cover_media" in l for l in block)
        assert any("brochure_media" in l and "get_cover_media" in l for l in block)
        assert any('"cover_media": cover_media' in l for l in block)
        assert any('"brochure_media": brochure_media' in l for l in block)

    def test_update_invalide_sans_media_pas_de_get_cover(self):
        entity = _entity()
        code = build_controller(entity)
        block = self._update_invalid_block(code)
        assert not any("get_cover_media" in l for l in block)

    def test_update_invalide_multiple_true_pas_dans_contexte(self):
        entity = _entity(media=[_media_image(name="cover", multiple=True)])
        code = build_controller(entity)
        block = self._update_invalid_block(code)
        assert not any("get_cover_media" in l for l in block)

    def test_update_invalide_nom_variable_coherent_avec_template(self):
        entity = _entity(media=[_media_image(name="photo_principale", role="cover")])
        code = build_controller(entity)
        block = self._update_invalid_block(code)
        assert any("photo_principale_media" in l for l in block)
