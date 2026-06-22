"""Tests destroy CRUD avec médias — MEDIA-DESTROY-001.

Vérifie que le contrôleur généré par make:crud supprime les médias liés
à l'entité lors de la suppression, via l'API média interne.
"""
from __future__ import annotations

import sys
import types
from types import SimpleNamespace

import pytest

from cli.entities.make_crud import build_controller, build_form
from cli.entities.validation import normalize_entity_definition
from forge_mvc_testing import FakeRequest


# ── Définitions d'entités ─────────────────────────────────────────────────────

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


def _hebergement_multiple_true():
    return normalize_entity_definition(
        {
            "entity": "Hebergement",
            "table": "hebergement",
            "description": "",
            "fields": [
                {"name": "id",  "sql_type": "INT",         "primary_key": True, "auto_increment": True},
                {"name": "nom", "sql_type": "VARCHAR(120)"},
            ],
            "media": [
                {"name": "cover", "field": "image", "role": "gallery", "multiple": True},
            ],
        },
        source="test.json",
    )


# ── Tests de génération ───────────────────────────────────────────────────────

class TestDestroyGenerationMedia:

    def test_avec_media_destroy_contient_list_media(self):
        code = build_controller(_article_with_media())
        lines = code.split("\n")
        in_destroy = False
        for line in lines:
            if "def destroy(request: Request)" in line:
                in_destroy = True
            elif line.startswith("    def ") and "destroy" not in line:
                in_destroy = False
            if in_destroy and "list_media_for_entity" in line:
                return
        pytest.fail("list_media_for_entity absent du bloc destroy")

    def test_avec_media_destroy_contient_delete_media(self):
        code = build_controller(_article_with_media())
        lines = code.split("\n")
        in_destroy = False
        for line in lines:
            if "def destroy(request: Request)" in line:
                in_destroy = True
            elif line.startswith("    def ") and "destroy" not in line:
                in_destroy = False
            if in_destroy and "delete_media" in line:
                return
        pytest.fail("delete_media absent du bloc destroy")

    def test_destroy_appelle_delete_media_avec_delete_files_true(self):
        code = build_controller(_article_with_media())
        lines = code.split("\n")
        in_destroy = False
        for line in lines:
            if "def destroy(request: Request)" in line:
                in_destroy = True
            elif line.startswith("    def ") and "destroy" not in line:
                in_destroy = False
            if in_destroy and "delete_media" in line:
                assert "delete_files=True" in line, f"delete_files=True absent : {line}"
                return
        pytest.fail("delete_media absent du bloc destroy")

    def test_destroy_utilise_le_bon_entity_name(self):
        code = build_controller(_article_with_media())
        lines = code.split("\n")
        in_destroy = False
        for line in lines:
            if "def destroy(request: Request)" in line:
                in_destroy = True
            elif line.startswith("    def ") and "destroy" not in line:
                in_destroy = False
            if in_destroy and "list_media_for_entity" in line:
                assert '"article"' in line, f"entity_name incorrect : {line}"
                return
        pytest.fail("list_media_for_entity absent du bloc destroy")

    def test_sans_media_destroy_sans_list_media(self):
        code = build_controller(_article_without_media())
        lines = code.split("\n")
        in_destroy = False
        for line in lines:
            if "def destroy(request: Request)" in line:
                in_destroy = True
            elif line.startswith("    def ") and "destroy" not in line:
                in_destroy = False
            if in_destroy and "list_media_for_entity" in line:
                pytest.fail(f"list_media_for_entity inattendu dans destroy sans media : {line}")

    def test_sans_media_destroy_appelle_delete_entity(self):
        code = build_controller(_article_without_media())
        lines = code.split("\n")
        in_destroy = False
        for line in lines:
            if "def destroy(request: Request)" in line:
                in_destroy = True
            elif line.startswith("    def ") and "destroy" not in line:
                in_destroy = False
            if in_destroy and "delete_article" in line:
                return
        pytest.fail("delete_article absent du bloc destroy")

    def test_multiple_true_destroy_contient_list_media(self):
        code = build_controller(_hebergement_multiple_true())
        lines = code.split("\n")
        in_destroy = False
        for line in lines:
            if "def destroy(request: Request)" in line:
                in_destroy = True
            elif line.startswith("    def ") and "destroy" not in line:
                in_destroy = False
            if in_destroy and "list_media_for_entity" in line:
                return
        pytest.fail("list_media_for_entity absent du destroy pour multiple=True")


