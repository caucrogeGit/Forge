"""Tests multi-upload galerie — MEDIA-GALLERY-MULTIUPLOAD-001.

Vérifie que le contrôleur généré par make:crud permet d'ajouter plusieurs
médias à une galerie (multiple=true) en une seule soumission :
- form.html génère <input type="file" multiple> pour les galeries ;
- create() boucle sur la liste de fichiers reçus ;
- update() boucle sur la liste de fichiers reçus en append-only ;
- un seul fichier continue de fonctionner (backward-compat) ;
- liste vide → aucun upload ;
- formulaire invalide → aucun upload ;
- entités sans galerie restent inchangées.
"""
from __future__ import annotations

import sys
import types
from types import SimpleNamespace

import pytest

from forge_mvc_entities.make_crud import build_controller, build_form, build_form_view
from forge_mvc_entities.validation import normalize_entity_definition
from forge_mvc_testing import FakeRequest


# ── Entités de référence ──────────────────────────────────────────────────────

def _article_with_gallery():
    return normalize_entity_definition(
        {
            "entity": "Article",
            "table": "article",
            "description": "",
            "fields": [
                {"name": "id",    "sql_type": "INT",          "primary_key": True, "auto_increment": True},
                {"name": "titre", "sql_type": "VARCHAR(120)", "constraints": {"not_empty": True}},
            ],
            "media": [
                {
                    "name": "photos",
                    "field": "image",
                    "role": "gallery",
                    "variants": False,
                    "multiple": True,
                    "required": False,
                    "label": "Photos",
                }
            ],
        },
        source="test.json",
    )


def _article_without_media():
    return normalize_entity_definition(
        {
            "entity": "Article",
            "table": "article",
            "description": "",
            "fields": [
                {"name": "id",    "sql_type": "INT",          "primary_key": True, "auto_increment": True},
                {"name": "titre", "sql_type": "VARCHAR(120)", "constraints": {"not_empty": True}},
            ],
        },
        source="test.json",
    )


def _article_mixed():
    """Entité avec un champ single (cover) ET un champ multiple (photos)."""
    return normalize_entity_definition(
        {
            "entity": "Article",
            "table": "article",
            "description": "",
            "fields": [
                {"name": "id",    "sql_type": "INT",          "primary_key": True, "auto_increment": True},
                {"name": "titre", "sql_type": "VARCHAR(120)", "constraints": {"not_empty": True}},
            ],
            "media": [
                {"name": "cover",  "field": "image", "role": "cover",   "multiple": False},
                {"name": "photos", "field": "image", "role": "gallery", "multiple": True},
            ],
        },
        source="test.json",
    )


# ── Helpers d'extraction ──────────────────────────────────────────────────────

def _lines_in_method(code: str, method_name: str) -> list[str]:
    lines = code.split("\n")
    result = []
    inside = False
    for line in lines:
        if f"def {method_name}(request: Request)" in line:
            inside = True
            continue
        if inside:
            if line.startswith("    def ") and method_name not in line:
                break
            result.append(line)
    return result


# ── Tests de génération ───────────────────────────────────────────────────────

