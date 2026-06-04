"""Tests runtime — CRUD généré avec champs média (MEDIA-RUNTIME-001).

Vérifie que le code généré par make:crud s'exécute correctement avec des
fichiers uploadés transmis via request.files.  Tous les appels SQL et média
sont interceptés par des mocks ; aucune base de données réelle n'est utilisée.
"""
from __future__ import annotations

import sys
import types
from types import SimpleNamespace

import pytest

from forge_cli.entities.make_crud import build_form, build_controller
from forge_cli.entities.validation import normalize_entity_definition
from tests.fake_request import FakeRequest


# ── Entité de référence ───────────────────────────────────────────────────────

def _article_def():
    return normalize_entity_definition(
        {
            "entity": "Article",
            "table": "article",
            "description": "",
            "fields": [
                {"name": "id",    "sql_type": "INT",        "primary_key": True, "auto_increment": True},
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


# ── Faux fichier uploadé ───────────────────────────────────────────────────────

class _DummyUpload:
    def __init__(self, filename="photo.png", content_type="image/png", size=100):
        self.filename  = filename
        self.content_type = content_type
        self.size      = size


# ── Faux BaseController ────────────────────────────────────────────────────────

class _FakeBaseController:
    @staticmethod
    def render(template, status=200, context=None, **kw):
        return SimpleNamespace(type="render", template=template, status=status,
                               context=context or {})

    @staticmethod
    def redirect_with_flash(request, location, message, **kw):
        return SimpleNamespace(type="redirect", location=location, message=message)

    @staticmethod
    def validation_error(template, context=None, *, request=None):
        return SimpleNamespace(type="validation_error", template=template,
                               context=context or {})

    @staticmethod
    def not_found():
        return SimpleNamespace(type="not_found")

    @staticmethod
    def set_flash(request, message, level="success"):
        pass

    @staticmethod
    def csrf_token(request):
        return "fake-csrf"


# ── Fixture principale ─────────────────────────────────────────────────────────

@pytest.fixture
def article_env(monkeypatch):
    """
    Génère et exec ArticleForm + ArticleController avec toutes les dépendances
    mockées.  Retourne (ArticleController, calls_dict).
    """
    definition = _article_def()

    # 1. Générer et exécuter le formulaire (core.forms est réel)
    form_code, _ = build_form(definition)
    form_ns: dict = {}
    exec(compile(form_code, "<article_form>", "exec"), form_ns)
    ArticleForm = form_ns["ArticleForm"]

    # 2. Journaliser les appels vers les fonctions mockées
    calls: dict = {
        "add_article":    [],
        "update_article": [],
        "delete_article": [],
        "save_upload":    [],
        "attach":         [],
        "list_media":     [],
        "delete_media":   [],
        "get_cover":      [],
        # données injectables par les tests
        "_existing_media": [],
        "_cover_media":    None,
    }

    def _add_article(data):
        calls["add_article"].append(data)
        return 42

    def _update_article(pk, data):
        calls["update_article"].append((pk, data))

    def _save_upload(f, cat, *, variants=False):
        calls["save_upload"].append({"file": f, "category": cat, "variants": variants})
        return SimpleNamespace(path=f"images/{f.filename}", mime_type=f.content_type)

    def _attach(saved, *, entity_name, entity_id, role, position, alt_text=None):
        calls["attach"].append(
            {"entity_name": entity_name, "entity_id": entity_id, "role": role, "alt_text": alt_text}
        )

    def _list_media(entity_name, entity_id, *, role=None):
        return calls["_existing_media"]

    def _delete_media(media_id, *, delete_files, variants):
        calls["delete_media"].append({"id": media_id, "delete_files": delete_files,
                                       "variants": variants})

    def _get_cover(entity_name, entity_id, *, role):
        return calls["_cover_media"]

    # 3. Injecter les modules factices dans sys.modules
    def _mod(name, **attrs):
        m = types.ModuleType(name)
        for k, v in attrs.items():
            setattr(m, k, v)
        return m

    model_mod = _mod(
        "mvc.models.article_model",
        get_articles=lambda *a, **kw: [],
        get_article_by_id=lambda pk: {"id": pk, "titre": "Existant"},
        add_article=_add_article,
        update_article=_update_article,
        delete_article=lambda pk: calls["delete_article"].append(pk),
        bulk_delete_articles=lambda ids: None,
        count_articles=lambda *a, **kw: 0,
        find_articles_paginated=lambda *a, **kw: [],
        find_articles_for_export=lambda *a, **kw: [],
    )
    form_mod   = _mod("mvc.forms.article_form",   ArticleForm=ArticleForm)
    flash_mod  = _mod("mvc.helpers.flash",         render_flash_html=lambda req: "")
    ctrl_mod   = _mod("core.mvc.controller",       BaseController=_FakeBaseController)
    upload_mod = _mod("core.uploads", save_upload=_save_upload)
    forge_media_mod = _mod(
        "forge_mvc_images",
        # CORE-SAVEUPLOAD-GENERIC-CLEANUP : les champs image passent par
        # save_image_upload (même signature que l'ancien save_upload images).
        save_image_upload=_save_upload,
        attach_media_to_entity=_attach,
        list_media_for_entity=_list_media,
        delete_media=_delete_media,
        update_media_alt_text=lambda *a, **kw: None,
        update_media_position=lambda *a, **kw: None,
        get_cover_media=_get_cover,
    )

    for pkg in ("mvc", "mvc.models", "mvc.forms", "mvc.helpers"):
        if pkg not in sys.modules:
            monkeypatch.setitem(sys.modules, pkg, types.ModuleType(pkg))

    monkeypatch.setitem(sys.modules, "mvc.models.article_model", model_mod)
    monkeypatch.setitem(sys.modules, "mvc.forms.article_form",   form_mod)
    monkeypatch.setitem(sys.modules, "mvc.helpers.flash",         flash_mod)
    monkeypatch.setitem(sys.modules, "core.mvc.controller",       ctrl_mod)
    monkeypatch.setitem(sys.modules, "core.uploads",              upload_mod)
    monkeypatch.setitem(sys.modules, "forge_mvc_images",           forge_media_mod)

    # 4. Générer et exécuter le contrôleur
    ctrl_code = build_controller(definition)
    ctrl_ns: dict = {}
    exec(compile(ctrl_code, "<article_ctrl>", "exec"), ctrl_ns)
    ArticleController = ctrl_ns["ArticleController"]

    return ArticleController, calls


# ── Helpers ────────────────────────────────────────────────────────────────────

def _req_create(titre="Article test", upload=None):
    return FakeRequest(
        "POST", "/articles",
        body={"titre": titre},
        files={"photo": upload} if upload else {},
    )


def _req_update(pk, titre="Article test", upload=None, delete=False):
    body = {"titre": titre, "_method": "PUT"}
    if delete:
        body["_delete_media_photo"] = "1"
    return FakeRequest(
        "POST", f"/articles/{pk}",
        body=body,
        files={"photo": upload} if upload else {},
        params={"id": str(pk)},
    )


def _set_pk(request, pk):
    request.route_params = {"id": str(pk)}
    return request


# ── Tests ──────────────────────────────────────────────────────────────────────

# 1. Le formulaire généré accepte un fichier image venant de request.files

def test_form_accepte_image_depuis_request_files(article_env):
    _, _ = article_env
    upload = _DummyUpload("photo.png", "image/png")
    req = _set_pk(_req_create(upload=upload), 0)
    ArticleForm = sys.modules["mvc.forms.article_form"].ArticleForm
    form = ArticleForm.from_request(req)
    assert form.is_valid(), form.errors
    assert form.cleaned_data.get("photo") is upload


# 2. create() appelle save_upload + attach_media_to_entity

def test_create_appelle_save_upload_et_attach(article_env):
    ArticleController, calls = article_env
    upload = _DummyUpload("photo.png", "image/png")
    req = _set_pk(_req_create(upload=upload), 0)
    resp = ArticleController.create(req)

    assert resp.type == "redirect"
    assert len(calls["save_upload"]) == 1
    assert calls["save_upload"][0]["category"] == "images"
    assert calls["save_upload"][0]["file"] is upload
    assert len(calls["attach"]) == 1
    assert calls["attach"][0]["entity_id"] == 42
    assert calls["attach"][0]["role"] == "cover"


# 3. create() sans image n'appelle pas save_upload

def test_create_sans_image_ne_fait_pas_upload(article_env):
    ArticleController, calls = article_env
    req = _set_pk(_req_create(upload=None), 0)
    resp = ArticleController.create(req)

    assert resp.type == "redirect"
    assert calls["save_upload"] == []
    assert calls["attach"] == []
    assert len(calls["add_article"]) == 1
    assert calls["add_article"][0] == {"titre": "Article test"}


# 4. create() avec formulaire invalide ne déclenche pas d'upload

def test_create_formulaire_invalide_pas_upload(article_env):
    ArticleController, calls = article_env
    upload = _DummyUpload("photo.png", "image/png")
    req = _set_pk(_req_create(titre="", upload=upload), 0)  # titre vide → invalide
    resp = ArticleController.create(req)

    assert resp.type == "validation_error"
    assert calls["save_upload"] == []
    assert calls["add_article"] == []


# 5. update() sans nouveau fichier ne remplace pas le média

def test_update_sans_nouveau_fichier_conserve_media(article_env):
    ArticleController, calls = article_env
    calls["_existing_media"] = [{"id": 99}]
    req = _set_pk(_req_update(7, upload=None, delete=False), 7)
    resp = ArticleController.update(req)

    assert resp.type == "redirect"
    assert calls["save_upload"] == []
    assert calls["delete_media"] == []
    assert calls["attach"] == []
    assert len(calls["update_article"]) == 1


# 6. update() avec nouveau fichier remplace le média existant

def test_update_avec_nouveau_fichier_remplace(article_env):
    ArticleController, calls = article_env
    calls["_existing_media"] = [{"id": 99}]
    upload = _DummyUpload("new.png", "image/png")
    req = _set_pk(_req_update(7, upload=upload), 7)
    resp = ArticleController.update(req)

    assert resp.type == "redirect"
    assert len(calls["delete_media"]) == 1
    assert calls["delete_media"][0]["id"] == 99
    assert len(calls["save_upload"]) == 1
    assert calls["save_upload"][0]["file"] is upload
    assert len(calls["attach"]) == 1
    assert calls["attach"][0]["entity_id"] == 7


# 7. update() avec case à cocher suppression supprime sans ré-upload

def test_update_suppression_explicite_sans_nouveau_fichier(article_env):
    ArticleController, calls = article_env
    calls["_existing_media"] = [{"id": 55}]
    req = _set_pk(_req_update(7, upload=None, delete=True), 7)
    resp = ArticleController.update(req)

    assert resp.type == "redirect"
    assert len(calls["delete_media"]) == 1
    assert calls["delete_media"][0]["id"] == 55
    assert calls["save_upload"] == []
    assert calls["attach"] == []


# 8. Le champ photo est exclu de _sql_data transmis au modèle

def test_create_photo_exclu_des_donnees_sql(article_env):
    ArticleController, calls = article_env
    upload = _DummyUpload("photo.png", "image/png")
    req = _set_pk(_req_create(upload=upload), 0)
    ArticleController.create(req)

    assert len(calls["add_article"]) == 1
    sql_data = calls["add_article"][0]
    assert "photo" not in sql_data
    assert "titre" in sql_data


# 9. L'entity_id utilisé pour attach provient du lastrowid de add_article

def test_create_entity_id_est_le_lastrowid(article_env):
    ArticleController, calls = article_env
    upload = _DummyUpload("photo.png", "image/png")
    req = _set_pk(_req_create(upload=upload), 0)
    ArticleController.create(req)

    assert calls["attach"][0]["entity_id"] == 42  # retourné par le mock add_article