# ── Fixture runtime ───────────────────────────────────────────────────────────

class _FakeBaseController:
    @staticmethod
    def render(template, status=200, context=None, **kw):
        return SimpleNamespace(type="render", template=template, context=context or {})

    @staticmethod
    def redirect_with_flash(request, location, message, **kw):
        return SimpleNamespace(type="redirect", location=location, message=message)

    @staticmethod
    def not_found():
        return SimpleNamespace(type="not_found")

    @staticmethod
    def csrf_token(request):
        return "fake-csrf"

    @staticmethod
    def set_flash(request, message, level="success"):
        pass

    @staticmethod
    def validation_error(template, context=None, *, request=None):
        return SimpleNamespace(type="validation_error", template=template, context=context or {})


def _build_env(monkeypatch, definition, media_entries=None):
    """
    Génère et exec ArticleForm + ArticleController pour destroy.
    Retourne (Controller, calls).
    """
    form_code, _ = build_form(definition)
    form_ns: dict = {}
    exec(compile(form_code, "<form>", "exec"), form_ns)
    ArticleForm = form_ns[f"{definition['entity']}Form"]

    calls: dict = {
        "delete_entity": [],
        "list_media":    [],
        "delete_media":  [],
        "_media_to_return": media_entries if media_entries is not None else [],
    }

    snake = definition["entity"].lower()

    def _delete_entity(pk):
        calls["delete_entity"].append(pk)

    def _list_media(entity_name, entity_id, *, role=None):
        calls["list_media"].append({"entity_name": entity_name, "entity_id": entity_id})
        return calls["_media_to_return"]

    def _delete_media(media_id, *, delete_files, variants):
        calls["delete_media"].append({"id": media_id, "delete_files": delete_files, "variants": variants})

    def _mod(name, **attrs):
        m = types.ModuleType(name)
        for k, v in attrs.items():
            setattr(m, k, v)
        return m

    plural = snake + "s"
    model_attrs = {
        f"get_{plural}": lambda *a, **kw: [],
        f"get_{snake}_by_id": lambda pk: {"id": pk, "titre": "T"},
        f"add_{snake}": lambda data: 1,
        f"update_{snake}": lambda pk, data: None,
        f"delete_{snake}": _delete_entity,
        f"bulk_delete_{plural}": lambda ids: None,
        f"count_{plural}": lambda *a, **kw: 0,
        f"find_{plural}_paginated": lambda *a, **kw: [],
        f"find_{plural}_for_export": lambda *a, **kw: [],
    }
    form_mod_name  = f"mvc.forms.{snake}_form"
    model_mod_name = f"mvc.models.{snake}_model"

    model_mod = _mod(model_mod_name, **model_attrs)
    form_mod  = _mod(form_mod_name,  **{f"{definition['entity']}Form": ArticleForm})
    flash_mod = _mod("mvc.helpers.flash", render_flash_html=lambda req: "")
    ctrl_mod  = _mod("core.mvc.controller", BaseController=_FakeBaseController)
    upload_mod = _mod(
        "core.uploads",
        save_upload=lambda *a, **kw: SimpleNamespace(path="images/x.png", mime_type="image/png"),
    )
    forge_media_mod = _mod(
        "forge_mvc_images",
        save_image_upload=lambda *a, **kw: SimpleNamespace(path="images/x.png", mime_type="image/png"),
        attach_media_to_entity=lambda *a, **kw: None,
        list_media_for_entity=_list_media,
        delete_media=_delete_media,
        update_media_alt_text=lambda *a, **kw: None,
        update_media_position=lambda *a, **kw: None,
        get_cover_media=lambda *a, **kw: None,
    )

    for pkg in ("mvc", "mvc.models", "mvc.forms", "mvc.helpers"):
        if pkg not in sys.modules:
            monkeypatch.setitem(sys.modules, pkg, types.ModuleType(pkg))

    monkeypatch.setitem(sys.modules, model_mod_name, model_mod)
    monkeypatch.setitem(sys.modules, form_mod_name,  form_mod)
    monkeypatch.setitem(sys.modules, "mvc.helpers.flash",   flash_mod)
    monkeypatch.setitem(sys.modules, "core.mvc.controller", ctrl_mod)
    monkeypatch.setitem(sys.modules, "core.uploads",        upload_mod)
    monkeypatch.setitem(sys.modules, "forge_mvc_images",     forge_media_mod)

    ctrl_code = build_controller(definition)
    ctrl_ns: dict = {}
    exec(compile(ctrl_code, "<ctrl>", "exec"), ctrl_ns)
    Controller = ctrl_ns[f"{definition['entity']}Controller"]

    return Controller, calls


