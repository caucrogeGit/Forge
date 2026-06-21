"""Tests ajout galerie — MEDIA-GALLERY-ADD-001.

Vérifie que le contrôleur généré par make:crud permet d'ajouter un
média à une galerie (multiple=true) en mode append-only :
- create() sauvegarde et attache le média à la nouvelle entité ;
- update() ajoute le média sans supprimer les existants ;
- update() invalide n'effectue aucun upload.

Limites : un seul fichier par soumission, append-only, pas de
suppression individuelle, pas d'ordre manuel.
"""
from __future__ import annotations

import sys
import types
from types import SimpleNamespace


from forge_cli.entities.make_crud import build_controller, build_form, build_form_view
from forge_cli.entities.validation import normalize_entity_definition
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
    """Entité avec cover (single) + photos (multiple)."""
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

class TestGalleryAddGeneration:

    def test_form_contient_input_file_pour_multiple(self):
        html = build_form_view(_article_with_gallery())
        assert 'name="photos"' in html
        assert 'type="file"' in html

    def test_create_contient_save_upload_pour_multiple(self):
        code = build_controller(_article_with_gallery())
        create_lines = _lines_in_method(code, "create")
        # CORE-SAVEUPLOAD-GENERIC-CLEANUP : galerie d'images → save_image_upload.
        assert any("save_image_upload" in l and "photos" in l for l in create_lines)

    def test_create_contient_attach_pour_multiple(self):
        code = build_controller(_article_with_gallery())
        create_lines = _lines_in_method(code, "create")
        assert any('attach_media_to_entity' in l and 'role="gallery"' in l for l in create_lines)

    def test_update_contient_save_upload_append_only(self):
        code = build_controller(_article_with_gallery())
        update_lines = _lines_in_method(code, "update")
        assert any("save_image_upload" in l and "photos" in l for l in update_lines)

    def test_update_contient_attach_pour_multiple(self):
        code = build_controller(_article_with_gallery())
        update_lines = _lines_in_method(code, "update")
        assert any('attach_media_to_entity' in l and 'role="gallery"' in l for l in update_lines)

    def test_update_galerie_suppression_individuelle_pas_remplacement(self):
        code = build_controller(_article_with_gallery())
        update_lines = _lines_in_method(code, "update")
        # Suppression individuelle présente via _delete_media_photos
        assert any("delete_media" in l for l in update_lines)
        # Pas de boucle de remplacement total (for _old in list_media_for_entity)
        assert not any("for _old in list_media_for_entity" in l for l in update_lines)

    def test_update_pas_de_for_old_pour_galerie(self):
        code = build_controller(_article_with_gallery())
        update_lines = _lines_in_method(code, "update")
        assert not any("for _old in list_media_for_entity" in l for l in update_lines)

    def test_photos_exclu_de_sql_data(self):
        code = build_controller(_article_with_gallery())
        assert '"photos"' in code
        assert '_media_keys = {"photos"}' in code or "_media_keys" in code

    def test_entite_sans_galerie_update_inchange(self):
        code = build_controller(_article_without_media())
        assert "save_upload" not in code
        assert "attach_media_to_entity" not in code

    def test_mixed_single_garde_logique_remplacement(self):
        code = build_controller(_article_mixed())
        update_lines = _lines_in_method(code, "update")
        # cover (single) a la logique de remplacement
        assert any("for _old in list_media_for_entity" in l and "cover" in l
                   for l in update_lines)

    def test_mixed_multiple_utilise_append_sans_delete(self):
        code = build_controller(_article_mixed())
        update_lines = _lines_in_method(code, "update")
        # photos (multiple) a l'attach mais pas le for _old
        assert any("attach_media_to_entity" in l and "gallery" in l for l in update_lines)
        assert not any("for _old in list_media_for_entity" in l and "gallery" in l
                       for l in update_lines)


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
        "add_article":    [],
        "update_article": [],
        "save_upload":    [],
        "attach":         [],
        "delete_media":   [],
        "list_media":     [],
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
        calls["delete_media"].append(media_id)

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
        update_media_position=lambda *a, **kw: None,
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

