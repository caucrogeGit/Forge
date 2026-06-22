"""Tests réorganisation galerie — MEDIA-GALLERY-ORDER-001.

Vérifie que le contrôleur généré par make:crud permet de modifier
l'ordre des médias d'une galerie (multiple=true) par champs numériques :
- form.html génère un <input type="number" name="_media_position_{name}_{id}"> ;
- update() lit les champs _media_position_{name}_* et appelle update_media_position ;
- les valeurs invalides ou absentes sont ignorées sans erreur ;
- formulaire invalide : aucune mise à jour de position ;
- ajout append-only et suppression individuelle restent fonctionnels.
"""
from __future__ import annotations

import sys
import types
from types import SimpleNamespace


from cli.entities.make_crud import build_controller, build_form, build_form_view
from cli.entities.validation import normalize_entity_definition
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


def _update_invalid_block(code: str) -> list[str]:
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


# ── Tests de génération ───────────────────────────────────────────────────────

class TestGalleryOrderGeneration:

    def test_form_html_genere_input_number_par_item_galerie(self):
        html = build_form_view(_article_with_gallery())
        assert 'type="number"' in html
        assert '_media_position_photos_' in html

    def test_nom_champ_position_stable(self):
        html = build_form_view(_article_with_gallery())
        assert 'name="_media_position_photos_{{ _m.id }}"' in html

    def test_form_html_champ_position_porte_valeur_courante(self):
        html = build_form_view(_article_with_gallery())
        assert 'value="{{ _m.position }}"' in html

    def test_update_detecte_champs_position_photos(self):
        code = build_controller(_article_with_gallery())
        update_lines = _lines_in_method(code, "update")
        assert any('_media_position_photos_' in l for l in update_lines)

    def test_update_appelle_update_media_position(self):
        code = build_controller(_article_with_gallery())
        update_lines = _lines_in_method(code, "update")
        assert any('update_media_position' in l for l in update_lines)

    def test_update_invalide_pas_de_mise_a_jour_position(self):
        code = build_controller(_article_with_gallery())
        block = _update_invalid_block(code)
        assert not any('update_media_position' in l for l in block)

    def test_entite_sans_galerie_pas_de_logique_position(self):
        code = build_controller(_article_without_media())
        assert 'update_media_position' not in code
        assert '_media_position_' not in code

    def test_mixed_seul_multiple_recoit_logique_position(self):
        code = build_controller(_article_mixed())
        update_lines = _lines_in_method(code, "update")
        assert any('_media_position_photos_' in l for l in update_lines)
        assert not any('_media_position_cover_' in l for l in update_lines)

    def test_suppression_et_ajout_toujours_presents(self):
        code = build_controller(_article_with_gallery())
        update_lines = _lines_in_method(code, "update")
        assert any('_delete_media_photos' in l for l in update_lines)
        assert any('attach_media_to_entity' in l for l in update_lines)


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
        "update_article":        [],
        "save_upload":           [],
        "attach":                [],
        "delete_media":          [],
        "update_media_position": [],
        "list_media":            [],
        "_gallery": gallery_entries if gallery_entries is not None else [],
    }

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

def _req_update(pk, titre="Article test", upload=None, positions=None, delete_ids=None):
    """
    positions : dict {media_id: position_str}, e.g. {12: "10", 15: "20"}
    delete_ids : list of str IDs
    """
    body = {"titre": titre}
    req = FakeRequest("POST", f"/articles/{pk}", body=body,
                      files={"photos": upload} if upload else {})
    req.route_params = {"id": str(pk)}
    if positions:
        for mid, pos in positions.items():
            req.body[f"_media_position_photos_{mid}"] = [pos]
    if delete_ids:
        req.body["_delete_media_photos"] = delete_ids
    return req


def _req_update_invalid(pk, positions=None):
    req = FakeRequest("POST", f"/articles/{pk}", body={"titre": ""})
    req.route_params = {"id": str(pk)}
    if positions:
        for mid, pos in positions.items():
            req.body[f"_media_position_photos_{mid}"] = [pos]
    return req


# ── Tests runtime ─────────────────────────────────────────────────────────────

def test_update_avec_une_position_appelle_update_media_position(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    resp = Ctrl.update(_req_update(7, positions={12: "10"}))

    assert resp.type == "redirect"
    assert len(calls["update_media_position"]) == 1
    assert calls["update_media_position"][0] == {"id": 12, "position": 10}


def test_update_avec_deux_positions_appelle_deux_updates(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    resp = Ctrl.update(_req_update(7, positions={12: "10", 15: "20"}))

    assert resp.type == "redirect"
    assert len(calls["update_media_position"]) == 2
    results = {c["id"]: c["position"] for c in calls["update_media_position"]}
    assert results == {12: 10, 15: 20}


def test_update_sans_position_aucun_update_media_position(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    resp = Ctrl.update(_req_update(7))

    assert resp.type == "redirect"
    assert calls["update_media_position"] == []


def test_update_valeur_invalide_ne_casse_pas(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    req = _req_update(7)
    req.body["_media_position_photos_12"] = ["abc"]
    resp = Ctrl.update(req)

    assert resp.type == "redirect"
    assert calls["update_media_position"] == []


def test_update_valeur_vide_ignoree(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    req = _req_update(7)
    req.body["_media_position_photos_12"] = []
    resp = Ctrl.update(req)

    assert resp.type == "redirect"
    assert calls["update_media_position"] == []


def test_update_invalide_pas_de_mise_a_jour(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    resp = Ctrl.update(_req_update_invalid(7, positions={12: "10"}))

    assert resp.type == "validation_error"
    assert calls["update_media_position"] == []


def test_update_position_et_ajout_garde_append(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    upload = _DummyUpload("new.png")
    resp = Ctrl.update(_req_update(7, upload=upload, positions={12: "5"}))

    assert resp.type == "redirect"
    assert len(calls["update_media_position"]) == 1
    assert calls["update_media_position"][0]["id"] == 12
    assert len(calls["save_upload"]) == 1
    assert len(calls["attach"]) == 1


def test_update_position_et_suppression_garde_delete(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_with_gallery())
    resp = Ctrl.update(_req_update(7, positions={15: "20"}, delete_ids=["12"]))

    assert resp.type == "redirect"
    assert len(calls["update_media_position"]) == 1
    assert calls["update_media_position"][0]["id"] == 15
    assert len(calls["delete_media"]) == 1
    assert calls["delete_media"][0]["id"] == 12


def test_entite_sans_galerie_aucun_update_position(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_without_media())
    req = FakeRequest("POST", "/articles/7", body={"titre": "Test"})
    req.route_params = {"id": "7"}
    resp = Ctrl.update(req)

    assert resp.type == "redirect"
    assert calls["update_media_position"] == []
