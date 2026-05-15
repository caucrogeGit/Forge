from __future__ import annotations

import json
from pathlib import Path

import pytest

import core.forge as forge
import core.i18n as i18n
from core.i18n import (
    I18nError,
    TranslationCatalogError,
    get_default_locale,
    get_fallback_locale,
    load_catalog,
    set_default_locale,
    set_fallback_locale,
    trans,
)


# ---------------------------------------------------------------------------
# Socle — exceptions et exports
# ---------------------------------------------------------------------------


def test_core_i18n_is_importable():
    assert i18n.I18nError is I18nError
    assert i18n.TranslationCatalogError is TranslationCatalogError


def test_i18n_exceptions_are_standard_exceptions():
    assert issubclass(I18nError, Exception)
    assert issubclass(TranslationCatalogError, I18nError)


def test_i18n_exports_public_api():
    assert "I18nError" in i18n.__all__
    assert "TranslationCatalogError" in i18n.__all__
    assert "load_catalog" in i18n.__all__
    assert "trans" in i18n.__all__
    assert "get_default_locale" in i18n.__all__
    assert "set_default_locale" in i18n.__all__
    assert "get_fallback_locale" in i18n.__all__
    assert "set_fallback_locale" in i18n.__all__


def test_i18n_trans_is_importable():
    assert callable(i18n.trans)


# ---------------------------------------------------------------------------
# Catalogue français — fichier
# ---------------------------------------------------------------------------


def test_french_translation_catalog_exists():
    assert Path("translations/fr.json").is_file()


def test_french_translation_catalog_is_valid_flat_json():
    catalog = json.loads(Path("translations/fr.json").read_text(encoding="utf-8"))

    assert isinstance(catalog, dict)
    assert catalog
    for key, value in catalog.items():
        assert isinstance(key, str)
        assert "." in key
        assert key.strip() == key
        assert isinstance(value, str)
        assert value.strip()


def test_french_translation_catalog_contains_minimal_generic_keys():
    catalog = json.loads(Path("translations/fr.json").read_text(encoding="utf-8"))

    for key in (
        "common.save",
        "common.cancel",
        "crud.create",
        "crud.edit",
        "validation.required",
    ):
        assert key in catalog


def test_french_translation_catalog_stays_generic():
    catalog = json.loads(Path("translations/fr.json").read_text(encoding="utf-8"))
    forbidden_terms = (
        "commune",
        "sejour",
        "séjour",
        "hebergement",
        "hébergement",
        "reservation",
        "réservation",
    )

    for key in catalog:
        lowered = key.lower()
        assert all(term not in lowered for term in forbidden_terms)


def test_only_french_translation_catalog_exists_for_now():
    assert not Path("translations/en.json").exists()
    assert not Path("translations/es.json").exists()
    assert not Path("mvc/translations").exists()
    assert not Path("core/i18n/translations").exists()


# ---------------------------------------------------------------------------
# load_catalog()
# ---------------------------------------------------------------------------


def test_load_catalog_returns_dict():
    catalog = load_catalog("fr")
    assert isinstance(catalog, dict)
    assert catalog


def test_load_catalog_contains_common_save():
    catalog = load_catalog("fr")
    assert "common.save" in catalog


def test_load_catalog_accepts_custom_translations_dir(tmp_path):
    catalog_file = tmp_path / "fr.json"
    catalog_file.write_text('{"common.ok": "OK"}', encoding="utf-8")
    catalog = load_catalog("fr", translations_dir=tmp_path)
    assert catalog == {"common.ok": "OK"}


def test_load_catalog_missing_raises_error(tmp_path):
    with pytest.raises(TranslationCatalogError):
        load_catalog("xx", translations_dir=tmp_path)


def test_load_catalog_invalid_json_raises_error(tmp_path):
    bad = tmp_path / "fr.json"
    bad.write_text("{invalid json", encoding="utf-8")
    with pytest.raises(TranslationCatalogError):
        load_catalog("fr", translations_dir=tmp_path)


def test_load_catalog_non_dict_json_raises_error(tmp_path):
    bad = tmp_path / "fr.json"
    bad.write_text('["liste"]', encoding="utf-8")
    with pytest.raises(TranslationCatalogError):
        load_catalog("fr", translations_dir=tmp_path)


def test_load_catalog_non_string_value_raises_error(tmp_path):
    bad = tmp_path / "fr.json"
    bad.write_text('{"common.save": 42}', encoding="utf-8")
    with pytest.raises(TranslationCatalogError):
        load_catalog("fr", translations_dir=tmp_path)


# ---------------------------------------------------------------------------
# trans()
# ---------------------------------------------------------------------------


def test_trans_returns_french_value():
    assert trans("common.save") == "Enregistrer"


def test_trans_validation_required():
    assert trans("validation.required") == "Ce champ est obligatoire."


def test_trans_with_explicit_locale():
    assert trans("common.save", locale="fr") == "Enregistrer"


def test_trans_unknown_key_returns_key():
    assert trans("clé.inconnue") == "clé.inconnue"