def _req_create(titre="Article test", upload=None):
    return FakeRequest(
        "POST", "/articles",
        body={"titre": titre},
        files={"photos": upload} if upload else {},
    )


def _req_update(pk, titre="Article test", upload=None):
    req = FakeRequest(
        "POST", f"/articles/{pk}",
        body={"titre": titre},
        files={"photos": upload} if upload else {},
    )
    req.route_params = {"id": str(pk)}
    return req


def _req_update_invalid(pk, upload=None):
    req = FakeRequest(
        "POST", f"/articles/{pk}",
        body={"titre": ""},
        files={"photos": upload} if upload else {},
    )
    req.route_params = {"id": str(pk)}
    return req


# ── Tests runtime ─────────────────────────────────────────────────────────────

def test_create_avec_fichier_galerie_appelle_save_upload(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    upload = _DummyUpload("photo.png")
    resp = Ctrl.create(_req_create(upload=upload))

    assert resp.type == "redirect"
    assert len(calls["save_upload"]) == 1
    assert calls["save_upload"][0]["file"] is upload


def test_create_avec_fichier_galerie_attache_a_entite(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    upload = _DummyUpload("photo.png")
    Ctrl.create(_req_create(upload=upload))

    assert len(calls["attach"]) == 1
    a = calls["attach"][0]
    assert a["entity_name"] == "article"
    assert a["entity_id"] == 42  # lastrowid retourné par le mock
    assert a["role"] == "gallery"


def test_create_sans_fichier_galerie_pas_upload(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    resp = Ctrl.create(_req_create(upload=None))

    assert resp.type == "redirect"
    assert calls["save_upload"] == []
    assert calls["attach"] == []
    assert len(calls["add_article"]) == 1


def test_update_avec_fichier_galerie_appelle_save_upload(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    upload = _DummyUpload("new.png")
    resp = Ctrl.update(_req_update(7, upload=upload))

    assert resp.type == "redirect"
    assert len(calls["save_upload"]) == 1
    assert calls["save_upload"][0]["file"] is upload


def test_update_avec_fichier_galerie_attache_a_entite(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    upload = _DummyUpload("new.png")
    Ctrl.update(_req_update(7, upload=upload))

    assert len(calls["attach"]) == 1
    a = calls["attach"][0]
    assert a["entity_name"] == "article"
    assert a["entity_id"] == 7
    assert a["role"] == "gallery"


def test_update_avec_fichier_galerie_ne_supprime_pas_existants(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery(),
                             gallery_entries=[{"id": 10}, {"id": 20}])
    upload = _DummyUpload("new.png")
    Ctrl.update(_req_update(7, upload=upload))

    assert calls["delete_media"] == []


def test_update_invalide_avec_fichier_aucun_upload(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    upload = _DummyUpload("photo.png")
    resp = Ctrl.update(_req_update_invalid(7, upload=upload))

    assert resp.type == "validation_error"
    assert calls["save_upload"] == []
    assert calls["attach"] == []


def test_update_invalide_recharge_photos_media_list(monkeypatch):
    medias = [{"id": 5, "url": "/media/x.png"}]
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery(), gallery_entries=medias)
    resp = Ctrl.update(_req_update_invalid(7))

    assert resp.type == "validation_error"
    assert "photos_media_list" in resp.context
    assert resp.context["photos_media_list"] is medias


def test_sql_data_ne_contient_pas_photos(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    upload = _DummyUpload("photo.png")
    Ctrl.create(_req_create(upload=upload))

    assert len(calls["add_article"]) == 1
    sql_data = calls["add_article"][0]
    assert "photos" not in sql_data
    assert "titre" in sql_data


def test_update_attach_position_vaut_zero_par_defaut(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    upload = _DummyUpload("new.png")
    Ctrl.update(_req_update(7, upload=upload))

    assert len(calls["attach"]) == 1
    assert calls["attach"][0]["position"] == 0
