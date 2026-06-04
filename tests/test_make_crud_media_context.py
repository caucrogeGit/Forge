"""Tests runtime — contexte média dans edit() et update() invalide (MEDIA-CONTEXT-001).

Vérifie que le code généré par make:crud :
- transmet le contexte média attendu à edit() ;
- préserve ce contexte après une erreur de validation dans update().
"""
from __future__ import annotations

import sys
import types
from types import SimpleNamespace


from forge_cli.entities.make_crud import build_controller, build_form
from forge_cli.entities.validation import normalize_entity_definition
from tests.fake_request import FakeRequest


# ── Entités de référence ──────────────────────────────────────────────────────

def _article_with_media():
    return normalize_entity_definition(
        {
            "entity": "Article",
            "table": "article",
            "description": "",
            "fields": [
                {"name": "id",    "sql_type": "INT",         "primary_key": True, "auto_increment": True},
                {"name": "titre", "sql_type": "VARCHAR(120)", "constraints": {"not_empty": True}},
            ],
            "media": [
                {
                    "name": "photo",
                    "field": "image",
                    "role": "cover",
                    "variants": False,
                    "multiple": False,
                    "required": False,
                    "label": "Photo",
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
                {"name": "id",    "sql_type": "INT",         "primary_key": True, "auto_increment": True},
                {"name": "titre", "sql_type": "VARCHAR(120)", "constraints": {"not_empty": True}},
            ],
        },
        source="test.json",
    )


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


# ── Fixture principale ────────────────────────────────────────────────────────

def _build_context_env(monkeypatch, definition, cover_media=None):
    """
    Génère et exec ArticleForm + ArticleController.
    Retourne (Controller, calls).
    cover_media : valeur retournée par get_cover_media.
    """
    form_code, _ = build_form(definition)
    form_ns: dict = {}
    exec(compile(form_code, "<form>", "exec"), form_ns)
    ArticleForm = form_ns[f"{definition['entity']}Form"]

    calls: dict = {
        "get_cover":     [],
        "save_upload":   [],
        "delete_media":  [],
        "list_media":    [],
        "update_entity": [],
        "_cover_media":  cover_media,
    }

    def _get_cover(entity_name, entity_id, *, role):
        calls["get_cover"].append({"entity_name": entity_name, "entity_id": entity_id, "role": role})
        return calls["_cover_media"]

    def _save_upload(f, cat, *, variants=False):
        calls["save_upload"].append(f)
        return SimpleNamespace(path=f"images/{f.filename}", mime_type="image/png")

    def _delete_media(media_id, *, delete_files, variants):
        calls["delete_media"].append(media_id)

    def _list_media(entity_name, entity_id, *, role=None):
        calls["list_media"].append({"entity_name": entity_name, "entity_id": entity_id})
        return []

    def _update_entity(pk, data):
        calls["update_entity"].append((pk, data))

    def _mod(name, **attrs):
        m = types.ModuleType(name)
        for k, v in attrs.items():
            setattr(m, k, v)
        return m

    entity  = definition["entity"]
    snake   = entity.lower()
    plural  = snake + "s"

    existing_record = {"id": 7, "titre": "Article existant"}

    model_mod = _mod(
        f"mvc.models.{snake}_model",
        **{
            f"get_{plural}":             lambda *a, **kw: [],
            f"get_{snake}_by_id":        lambda pk: existing_record,
            f"add_{snake}":              lambda data: 1,
            f"update_{snake}":           _update_entity,
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
        attach_media_to_entity=lambda *a, **kw: None,
        list_media_for_entity=_list_media,
        delete_media=_delete_media,
        update_media_alt_text=lambda *a, **kw: None,
        update_media_position=lambda *a, **kw: None,
        get_cover_media=_get_cover,
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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _req_edit(pk):
    req = FakeRequest("GET", f"/articles/{pk}")
    req.route_params = {"id": str(pk)}
    return req


def _req_update(pk, titre="Article test", upload=None):
    body = {"titre": titre}
    req = FakeRequest("POST", f"/articles/{pk}", body=body,
                      files={"photo": upload} if upload else {})
    req.route_params = {"id": str(pk)}
    return req


# ── Tests runtime ─────────────────────────────────────────────────────────────

# 1. edit(7) appelle get_cover_media avec entity_name="article" et entity_id=7

def test_edit_appelle_get_cover_media(monkeypatch):
    fake_media = SimpleNamespace(url="/media/images/photo.png", thumbnail_url=None)
    Ctrl, calls = _build_context_env(monkeypatch, _article_with_media(), cover_media=fake_media)
    resp = Ctrl.edit(_req_edit(7))

    assert resp.type == "render"
    assert len(calls["get_cover"]) >= 1
    assert calls["get_cover"][0]["entity_name"] == "article"
    assert calls["get_cover"][0]["entity_id"] == 7
    assert calls["get_cover"][0]["role"] == "cover"


# 2. edit(7) transmet photo_media à la vue

def test_edit_transmet_photo_media_au_contexte(monkeypatch):
    fake_media = SimpleNamespace(url="/media/images/photo.png", thumbnail_url=None)
    Ctrl, calls = _build_context_env(monkeypatch, _article_with_media(), cover_media=fake_media)
    resp = Ctrl.edit(_req_edit(7))

    assert resp.type == "render"
    assert "photo_media" in resp.context
    assert resp.context["photo_media"] is fake_media


# 3. update(7) invalide (titre vide) retourne validation_error sans save_upload

def test_update_invalide_retourne_validation_error_sans_upload(monkeypatch):
    Ctrl, calls = _build_context_env(monkeypatch, _article_with_media())
    resp = Ctrl.update(_req_update(7, titre=""))  # titre vide → invalide

    assert resp.type == "validation_error"
    assert calls["save_upload"] == []


# 4. update(7) invalide transmet photo_media au contexte

def test_update_invalide_transmet_photo_media(monkeypatch):
    fake_media = SimpleNamespace(url="/media/images/photo.png", thumbnail_url=None)
    Ctrl, calls = _build_context_env(monkeypatch, _article_with_media(), cover_media=fake_media)
    resp = Ctrl.update(_req_update(7, titre=""))

    assert resp.type == "validation_error"
    assert "photo_media" in resp.context
    assert resp.context["photo_media"] is fake_media


# 5. update(7) invalide n'appelle pas delete_media

def test_update_invalide_ne_supprime_aucun_media(monkeypatch):
    Ctrl, calls = _build_context_env(monkeypatch, _article_with_media())
    Ctrl.update(_req_update(7, titre=""))

    assert calls["delete_media"] == []
    assert calls["list_media"] == []


# 6. entité sans média : edit() fonctionne sans appel média

def test_edit_sans_media_fonctionne_sans_appel_media(monkeypatch):
    Ctrl, calls = _build_context_env(monkeypatch, _article_without_media())
    resp = Ctrl.edit(_req_edit(7))

    assert resp.type == "render"
    assert calls["get_cover"] == []
    assert "photo_media" not in resp.context


# 7. entité sans média : update() invalide fonctionne sans appel média

def test_update_invalide_sans_media_fonctionne(monkeypatch):
    Ctrl, calls = _build_context_env(monkeypatch, _article_without_media())
    resp = Ctrl.update(_req_update(7, titre=""))

    assert resp.type == "validation_error"
    assert calls["get_cover"] == []
    assert calls["save_upload"] == []