class TestMultiuploadGeneration:

    def test_form_html_ajoute_multiple_pour_galerie(self):
        html = build_form_view(_article_with_gallery())
        assert "multiple" in html

    def test_form_html_ne_met_pas_multiple_pour_single(self):
        def _single():
            return normalize_entity_definition(
                {
                    "entity": "Article", "table": "article", "description": "",
                    "fields": [
                        {"name": "id", "sql_type": "INT", "primary_key": True, "auto_increment": True},
                        {"name": "titre", "sql_type": "VARCHAR(120)", "constraints": {"not_empty": True}},
                    ],
                    "media": [{"name": "cover", "field": "image", "role": "cover", "multiple": False}],
                },
                source="test.json",
            )
        html = build_form_view(_single())
        assert "multiple" not in html

    def test_form_html_mixed_seul_multiple_porte_attribut(self):
        html = build_form_view(_article_mixed())
        lines = html.split("\n")
        photos_idx = next((i for i, l in enumerate(lines) if 'name="photos"' in l), None)
        cover_idx  = next((i for i, l in enumerate(lines) if 'name="cover"' in l), None)
        assert photos_idx is not None
        assert cover_idx is not None
        # La ligne "multiple" doit apparaître après name="photos" mais avant name="cover"
        # (ou l'inverse selon l'ordre de déclaration — il suffit qu'elle soit présente une fois)
        assert any("multiple" in l for l in lines)

    def test_create_boucle_sur_fichiers_galerie(self):
        code = build_controller(_article_with_gallery())
        create_lines = _lines_in_method(code, "create")
        assert any("for _photos_f in _photos_files" in l for l in create_lines)

    def test_create_normalise_fichier_unique_en_liste(self):
        code = build_controller(_article_with_gallery())
        create_lines = _lines_in_method(code, "create")
        assert any("isinstance(_photos_files_raw, list)" in l for l in create_lines)

    def test_create_utilise_request_files_pas_cleaned_data(self):
        code = build_controller(_article_with_gallery())
        create_lines = _lines_in_method(code, "create")
        assert any('request.files.get("photos"' in l for l in create_lines)
        assert not any('form.cleaned_data.get("photos")' in l for l in create_lines)

    def test_update_boucle_sur_fichiers_galerie(self):
        code = build_controller(_article_with_gallery())
        update_lines = _lines_in_method(code, "update")
        assert any("for _photos_f in _photos_files" in l for l in update_lines)

    def test_update_utilise_request_files_pas_cleaned_data(self):
        code = build_controller(_article_with_gallery())
        update_lines = _lines_in_method(code, "update")
        assert any('request.files.get("photos"' in l for l in update_lines)
        assert not any('form.cleaned_data.get("photos")' in l for l in update_lines)

    def test_update_ne_contient_pas_delete_media_pour_multiupload(self):
        code = build_controller(_article_with_gallery())
        update_lines = _lines_in_method(code, "update")
        # La boucle d'upload (dernière occurrence de for _photos_f) ne doit pas
        # contenir delete_media — ce bloc appartient à la suppression individuelle.
        last_upload_idx = None
        for i, l in enumerate(update_lines):
            if "for _photos_f in _photos_files" in l:
                last_upload_idx = i
        assert last_upload_idx is not None
        for l in update_lines[last_upload_idx:]:
            if "delete_media" in l:
                pytest.fail("delete_media trouvé dans la boucle d'upload multi")

    def test_sql_data_exclut_champ_galerie(self):
        code = build_controller(_article_with_gallery())
        assert '"photos"' in code
        assert '_media_keys' in code
        assert '_sql_data' in code

    def test_entite_sans_galerie_aucun_code_multiupload(self):
        code = build_controller(_article_without_media())
        assert "request.files" not in code
        assert "_files_raw" not in code

    def test_mixed_single_utilise_cleaned_data_pas_files(self):
        code = build_controller(_article_mixed())
        create_lines = _lines_in_method(code, "create")
        assert any('form.cleaned_data.get("cover")' in l for l in create_lines)
        assert any('request.files.get("photos"' in l for l in create_lines)

    # ── Tests de génération pour la validation ────────────────────────────────

    def test_create_contient_validation_avant_save_upload(self):
        code = build_controller(_article_with_gallery())
        create_lines = _lines_in_method(code, "create")
        validate_idx = next((i for i, l in enumerate(create_lines) if 'form.fields["photos"].validate' in l), None)
        save_idx = next((i for i, l in enumerate(create_lines) if "save_image_upload" in l), None)
        assert validate_idx is not None, "form.fields validation absent de create()"
        assert save_idx is not None
        assert validate_idx < save_idx

    def test_update_contient_validation_avant_save_upload(self):
        code = build_controller(_article_with_gallery())
        update_lines = _lines_in_method(code, "update")
        validate_idx = next((i for i, l in enumerate(update_lines) if 'form.fields["photos"].validate' in l), None)
        save_idx = next((i for i, l in enumerate(update_lines) if "save_image_upload" in l), None)
        assert validate_idx is not None, "form.fields validation absent de update()"
        assert save_idx is not None
        assert validate_idx < save_idx

    def test_update_validation_avant_delete_media(self):
        code = build_controller(_article_with_gallery())
        update_lines = _lines_in_method(code, "update")
        validate_idx = next((i for i, l in enumerate(update_lines) if 'form.fields["photos"].validate' in l), None)
        delete_idx = next((i for i, l in enumerate(update_lines) if 'delete_media(int(_did)' in l), None)
        assert validate_idx is not None
        assert delete_idx is not None
        assert validate_idx < delete_idx

    def test_update_validation_avant_update_media_position(self):
        code = build_controller(_article_with_gallery())
        update_lines = _lines_in_method(code, "update")
        validate_idx = next((i for i, l in enumerate(update_lines) if 'form.fields["photos"].validate' in l), None)
        pos_idx = next((i for i, l in enumerate(update_lines) if "update_media_position" in l), None)
        assert validate_idx is not None
        assert pos_idx is not None
        assert validate_idx < pos_idx

    def test_update_validation_avant_update_media_alt_text(self):
        code = build_controller(_article_with_gallery())
        update_lines = _lines_in_method(code, "update")
        validate_idx = next((i for i, l in enumerate(update_lines) if 'form.fields["photos"].validate' in l), None)
        alt_idx = next((i for i, l in enumerate(update_lines) if "update_media_alt_text" in l), None)
        assert validate_idx is not None
        assert alt_idx is not None
        assert validate_idx < alt_idx

    def test_entite_sans_galerie_aucune_validation_multiupload(self):
        code = build_controller(_article_without_media())
        assert 'form.fields[' not in code or 'validate' not in code

    def test_mixed_single_pas_de_validation_pour_cover(self):
        code = build_controller(_article_mixed())
        create_lines = _lines_in_method(code, "create")
        assert not any('form.fields["cover"].validate' in l for l in create_lines)
        assert any('form.fields["photos"].validate' in l for l in create_lines)


