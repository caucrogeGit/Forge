"""Tests texte alternatif dans le CRUD — MEDIA-ALT-CRUD-001.

Vérifie que le contrôleur et le formulaire générés par make:crud gèrent
le texte alternatif des médias :
- form.html inclut un champ alt_text pour les médias single et gallery ;
- create()/update() transmettent alt_text à attach_media_to_entity ;
- update() met à jour les alt_text des médias existants (single + gallery) ;
- le formulaire invalide ne modifie aucun alt_text ;
- entité sans média : aucun champ alt_text généré.

Convention retenue : chaîne vide ou None → stockée comme None.
"""
from __future__ import annotations

import sys
import types
from types import SimpleNamespace


from forge_cli.entities.make_crud import build_controller, build_form, build_form_view
from forge_cli.entities.validation import normalize_entity_definition
from tests.fake_request import FakeRequest


# ── Entités de référence ──────────────────────────────────────────────────────

def _article_single():
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
                {"name": "photo", "field": "image", "role": "cover",
                 "multiple": False, "required": False, "label": "Photo"},
            ],
        },
        source="test.json",
    )


def _article_gallery():
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
                {"name": "photos", "field": "image", "role": "gallery",
                 "multiple": True, "required": False, "label": "Photos"},
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

class TestAltCrudGeneration:

    def test_form_html_genere_champ_alt_text_pour_single(self):
        html = build_form_view(_article_single())
        assert 'name="_media_alt_photo"' in html

    def test_form_html_champ_alt_single_porte_valeur_courante(self):
        html = build_form_view(_article_single())
        assert "photo_media.alt_text" in html

    def test_form_html_genere_champ_alt_text_pour_galerie_ajout(self):
        html = build_form_view(_article_gallery())
        assert 'name="_media_alt_photos_new"' in html

    def test_form_html_genere_champ_alt_text_par_item_galerie(self):
        html = build_form_view(_article_gallery())
        assert '_media_alt_photos_{{ _m.id }}' in html

    def test_form_html_champ_alt_item_galerie_porte_valeur(self):
        html = build_form_view(_article_gallery())
        assert '_m.alt_text' in html

    def test_create_transmet_alt_text_pour_single(self):
        code = build_controller(_article_single())
        create_lines = _lines_in_method(code, "create")
        assert any("_media_alt_photo" in l for l in create_lines)
        assert any("alt_text=_photo_alt" in l for l in create_lines)

    def test_create_transmet_alt_text_pour_galerie(self):
        code = build_controller(_article_gallery())
        create_lines = _lines_in_method(code, "create")
        assert any("_media_alt_photos_new" in l for l in create_lines)
        assert any("alt_text=_photos_alt" in l for l in create_lines)

    def test_update_transmet_alt_text_sur_nouveau_single(self):
        code = build_controller(_article_single())
        update_lines = _lines_in_method(code, "update")
        assert any("_media_alt_photo" in l for l in update_lines)
        assert any("alt_text=_photo_alt" in l for l in update_lines)

    def test_update_met_a_jour_alt_existant_pour_single(self):
        code = build_controller(_article_single())
        update_lines = _lines_in_method(code, "update")
        assert any("update_media_alt_text" in l for l in update_lines)

    def test_update_met_a_jour_alt_galerie_existante(self):
        code = build_controller(_article_gallery())
        update_lines = _lines_in_method(code, "update")
        assert any("_media_alt_photos_" in l for l in update_lines)
        assert any("update_media_alt_text" in l for l in update_lines)

    def test_update_invalide_pas_de_alt_text(self):
        code = build_controller(_article_single())
        block = _update_invalid_block(code)
        assert not any("update_media_alt_text" in l for l in block)

    def test_entite_sans_media_aucun_alt_text(self):
        code = build_controller(_article_without_media())
        assert "_media_alt_" not in code
        assert "update_media_alt_text" not in code

    def test_form_sans_media_aucun_alt_text(self):
        html = build_form_view(_article_without_media())
        assert "_media_alt_" not in html


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

def _build_env(monkeypatch, definition, existing_single=None, gallery_entries=None):
    """
    existing_single : valeur retournée par list_media_for_entity pour le single cover.
    gallery_entries : valeur retournée par list_media_for_entity pour la gallery.
    """
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
        "update_media_alt_text": [],
        "update_media_position": [],
        "list_media":            [],
        "_existing_single": [existing_single] if existing_single else [],
        "_gallery":         gallery_entries if gallery_entries is not None else [],
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
                                "role": role, "alt_text": alt_text})

    def _delete_media(media_id, *, delete_files, variants):
        calls["delete_media"].append({"id": media_id})

    def _update_media_alt_text(media_id, alt_text):
        calls["update_media_alt_text"].append({"id": media_id, "alt_text": alt_text})

    def _update_media_position(media_id, position):
        calls["update_media_position"].append({"id": media_id, "position": position})

    def _list_media(entity_name, entity_id, *, role=None):
        calls["list_media"].append({"entity_name": entity_name, "entity_id": entity_id, "role": role})
        if role == "gallery":
            return calls["_gallery"]
        return calls["_existing_single"]

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
        update_media_alt_text=_update_media_alt_text,
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

