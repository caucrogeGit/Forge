"""Garde-fou I18N-LOCALE-TRAVERSAL-GUARD-001.

`locale` ne sert qu'à composer `<locale>.json` ; un argument contenant des
caractères de chemin (`/`, `\\`, `..`) ne doit jamais permettre de sortir du
dossier des catalogues.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_i18n")

from forge_mvc_i18n.exceptions import TranslationCatalogError
from forge_mvc_i18n.translator import clear_translation_cache, load_catalog


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_translation_cache()
    yield
    clear_translation_cache()


@pytest.mark.parametrize(
    "locale",
    ["../secret", "fr/../../etc/passwd", "..", "fr/fr", "a\\b", "a.b", "a\x00b"],
)
def test_locale_avec_caractere_de_chemin_rejetee(tmp_path: Path, locale: str) -> None:
    with pytest.raises(TranslationCatalogError):
        load_catalog(locale, translations_dir=tmp_path)


def test_locale_valide_charge_le_catalogue(tmp_path: Path) -> None:
    (tmp_path / "fr.json").write_text(json.dumps({"hello": "bonjour"}), encoding="utf-8")
    assert load_catalog("fr", translations_dir=tmp_path) == {"hello": "bonjour"}


def test_traversal_ne_lit_pas_un_fichier_hors_dossier(tmp_path: Path) -> None:
    secret = tmp_path / "secret.json"
    secret.write_text(json.dumps({"leak": "x"}), encoding="utf-8")
    catalogs = tmp_path / "translations"
    catalogs.mkdir()
    # Tenter de remonter vers ../secret.json depuis le dossier des catalogues.
    with pytest.raises(TranslationCatalogError):
        load_catalog("../secret", translations_dir=catalogs)
