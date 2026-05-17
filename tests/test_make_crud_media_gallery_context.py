"""Tests galerie en lecture — MEDIA-GALLERY-CONTEXT-001.

Vérifie que le contrôleur généré par make:crud expose correctement
le contexte galerie (list_media_for_entity) pour les médias déclarés
multiple=true dans show(), edit() et update() invalide.

Limites : lecture seule. Pas de multi-upload, pas d'ordre manuel,
pas de suppression individuelle depuis galerie.
"""
from __future__ import annotations

import sys
import types
from types import SimpleNamespace


from forge_cli.entities.make_crud import build_controller, build_form, build_show_view, build_form_view
from forge_cli.entities.validation import normalize_entity_definition
from tests.fake_request import FakeRequest


# ── Entités de référence ──────────────────────────────────────────────────────

def _article_with_gallery():
    return normalize_entity_definition(
        {
            "format_version": 1,
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
            "format_version": 1,
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
            "format_version": 1,
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


# ── Helpers d'extraction de blocs ─────────────────────────────────────────────

def _lines_in_method(code: str, method_name: str) -> list[str]:
    """Extrait les lignes de la méthode nommée dans le code généré."""
    lines = code.split("\n")
    result = []
    inside = False
    for line in lines:
        if f"def {method_name}(request)" in line:
            inside = True
            continue
        if inside:
            if line.startswith("    def ") and method_name not in line:
                break
            result.append(line)
    return result


def _update_invalid_block(code: str) -> list[str]:
    """Extrait les lignes du bloc if not form.is_valid() dans update."""
    lines = code.split("\n")
    in_update = False
    in_invalid = False
    block: list[str] = []
    for line in lines:
        if "def update(request)" in line:
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


# ── Tests de génération ───────────────────────────────────────────────────────

class TestGalleryContextGeneration:

    def test_show_appelle_list_media_pour_multiple(self):
        code = build_controller(_article_with_gallery())
        show_lines = _lines_in_method(code, "show")
        assert any('list_media_for_entity("article", id, role="gallery")' in l for l in show_lines)

    def test_show_context_contient_photos_media_list(self):
        code = build_controller(_article_with_gallery())
        show_lines = _lines_in_method(code, "show")
        assert any('"photos_media_list": photos_media_list' in l for l in show_lines)

    def test_edit_appelle_list_media_pour_multiple(self):
        code = build_controller(_article_with_gallery())
        edit_lines = _lines_in_method(code, "edit")
        assert any('list_media_for_entity("article", id, role="gallery")' in l for l in edit_lines)

    def test_edit_context_contient_photos_media_list(self):
        code = build_controller(_article_with_gallery())
        edit_lines = _lines_in_method(code, "edit")
        assert any('"photos_media_list": photos_media_list' in l for l in edit_lines)

    def test_update_invalide_recharge_photos_media_list(self):
        code = build_controller(_article_with_gallery())
        block = _update_invalid_block(code)
        assert any('photos_media_list = list_media_for_entity("article", id, role="gallery")' in l
                   for l in block)

    def test_update_invalide_context_contient_photos_media_list(self):
        code = build_controller(_article_with_gallery())
        block = _update_invalid_block(code)
        assert any('"photos_media_list": photos_media_list' in l for l in block)

    def test_entite_sans_multiple_aucune_variable_list(self):
        code = build_controller(_article_without_media())
        assert "_media_list" not in code

    def test_single_utilise_get_cover_media_pas_list(self):
        """media multiple=False continue d'utiliser get_cover_media dans show/edit."""
        code = build_controller(_article_mixed())
        show_lines = _lines_in_method(code, "show")
        assert any("get_cover_media" in l and "cover" in l for l in show_lines)
        assert any("list_media_for_entity" in l and "photos" in l for l in show_lines)

    def test_mixed_edit_contient_les_deux_variables(self):
        code = build_controller(_article_mixed())
        edit_lines = _lines_in_method(code, "edit")
        assert any("cover_media" in l and "get_cover_media" in l for l in edit_lines)
        assert any("photos_media_list" in l and "list_media_for_entity" in l for l in edit_lines)

    def test_nom_variable_stable_photos_media_list(self):
        """La variable de contexte doit être exactement {name}_media_list."""
        code = build_controller(_article_with_gallery())
        assert "photos_media_list" in code

    def test_show_view_affiche_galerie_multiple(self):
        html = build_show_view(_article_with_gallery())
        assert "photos_media_list" in html
        assert "{% for _m in photos_media_list %}" in html

    def test_form_view_affiche_galerie_avec_suppression_individuelle(self):
        html = build_form_view(_article_with_gallery())
        assert "photos_media_list" in html
        assert "{% for _m in photos_media_list %}" in html
        # Chaque item de galerie a une checkbox individuelle
        assert 'name="_delete_media_photos"' in html
        assert 'value="{{ _m.id }}"' in html


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
    """
    Génère et exec ArticleForm + ArticleController.
    gallery_entries : valeur retournée par list_media_for_entity.
    Retourne (Controller, calls).
    """
    form_code, _ = build_form(definition)
    form_ns: dict = {}
    exec(compile(form_code, "<form>", "exec"), form_ns)
    ArticleForm = form_ns[f"{definition['entity']}Form"]

    calls: dict = {
        "list_media":   [],
        "save_upload":  [],
        "delete_media": [],
        "get_cover":    [],
        "_gallery": gallery_entries if gallery_entries is not None else [],
    }

    def _list_media(entity_name, entity_id, *, role=None):
        calls["list_media"].append({"entity_name": entity_name, "entity_id": entity_id, "role": role})
        return calls["_gallery"]

    def _save_upload(f, cat, *, variants=False):
        calls["save_upload"].append(f)
        return SimpleNamespace(path=f"images/{f.filename}", mime_type="image/png")

    def _delete_media(media_id, *, delete_files, variants):
        calls["delete_media"].append(media_id)

    def _get_cover(entity_name, entity_id, *, role):
        calls["get_cover"].append({"entity_name": entity_name, "entity_id": entity_id, "role": role})
        return None

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
            f"get_{snake}_by_id":        lambda pk: {"id": pk, "titre": "Article test"},
            f"add_{snake}":              lambda data: 1,
            f"update_{snake}":           lambda pk, data: None,
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
        "forge_mvc_media",
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
    monkeypatch.setitem(sys.modules, "forge_mvc_media",            forge_media_mod)

    ctrl_code = build_controller(definition)
    ctrl_ns: dict = {}
    exec(compile(ctrl_code, "<ctrl>", "exec"), ctrl_ns)
    Controller = ctrl_ns[f"{entity}Controller"]

    return Controller, calls


# ── Helpers requêtes ──────────────────────────────────────────────────────────

def _req_show(pk):
    req = FakeRequest("GET", f"/articles/{pk}")
    req.route_params = {"id": str(pk)}
    return req


def _req_edit(pk):
    req = FakeRequest("GET", f"/articles/{pk}/edit")
    req.route_params = {"id": str(pk)}
    return req


def _req_update_invalid(pk):
    req = FakeRequest("POST", f"/articles/{pk}", body={"titre": ""})
    req.route_params = {"id": str(pk)}
    return req


# ── Tests runtime ─────────────────────────────────────────────────────────────

def test_show_appelle_list_media_avec_bon_role(monkeypatch):
    medias = [{"id": 1, "url": "/media/a.png", "thumbnail_url": None}]
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery(), gallery_entries=medias)
    resp = Ctrl.show(_req_show(7))

    assert resp.type == "render"
    assert any(c["entity_name"] == "article" and c["entity_id"] == 7 and c["role"] == "gallery"
               for c in calls["list_media"])


def test_show_transmet_photos_media_list_au_contexte(monkeypatch):
    medias = [{"id": 1, "url": "/media/a.png", "thumbnail_url": None}]
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery(), gallery_entries=medias)
    resp = Ctrl.show(_req_show(7))

    assert resp.type == "render"
    assert "photos_media_list" in resp.context
    assert resp.context["photos_media_list"] is medias


