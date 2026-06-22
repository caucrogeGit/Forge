from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_i18n")

import core.forge as forge
import forge_mvc_i18n as i18n
from forge_mvc_i18n import set_fallback_locale
from integrations.jinja2.renderer import Jinja2Renderer, _default_trans


@pytest.fixture(autouse=False)
def reset_fallback_locale():
    original = forge._cfg["i18n_fallback_locale"]
    yield
    forge._cfg["i18n_fallback_locale"] = original


def test_jinja_env_expose_trans(tmp_path):
    r = Jinja2Renderer(str(tmp_path))
    assert "trans" in r._env.globals


def test_trans_jinja_global_est_la_fonction_i18n_optin(tmp_path):
    # forge-mvc-i18n installé : le renderer remplace le repli no-op par la
    # vraie fonction trans() du paquet.
    r = Jinja2Renderer(str(tmp_path))
    assert r._env.globals["trans"] is i18n.trans


def test_default_trans_retourne_la_cle():
    # Repli no-op du noyau quand forge-mvc-i18n est absent : la clé brute.
    assert _default_trans("crud.edit") == "crud.edit"
    assert _default_trans("common.save", locale="en") == "common.save"
    assert _default_trans("x", locale="fr", translations_dir="/tmp") == "x"


def test_template_trans_common_save(tmp_path):
    (tmp_path / "t.html").write_text('{{ trans("common.save") }}')
    r = Jinja2Renderer(str(tmp_path))
    assert r.render("t.html", {}) == "Enregistrer"


def test_template_trans_validation_required(tmp_path):
    (tmp_path / "t.html").write_text('{{ trans("validation.required") }}')
    r = Jinja2Renderer(str(tmp_path))
    assert r.render("t.html", {}) == "Ce champ est obligatoire."


def test_template_trans_cle_inconnue_retourne_cle(tmp_path):
    (tmp_path / "t.html").write_text('{{ trans("cle.inconnue") }}')
    r = Jinja2Renderer(str(tmp_path))
    assert r.render("t.html", {}) == "cle.inconnue"


def test_template_trans_locale_explicite(tmp_path):
    (tmp_path / "t.html").write_text('{{ trans("common.cancel", locale="fr") }}')
    r = Jinja2Renderer(str(tmp_path))
    assert r.render("t.html", {}) == "Annuler"


def test_template_trans_dans_condition(tmp_path):
    (tmp_path / "t.html").write_text(
        '{% if True %}{{ trans("crud.create") }}{% endif %}'
    )
    r = Jinja2Renderer(str(tmp_path))
    assert r.render("t.html", {}) == "Créer"


def test_aucun_catalogue_en_ou_es(tmp_path):
    assert not Path("translations/en.json").exists()
    assert not Path("translations/es.json").exists()


def test_make_crud_utilise_trans_depuis_i18n_009():
    src = Path("cli/entities/make_crud.py").read_text(encoding="utf-8")
    assert "trans(" in src


def test_template_trans_fallback_jinja(tmp_path, reset_fallback_locale):
    # en.json sans "common.save" → fallback sur fr.json dans translations/
    (tmp_path / "views").mkdir()
    (tmp_path / "views" / "t.html").write_text(
        '{{ trans("common.save", locale="en", translations_dir=tdir) }}'
    )
    catalog_dir = tmp_path / "catalogs"
    catalog_dir.mkdir()
    (catalog_dir / "fr.json").write_text('{"common.save": "Enregistrer"}', encoding="utf-8")
    (catalog_dir / "en.json").write_text('{"other.key": "Other"}', encoding="utf-8")
    set_fallback_locale("fr")
    r = Jinja2Renderer(str(tmp_path / "views"))
    result = r.render("t.html", {"tdir": str(catalog_dir)})
    assert result == "Enregistrer"
