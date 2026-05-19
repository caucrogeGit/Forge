"""Tests suppression individuelle galerie — MEDIA-GALLERY-DELETE-001.

Vérifie que le contrôleur généré par make:crud permet de supprimer
individuellement un média d'une galerie multiple=true :
- update() détecte _delete_media_{name} dans request.body ;
- appelle delete_media(id, delete_files=True, variants=True) pour chaque id ;
- conserve les autres médias de la galerie ;
- l'ajout append-only continue de fonctionner dans la même soumission ;
- update() invalide ne supprime rien.
"""
from __future__ import annotations

import sys
import types
from types import SimpleNamespace

import pytest

from forge_cli.entities.make_crud import build_controller, build_form, build_form_view
from forge_cli.entities.validation import normalize_entity_definition
from tests.fake_request import FakeRequest


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
        if f"def {method_name}(request)" in line:
            inside = True
            continue
        if inside:
            if line.startswith("    def ") and method_name not in line:
                break
            result.append(line)
    return result


# ── Tests de génération ───────────────────────────────────────────────────────

class TestGalleryDeleteGeneration:

    def test_form_html_affiche_checkbox_suppression_par_item(self):
        html = build_form_view(_article_with_gallery())
        assert 'name="_delete_media_photos"' in html

    def test_form_html_checkbox_value_est_id_media(self):
        html = build_form_view(_article_with_gallery())
        assert 'value="{{ _m.id }}"' in html

    def test_nom_champ_stable_delete_media_name(self):
        html = build_form_view(_article_with_gallery())
        # Le nom est exactement _delete_media_{name}
        assert 'name="_delete_media_photos"' in html
        assert 'name="_delete_media_photos_" ' not in html

    def test_update_detecte_delete_media_photos(self):
        code = build_controller(_article_with_gallery())
        update_lines = _lines_in_method(code, "update")
        assert any('_delete_media_photos' in l for l in update_lines)

    def test_update_appelle_delete_media_avec_delete_files_true(self):
        code = build_controller(_article_with_gallery())
        update_lines = _lines_in_method(code, "update")
        assert any("delete_media" in l and "delete_files=True" in l for l in update_lines)

    def test_update_appelle_delete_media_avec_variants_true(self):
        code = build_controller(_article_with_gallery())
        update_lines = _lines_in_method(code, "update")
        assert any("delete_media" in l and "variants=True" in l for l in update_lines)

    def test_update_invalide_pas_de_suppression_avant_validation(self):
        code = build_controller(_article_with_gallery())
        lines = code.split("\n")
        # Vérifier que delete_media apparaît APRÈS la validation (not in invalid block)
        in_update = False
        in_invalid = False
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
                # Sort du bloc invalide quand on trouve une ligne à 8 espaces
                if line.startswith("        ") and not line.startswith("            "):
                    in_invalid = False
            if in_invalid and "delete_media" in line:
                pytest.fail(f"delete_media dans le bloc invalide : {line}")

    def test_entite_sans_galerie_pas_de_delete_photos(self):
        code = build_controller(_article_without_media())
        assert "_delete_media_" not in code

    def test_mixed_single_conserve_logique_remplacement(self):
        code = build_controller(_article_mixed())
        update_lines = _lines_in_method(code, "update")
        assert any("for _old in list_media_for_entity" in l and "cover" in l
                   for l in update_lines)

    def test_mixed_multiple_suppression_individuelle(self):
        code = build_controller(_article_mixed())
        update_lines = _lines_in_method(code, "update")
        assert any('_delete_media_photos' in l for l in update_lines)
        assert not any("for _old in list_media_for_entity" in l and "photos" in l
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
        "update_article": [],
        "save_upload":    [],
        "attach":         [],
        "delete_media":   [],
        "list_media":     [],
        "_gallery": gallery_entries if gallery_entries is not None else [],
    }

    def _update_article(pk, data):
        calls["update_article"].append((pk, data))

    def _save_upload(f, cat, *, variants=False):
        calls["save_upload"].append({"file": f, "category": cat})
        return SimpleNamespace(path=f"images/{f.filename}", mime_type="image/png",
                               original_name=f.filename, size=100)

    def _attach(saved, *, entity_name, entity_id, role, position, alt_text=None):
        calls["attach"].append({"entity_name": entity_name, "entity_id": entity_id, "role": role})

    def _delete_media(media_id, *, delete_files, variants):
        calls["delete_media"].append({"id": media_id, "delete_files": delete_files,
                                      "variants": variants})

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
            f"add_{snake}":              lambda data: 1,
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
        "forge_mvc_media",
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
    monkeypatch.setitem(sys.modules, "forge_mvc_media",            forge_media_mod)

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