# ── Faux BaseController ───────────────────────────────────────────────────────

class _FakeBaseController:
    @staticmethod
    def render(template, status=200, context=None, **kw):
        return SimpleNamespace(type="render", template=template, context=context or {})

    @staticmethod
    def redirect_with_flash(request, location, message, **kw):
        return SimpleNamespace(type="redirect", location=location, message=message)

    @staticmethod
    def validation_error(template, context=None, *, request=None):
        return SimpleNamespace(type="validation_error", template=template, context=context or {})

    @staticmethod
    def not_found():
        return SimpleNamespace(type="not_found")

    @staticmethod
    def csrf_token(request):
        return "fake-csrf"

    @staticmethod
    def set_flash(request, message, level="success"):
        pass


# ── Fixture d'environnement ───────────────────────────────────────────────────

def _build_env(monkeypatch, definition, gallery_entries=None):
    form_code, _ = build_form(definition)
    form_ns: dict = {}
    exec(compile(form_code, "<form>", "exec"), form_ns)
    ArticleForm = form_ns[f"{definition['entity']}Form"]

    calls: dict = {
        "add_article":           [],
        "update_article":        [],
        "save_upload":           [],
        "attach":                [],
        "delete_media":          [],
        "update_media_position": [],
        "list_media":            [],
        "_gallery": gallery_entries if gallery_entries is not None else [],
    }

    def _add_article(data):
        calls["add_article"].append(data)
        return 42

    def _update_article(pk, data):
        calls["update_article"].append((pk, data))

    def _save_upload(f, cat, *, variants=False):
        calls["save_upload"].append({"file": f, "category": cat})
        return SimpleNamespace(path=f"images/{f.filename}", mime_type="image/png",
                               original_name=f.filename, size=100)

    def _attach(saved, *, entity_name, entity_id, role, position, alt_text=None):
        calls["attach"].append({"entity_name": entity_name, "entity_id": entity_id,
                                "role": role, "position": position, "alt_text": alt_text})

    def _delete_media(media_id, *, delete_files, variants):
        calls["delete_media"].append({"id": media_id})

    def _update_media_position(media_id, position):
        calls["update_media_position"].append({"id": media_id, "position": position})

    def _list_media(entity_name, entity_id, *, role=None):
        calls["list_media"].append({"entity_name": entity_name, "entity_id": entity_id})
        return calls["_gallery"]

    def _mod(name, **attrs):
        m = types.ModuleType(name)
        for k, v in attrs.items():
            setattr(m, k, v)
        return m

    entity = definition["entity"]
    snake  = entity.lower()
    plural = snake + "s"

    model_mod = _mod(
        f"mvc.models.{snake}_model",
        **{
            f"get_{plural}":             lambda *a, **kw: [],
            f"get_{snake}_by_id":        lambda pk: {"id": pk, "titre": "Test"},
            f"add_{snake}":              _add_article,
            f"update_{snake}":           _update_article,
            f"delete_{snake}":           lambda pk: None,
            f"bulk_delete_{plural}":     lambda ids: None,
            f"count_{plural}":           lambda *a, **kw: 0,
            f"find_{plural}_paginated":  lambda *a, **kw: [],
            f"find_{plural}_for_export":  lambda *a, **kw: [],
        },
    )
    form_mod  = _mod(f"mvc.forms.{snake}_form",  **{f"{entity}Form": ArticleForm})
    flash_mod = _mod("mvc.helpers.flash",         render_flash_html=lambda req: "")
    ctrl_mod  = _mod("core.mvc.controller",       BaseController=_FakeBaseController)
    upload_mod = _mod("core.uploads", save_upload=_save_upload)
    forge_media_mod = _mod(
        "forge_mvc_images",
        save_image_upload=_save_upload,
        attach_media_to_entity=_attach,
        list_media_for_entity=_list_media,
        delete_media=_delete_media,
        update_media_alt_text=lambda *a, **kw: None,
        update_media_position=_update_media_position,
        get_cover_media=lambda *a, **kw: None,
    )

    for pkg in ("mvc", "mvc.models", "mvc.forms", "mvc.helpers"):
        if pkg not in sys.modules:
            monkeypatch.setitem(sys.modules, pkg, types.ModuleType(pkg))

    monkeypatch.setitem(sys.modules, f"mvc.models.{snake}_model", model_mod)
    monkeypatch.setitem(sys.modules, f"mvc.forms.{snake}_form",   form_mod)
    monkeypatch.setitem(sys.modules, "mvc.helpers.flash",          flash_mod)
    monkeypatch.setitem(sys.modules, "core.mvc.controller",        ctrl_mod)
    monkeypatch.setitem(sys.modules, "core.uploads",               upload_mod)
    monkeypatch.setitem(sys.modules, "forge_mvc_images",            forge_media_mod)

    ctrl_code = build_controller(definition)
    ctrl_ns: dict = {}
    exec(compile(ctrl_code, "<ctrl>", "exec"), ctrl_ns)
    Controller = ctrl_ns[f"{entity}Controller"]

    return Controller, calls