def test_edit_transmet_photos_media_list_au_contexte(monkeypatch):
    medias = [{"id": 2, "url": "/media/b.png", "thumbnail_url": None}]
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery(), gallery_entries=medias)
    resp = Ctrl.edit(_req_edit(7))

    assert resp.type == "render"
    assert "photos_media_list" in resp.context
    assert resp.context["photos_media_list"] is medias


def test_update_invalide_recharge_photos_media_list(monkeypatch):
    medias = [{"id": 3, "url": "/media/c.png", "thumbnail_url": None}]
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery(), gallery_entries=medias)
    resp = Ctrl.update(_req_update_invalid(7))

    assert resp.type == "validation_error"
    assert "photos_media_list" in resp.context
    assert resp.context["photos_media_list"] is medias


def test_update_invalide_ne_fait_ni_upload_ni_delete(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    Ctrl.update(_req_update_invalid(7))

    assert calls["save_upload"] == []
    assert calls["delete_media"] == []


def test_show_liste_vide_contexte_present(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery(), gallery_entries=[])
    resp = Ctrl.show(_req_show(7))

    assert resp.type == "render"
    assert "photos_media_list" in resp.context
    assert resp.context["photos_media_list"] == []


def test_entite_sans_galerie_aucun_appel_list_media_hors_destroy(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_without_media())

    Ctrl.show(_req_show(7))
    Ctrl.edit(_req_edit(7))
    Ctrl.update(_req_update_invalid(7))

    assert calls["list_media"] == []