def _req_update(pk, titre="Article test", upload=None, delete_ids=None):
    """delete_ids : liste de chaînes représentant les ids à supprimer."""
    body = {"titre": titre}
    req = FakeRequest("POST", f"/articles/{pk}", body=body,
                      files={"photos": upload} if upload else {})
    req.route_params = {"id": str(pk)}
    if delete_ids:
        req.body["_delete_media_photos"] = delete_ids
    return req


def _req_update_invalid(pk, delete_ids=None):
    req = FakeRequest("POST", f"/articles/{pk}", body={"titre": ""})
    req.route_params = {"id": str(pk)}
    if delete_ids:
        req.body["_delete_media_photos"] = delete_ids
    return req


# ── Tests runtime ─────────────────────────────────────────────────────────────

def test_update_avec_un_id_supprime_ce_media(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    resp = Ctrl.update(_req_update(7, delete_ids=["12"]))

    assert resp.type == "redirect"
    assert len(calls["delete_media"]) == 1
    assert calls["delete_media"][0]["id"] == 12
    assert calls["delete_media"][0]["delete_files"] is True
    assert calls["delete_media"][0]["variants"] is True


def test_update_avec_plusieurs_ids_supprime_chaque_media(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    resp = Ctrl.update(_req_update(7, delete_ids=["12", "15"]))

    assert resp.type == "redirect"
    assert len(calls["delete_media"]) == 2
    deleted_ids = {c["id"] for c in calls["delete_media"]}
    assert deleted_ids == {12, 15}


def test_update_sans_suppression_aucun_delete(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    resp = Ctrl.update(_req_update(7))

    assert resp.type == "redirect"
    assert calls["delete_media"] == []


def test_update_suppression_et_ajout_dans_meme_soumission(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    upload = _DummyUpload("new.png")
    resp = Ctrl.update(_req_update(7, upload=upload, delete_ids=["12"]))

    assert resp.type == "redirect"
    assert len(calls["delete_media"]) == 1
    assert calls["delete_media"][0]["id"] == 12
    assert len(calls["save_upload"]) == 1
    assert len(calls["attach"]) == 1
    assert calls["attach"][0]["role"] == "gallery"


def test_update_invalide_aucune_suppression(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    resp = Ctrl.update(_req_update_invalid(7, delete_ids=["12"]))

    assert resp.type == "validation_error"
    assert calls["delete_media"] == []


def test_update_invalide_recharge_photos_media_list(monkeypatch):
    medias = [{"id": 12, "url": "/media/a.png"}]
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery(), gallery_entries=medias)
    resp = Ctrl.update(_req_update_invalid(7, delete_ids=["12"]))

    assert resp.type == "validation_error"
    assert "photos_media_list" in resp.context
    assert resp.context["photos_media_list"] is medias


def test_entite_sans_galerie_aucun_delete_appele(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_without_media())
    req = FakeRequest("POST", "/articles/7", body={"titre": "Test"})
    req.route_params = {"id": "7"}
    resp = Ctrl.update(req)

    assert resp.type == "redirect"
    assert calls["delete_media"] == []