def test_trans_no_jinja_integration():
    # trans() est une fonction Python pure — pas de moteur de template
    import inspect
    src = inspect.getsource(i18n.trans)
    assert "jinja" not in src.lower()
    assert "Environment" not in src


# ---------------------------------------------------------------------------
# Langue par défaut
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=False)
def reset_default_locale():
    """Remet i18n_default_locale à 'fr' après chaque test qui le modifie."""
    original = forge._cfg["i18n_default_locale"]
    yield
    forge._cfg["i18n_default_locale"] = original


def test_get_default_locale_retourne_fr():
    assert get_default_locale() == "fr"


def test_trans_utilise_locale_par_defaut():
    assert trans("common.save") == "Enregistrer"


def test_trans_avec_locale_explicite_toujours_fonctionnel():
    assert trans("common.save", locale="fr") == "Enregistrer"


def test_trans_cle_inconnue_retourne_cle_avec_locale_par_defaut():
    assert trans("inconnu.test") == "inconnu.test"


def test_trans_translations_dir_personnalise_reste_fonctionnel(tmp_path):
    (tmp_path / "fr.json").write_text('{"custom.key": "Valeur custom"}', encoding="utf-8")
    assert trans("custom.key", translations_dir=tmp_path) == "Valeur custom"


def test_set_default_locale_change_la_locale(reset_default_locale):
    set_default_locale("fr")
    assert get_default_locale() == "fr"


def test_set_default_locale_est_repercute_dans_trans(reset_default_locale, tmp_path):
    (tmp_path / "fr.json").write_text('{"hello.world": "Bonjour monde"}', encoding="utf-8")
    set_default_locale("fr")
    assert trans("hello.world", translations_dir=tmp_path) == "Bonjour monde"


def test_set_default_locale_chaine_vide_leve_erreur():
    with pytest.raises(I18nError):
        set_default_locale("")


def test_set_default_locale_espaces_seuls_leve_erreur():
    with pytest.raises(I18nError):
        set_default_locale("   ")


def test_set_default_locale_non_chaine_leve_erreur():
    with pytest.raises(I18nError):
        set_default_locale(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Fallback locale
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=False)
def reset_fallback_locale():
    """Remet i18n_fallback_locale à 'fr' après chaque test qui le modifie."""
    original = forge._cfg["i18n_fallback_locale"]
    yield
    forge._cfg["i18n_fallback_locale"] = original


def test_get_fallback_locale_retourne_fr():
    assert get_fallback_locale() == "fr"


def test_trans_fr_inchange_avec_fallback():
    assert trans("common.save", locale="fr") == "Enregistrer"


def test_trans_fallback_quand_cle_absente_dans_locale(tmp_path):
    (tmp_path / "fr.json").write_text('{"common.save": "Enregistrer"}', encoding="utf-8")
    (tmp_path / "en.json").write_text('{"other.key": "Other"}', encoding="utf-8")
    assert trans("common.save", locale="en", translations_dir=tmp_path) == "Enregistrer"


def test_trans_cle_absente_partout_retourne_cle(tmp_path):
    (tmp_path / "fr.json").write_text('{"common.save": "Enregistrer"}', encoding="utf-8")
    (tmp_path / "en.json").write_text('{"other.key": "Other"}', encoding="utf-8")
    assert trans("vraiment.inconnue", locale="en", translations_dir=tmp_path) == "vraiment.inconnue"


def test_trans_locale_et_fallback_identiques_pas_double_chargement(tmp_path):
    (tmp_path / "fr.json").write_text('{"common.save": "Enregistrer"}', encoding="utf-8")
    # locale == fallback_locale == "fr" : comportement stable
    assert trans("common.save", locale="fr", translations_dir=tmp_path) == "Enregistrer"


def test_trans_fallback_absent_retourne_cle(tmp_path, reset_fallback_locale):
    # fallback locale "es" n'existe pas : pas d'erreur, on retourne la clé
    (tmp_path / "en.json").write_text('{"other.key": "Other"}', encoding="utf-8")
    set_fallback_locale("es")
    assert trans("common.save", locale="en", translations_dir=tmp_path) == "common.save"


def test_set_fallback_locale_change_la_fallback(reset_fallback_locale):
    set_fallback_locale("fr")
    assert get_fallback_locale() == "fr"


def test_set_fallback_locale_none_desactive_fallback(reset_fallback_locale):
    set_fallback_locale(None)
    assert get_fallback_locale() is None


def test_set_fallback_locale_chaine_vide_leve_erreur():
    with pytest.raises(I18nError):
        set_fallback_locale("")


def test_set_fallback_locale_espaces_seuls_leve_erreur():
    with pytest.raises(I18nError):
        set_fallback_locale("   ")


def test_set_fallback_locale_non_chaine_non_none_leve_erreur():
    with pytest.raises(I18nError):
        set_fallback_locale(42)  # type: ignore[arg-type]


def test_fallback_desactive_retourne_cle_si_absente(tmp_path, reset_fallback_locale):
    (tmp_path / "en.json").write_text('{"other.key": "Other"}', encoding="utf-8")
    set_fallback_locale(None)
    assert trans("common.save", locale="en", translations_dir=tmp_path) == "common.save"