def _req_create(titre="Article test", upload=None, alt_text=None, field="photo"):
    body = {"titre": titre}
    req = FakeRequest("POST", "/articles", body=body,
                      files={field: upload} if upload else {})
    if alt_text is not None:
        key = f"_media_alt_{field}" if field == "photo" else f"_media_alt_{field}_new"
        req.body[key] = [alt_text]
    return req


def _req_update_single(pk, titre="Article test", upload=None, alt_text=None):
    body = {"titre": titre}
    req = FakeRequest("POST", f"/articles/{pk}", body=body,
                      files={"photo": upload} if upload else {})
    req.route_params = {"id": str(pk)}
    if alt_text is not None:
        req.body["_media_alt_photo"] = [alt_text]
    return req


def _req_update_gallery(pk, titre="Article test", upload=None, alt_text_new=None,
                         alt_ids=None):
    """alt_ids : dict {media_id: alt_text_str}"""
    body = {"titre": titre}
    req = FakeRequest("POST", f"/articles/{pk}", body=body,
                      files={"photos": upload} if upload else {})
    req.route_params = {"id": str(pk)}
    if alt_text_new is not None:
        req.body["_media_alt_photos_new"] = [alt_text_new]
    if alt_ids:
        for mid, alt in alt_ids.items():
            req.body[f"_media_alt_photos_{mid}"] = [alt]
    return req


def _req_update_invalid(pk, alt_text=None):
    req = FakeRequest("POST", f"/articles/{pk}", body={"titre": ""})
    req.route_params = {"id": str(pk)}
    if alt_text is not None:
        req.body["_media_alt_photo"] = [alt_text]
    return req


# ── Tests runtime ─────────────────────────────────────────────────────────────

def test_create_single_avec_alt_text_transmet_a_attach(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_single())
    upload = _DummyUpload("photo.png")
    Ctrl.create(_req_create(upload=upload, alt_text="Façade principale"))

    assert len(calls["attach"]) == 1
    assert calls["attach"][0]["alt_text"] == "Façade principale"


def test_create_single_sans_alt_text_transmet_none(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_single())
    upload = _DummyUpload("photo.png")
    Ctrl.create(_req_create(upload=upload))

    assert len(calls["attach"]) == 1
    assert calls["attach"][0]["alt_text"] is None


def test_update_single_avec_nouveau_fichier_transmet_alt_text(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_single())
    upload = _DummyUpload("new.png")
    Ctrl.update(_req_update_single(7, upload=upload, alt_text="Détail produit"))

    assert len(calls["attach"]) == 1
    assert calls["attach"][0]["alt_text"] == "Détail produit"


def test_update_single_sans_fichier_met_a_jour_existant(monkeypatch):
    existing = {"id": 5, "path": "images/old.png", "alt_text": "ancien"}
    Ctrl, calls = _build_env(monkeypatch, _article_single(), existing_single=existing)
    Ctrl.update(_req_update_single(7, alt_text="nouveau alt"))

    assert len(calls["update_media_alt_text"]) == 1
    assert calls["update_media_alt_text"][0] == {"id": 5, "alt_text": "nouveau alt"}


def test_update_single_chaine_vide_passe_none(monkeypatch):
    existing = {"id": 5, "path": "images/old.png", "alt_text": "ancien"}
    Ctrl, calls = _build_env(monkeypatch, _article_single(), existing_single=existing)
    Ctrl.update(_req_update_single(7, alt_text=""))

    assert len(calls["update_media_alt_text"]) == 1
    assert calls["update_media_alt_text"][0]["alt_text"] is None


def test_update_gallery_nouveau_fichier_transmet_alt_text(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_gallery())
    upload = _DummyUpload("new.png")
    Ctrl.update(_req_update_gallery(7, upload=upload, alt_text_new="Photo intérieure"))

    assert len(calls["attach"]) == 1
    assert calls["attach"][0]["alt_text"] == "Photo intérieure"


def test_update_gallery_alt_existant_appelle_update_media_alt_text(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_gallery())
    Ctrl.update(_req_update_gallery(7, alt_ids={12: "Vue de face", 15: "Vue arrière"}))

    assert len(calls["update_media_alt_text"]) == 2
    results = {c["id"]: c["alt_text"] for c in calls["update_media_alt_text"]}
    assert results == {12: "Vue de face", 15: "Vue arrière"}


def test_update_invalide_pas_de_alt_text(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_single())
    Ctrl.update(_req_update_invalid(7, alt_text="Ne doit pas passer"))

    assert calls["update_media_alt_text"] == []
    assert calls["attach"] == []


def test_entite_sans_media_aucun_alt_text(monkeypatch):
    Ctrl, calls = _build_env(monkeypatch, _article_without_media())
    req = FakeRequest("POST", "/articles/7", body={"titre": "Test"})
    req.route_params = {"id": "7"}
    resp = Ctrl.update(req)

    assert resp.type == "redirect"
    assert calls["update_media_alt_text"] == []
    assert calls["attach"] == []