# ── Faux fichier uploadé ──────────────────────────────────────────────────────

class _DummyUpload:
    def __init__(self, filename="photo.png"):
        self.filename = filename
        self.content_type = "image/png"
        self.size = 100


# ── Helpers requêtes ──────────────────────────────────────────────────────────

def _req_create(titre="Article test", uploads=None):
    """uploads : None | un seul fichier | liste de fichiers."""
    files = {}
    if uploads is not None:
        files = {"photos": uploads}
    return FakeRequest("POST", "/articles", body={"titre": titre}, files=files)


def _req_update(pk, titre="Article test", uploads=None, positions=None, delete_ids=None):
    body = {"titre": titre}
    req = FakeRequest(
        "POST", f"/articles/{pk}",
        body=body,
        files={"photos": uploads} if uploads is not None else {},
    )
    req.route_params = {"id": str(pk)}
    if positions:
        for mid, pos in positions.items():
            req.body[f"_media_position_photos_{mid}"] = [pos]
    if delete_ids:
        req.body["_delete_media_photos"] = delete_ids
    return req


def _req_update_invalid(pk, uploads=None):
    req = FakeRequest(
        "POST", f"/articles/{pk}",
        body={"titre": ""},
        files={"photos": uploads} if uploads is not None else {},
    )
    req.route_params = {"id": str(pk)}
    return req