# ── Tests runtime ─────────────────────────────────────────────────────────────

def test_destroy_appelle_list_media_pour_entite_avec_media(monkeypatch):
    """destroy() appelle list_media_for_entity avec le bon entity_name et entity_id."""
    Ctrl, calls = _build_env(monkeypatch, _article_with_media(), media_entries=[])
    req = FakeRequest("POST", "/articles/7/delete")
    req.route_params = {"id": "7"}
    resp = Ctrl.destroy(req)

    assert resp.type == "redirect"
    assert len(calls["list_media"]) == 1
    assert calls["list_media"][0]["entity_name"] == "article"
    assert calls["list_media"][0]["entity_id"] == 7


def test_destroy_appelle_delete_media_pour_chaque_media(monkeypatch):
    """destroy() supprime chaque média retourné par list_media_for_entity."""
    medias = [{"id": 10}, {"id": 20}]
    Ctrl, calls = _build_env(monkeypatch, _article_with_media(), media_entries=medias)
    req = FakeRequest("POST", "/articles/7/delete")
    req.route_params = {"id": "7"}
    Ctrl.destroy(req)

    assert len(calls["delete_media"]) == 2
    deleted_ids = {c["id"] for c in calls["delete_media"]}
    assert deleted_ids == {10, 20}
    assert all(c["delete_files"] is True for c in calls["delete_media"])


def test_destroy_supprime_entite_apres_medias(monkeypatch):
    """delete_article() est appelé après la suppression des médias."""
    medias = [{"id": 99}]
    Ctrl, calls = _build_env(monkeypatch, _article_with_media(), media_entries=medias)
    req = FakeRequest("POST", "/articles/7/delete")
    req.route_params = {"id": "7"}
    Ctrl.destroy(req)

    assert calls["delete_entity"] == [7]
    assert len(calls["delete_media"]) == 1


def test_destroy_sans_media_fonctionne_sans_appel_media(monkeypatch):
    """destroy() sur entité sans champ media ne fait aucun appel à l'API média."""
    Ctrl, calls = _build_env(monkeypatch, _article_without_media())
    req = FakeRequest("POST", "/articles/7/delete")
    req.route_params = {"id": "7"}
    resp = Ctrl.destroy(req)

    assert resp.type == "redirect"
    assert calls["list_media"] == []
    assert calls["delete_media"] == []
    assert calls["delete_entity"] == [7]


def test_destroy_aucun_media_lie_supprime_quand_meme_entite(monkeypatch):
    """Si list_media_for_entity retourne [], delete_article est quand même appelé."""
    Ctrl, calls = _build_env(monkeypatch, _article_with_media(), media_entries=[])
    req = FakeRequest("POST", "/articles/7/delete")
    req.route_params = {"id": "7"}
    resp = Ctrl.destroy(req)

    assert resp.type == "redirect"
    assert calls["delete_media"] == []
    assert calls["delete_entity"] == [7]