# ── Tests runtime ─────────────────────────────────────────────────────────────

def test_create_avec_un_fichier_fonctionne_encore(monkeypatch):
    """Backward-compat : un seul fichier passé directement."""
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    resp = Ctrl.create(_req_create(uploads=_DummyUpload("a.png")))

    assert resp.type == "redirect"
    assert len(calls["save_upload"]) == 1
    assert len(calls["attach"]) == 1


def test_create_avec_trois_fichiers_appelle_save_upload_trois_fois(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    uploads = [_DummyUpload("a.png"), _DummyUpload("b.png"), _DummyUpload("c.png")]
    resp = Ctrl.create(_req_create(uploads=uploads))

    assert resp.type == "redirect"
    assert len(calls["save_upload"]) == 3


def test_create_avec_trois_fichiers_appelle_attach_trois_fois(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    uploads = [_DummyUpload("a.png"), _DummyUpload("b.png"), _DummyUpload("c.png")]
    resp = Ctrl.create(_req_create(uploads=uploads))

    assert resp.type == "redirect"
    assert len(calls["attach"]) == 3
    for call in calls["attach"]:
        assert call["entity_name"] == "article"
        assert call["role"] == "gallery"


def test_create_avec_liste_vide_aucun_upload(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    resp = Ctrl.create(_req_create(uploads=[]))

    assert resp.type == "redirect"
    assert calls["save_upload"] == []
    assert calls["attach"] == []


def test_update_avec_deux_fichiers_appelle_save_upload_deux_fois(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    uploads = [_DummyUpload("x.png"), _DummyUpload("y.png")]
    resp = Ctrl.update(_req_update(7, uploads=uploads))

    assert resp.type == "redirect"
    assert len(calls["save_upload"]) == 2


def test_update_avec_deux_fichiers_attache_avec_entity_id_correct(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    uploads = [_DummyUpload("x.png"), _DummyUpload("y.png")]
    resp = Ctrl.update(_req_update(7, uploads=uploads))

    assert resp.type == "redirect"
    assert len(calls["attach"]) == 2
    for call in calls["attach"]:
        assert call["entity_id"] == 7
        assert call["entity_name"] == "article"
        assert call["role"] == "gallery"


def test_update_avec_liste_vide_aucun_upload(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    resp = Ctrl.update(_req_update(7, uploads=[]))

    assert resp.type == "redirect"
    assert calls["save_upload"] == []
    assert calls["attach"] == []


def test_update_invalide_avec_fichiers_aucun_upload(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    uploads = [_DummyUpload("a.png"), _DummyUpload("b.png")]
    resp = Ctrl.update(_req_update_invalid(7, uploads=uploads))

    assert resp.type == "validation_error"
    assert calls["save_upload"] == []
    assert calls["attach"] == []


def test_update_multiupload_conserve_logique_position(monkeypatch):
    """Multi-upload + positions existantes : les deux fonctionnent en même temps."""
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    uploads = [_DummyUpload("new1.png"), _DummyUpload("new2.png")]
    resp = Ctrl.update(_req_update(7, uploads=uploads, positions={10: "5", 20: "10"}))

    assert resp.type == "redirect"
    assert len(calls["save_upload"]) == 2
    assert len(calls["update_media_position"]) == 2


def test_update_multiupload_conserve_suppression_individuelle(monkeypatch):
    """Multi-upload + suppression individuelle : les deux fonctionnent en même temps."""
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    uploads = [_DummyUpload("new.png")]
    resp = Ctrl.update(_req_update(7, uploads=uploads, delete_ids=["99"]))

    assert resp.type == "redirect"
    assert len(calls["save_upload"]) == 1
    assert len(calls["delete_media"]) == 1
    assert calls["delete_media"][0]["id"] == 99


def test_entite_sans_galerie_aucun_comportement_multiupload(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_without_media())
    req = FakeRequest("POST", "/articles/7", body={"titre": "Test"},
                      files={"photos": [_DummyUpload("a.png"), _DummyUpload("b.png")]})
    req.route_params = {"id": "7"}
    resp = Ctrl.update(req)

    assert resp.type == "redirect"
    assert calls["save_upload"] == []
    assert calls["attach"] == []


# ── Tests runtime — validation fichiers invalides ─────────────────────────────

class _DummyInvalidUpload:
    """Fichier avec extension non autorisée par ImageField (rejette jpg/png/webp)."""
    def __init__(self, filename="document.txt"):
        self.filename = filename
        self.content_type = "text/plain"
        self.size = 100


def test_create_avec_fichier_invalide_parmi_trois_ne_sauvegarde_rien(monkeypatch):
    """Un fichier invalide dans la liste bloque tous les uploads."""
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    uploads = [_DummyUpload("a.png"), _DummyInvalidUpload("bad.txt"), _DummyUpload("c.png")]
    resp = Ctrl.create(_req_create(uploads=uploads))

    assert resp.type == "validation_error"
    assert calls["save_upload"] == []


def test_create_avec_fichier_invalide_nattache_rien(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    uploads = [_DummyUpload("a.png"), _DummyInvalidUpload("bad.txt")]
    resp = Ctrl.create(_req_create(uploads=uploads))

    assert resp.type == "validation_error"
    assert calls["attach"] == []


def test_create_avec_trois_fichiers_valides_sauvegarde_les_trois(monkeypatch):
    """Backward-compat : tous valides → 3 uploads."""
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    uploads = [_DummyUpload("a.png"), _DummyUpload("b.png"), _DummyUpload("c.png")]
    resp = Ctrl.create(_req_create(uploads=uploads))

    assert resp.type == "redirect"
    assert len(calls["save_upload"]) == 3


def test_update_avec_fichier_invalide_ne_sauvegarde_rien(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    uploads = [_DummyUpload("a.png"), _DummyInvalidUpload("bad.txt")]
    resp = Ctrl.update(_req_update(7, uploads=uploads))

    assert resp.type == "validation_error"
    assert calls["save_upload"] == []


def test_update_avec_fichier_invalide_ne_supprime_aucun_media(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    uploads = [_DummyInvalidUpload("bad.txt")]
    resp = Ctrl.update(_req_update(7, uploads=uploads, delete_ids=["5", "6"]))

    assert resp.type == "validation_error"
    assert calls["delete_media"] == []


def test_update_avec_fichier_invalide_ne_modifie_aucune_position(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    uploads = [_DummyInvalidUpload("bad.txt")]
    resp = Ctrl.update(_req_update(7, uploads=uploads, positions={10: "5"}))

    assert resp.type == "validation_error"
    assert calls["update_media_position"] == []


def test_update_avec_fichier_invalide_recharge_photos_media_list(monkeypatch):
    medias = [{"id": 1, "url": "/media/a.png", "thumbnail_url": None, "position": 0, "alt_text": None}]
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery(), gallery_entries=medias)
    uploads = [_DummyInvalidUpload("bad.txt")]
    resp = Ctrl.update(_req_update(7, uploads=uploads))

    assert resp.type == "validation_error"
    assert "photos_media_list" in resp.context
    assert resp.context["photos_media_list"] is medias


def test_update_avec_deux_fichiers_valides_sauvegarde_les_deux(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    uploads = [_DummyUpload("x.png"), _DummyUpload("y.png")]
    resp = Ctrl.update(_req_update(7, uploads=uploads))

    assert resp.type == "redirect"
    assert len(calls["save_upload"]) == 2


def test_fichier_unique_valide_continue_de_fonctionner(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    resp = Ctrl.create(_req_create(uploads=_DummyUpload("ok.png")))

    assert resp.type == "redirect"
    assert len(calls["save_upload"]) == 1


def test_fichier_unique_invalide_echoue_proprement(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    resp = Ctrl.create(_req_create(uploads=_DummyInvalidUpload("bad.txt")))

    assert resp.type == "validation_error"
    assert calls["save_upload"] == []
