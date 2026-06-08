"""Tests pour I18N-CACHE-001 — Cache des catalogues de traduction."""

from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_i18n")

from forge_mvc_i18n import (
    TranslationCatalogError,
    clear_translation_cache,
    load_catalog,
    trans,
)
from forge_mvc_i18n.translator import _load_catalog_cached


@pytest.fixture(autouse=True)
def reset_cache():
    """Vide le cache avant et après chaque test pour garantir l'isolation."""
    clear_translation_cache()
    yield
    clear_translation_cache()


# ── Export public ──────────────────────────────────────────────────────────────


def test_clear_translation_cache_est_exportee():
    """clear_translation_cache est accessible depuis forge_mvc_i18n."""
    import forge_mvc_i18n as i18n
    assert callable(i18n.clear_translation_cache)
    assert "clear_translation_cache" in i18n.__all__


# ── Cache actif après premier chargement ─────────────────────────────────────


def test_deuxieme_appel_load_catalog_est_un_hit(tmp_path):
    """Deux appels successifs à load_catalog réutilisent le cache."""
    (tmp_path / "fr.json").write_text('{"common.save": "Enregistrer"}', encoding="utf-8")
    load_catalog("fr", translations_dir=tmp_path)
    info_before = _load_catalog_cached.cache_info()
    load_catalog("fr", translations_dir=tmp_path)
    info_after = _load_catalog_cached.cache_info()
    assert info_after.hits == info_before.hits + 1


def test_premier_appel_load_catalog_est_un_miss(tmp_path):
    """Le premier appel à load_catalog est un cache miss."""
    (tmp_path / "fr.json").write_text('{"common.save": "Enregistrer"}', encoding="utf-8")
    info_before = _load_catalog_cached.cache_info()
    load_catalog("fr", translations_dir=tmp_path)
    info_after = _load_catalog_cached.cache_info()
    assert info_after.misses == info_before.misses + 1


def test_trans_multiples_appels_reutilisent_cache(tmp_path):
    """Plusieurs appels trans() sur la même locale utilisent le cache."""
    (tmp_path / "fr.json").write_text(
        '{"a.key": "Alpha", "b.key": "Beta"}', encoding="utf-8"
    )
    trans("a.key", locale="fr", translations_dir=tmp_path)
    info_before = _load_catalog_cached.cache_info()
    trans("b.key", locale="fr", translations_dir=tmp_path)
    info_after = _load_catalog_cached.cache_info()
    assert info_after.hits > info_before.hits


# ── Vidage du cache ───────────────────────────────────────────────────────────


def test_clear_translation_cache_vide_le_cache(tmp_path):
    """clear_translation_cache() remet le cache à zéro."""
    (tmp_path / "fr.json").write_text('{"common.save": "Enregistrer"}', encoding="utf-8")
    load_catalog("fr", translations_dir=tmp_path)
    assert _load_catalog_cached.cache_info().currsize > 0
    clear_translation_cache()
    assert _load_catalog_cached.cache_info().currsize == 0


def test_apres_vidage_fichier_relu(tmp_path):
    """Après clear_translation_cache(), le fichier est relu au prochain appel."""
    catalog_file = tmp_path / "fr.json"
    catalog_file.write_text('{"common.save": "Enregistrer"}', encoding="utf-8")
    load_catalog("fr", translations_dir=tmp_path)
    clear_translation_cache()
    # Modifier le fichier après vidage
    catalog_file.write_text('{"common.save": "Sauvegarder"}', encoding="utf-8")
    result = load_catalog("fr", translations_dir=tmp_path)
    assert result["common.save"] == "Sauvegarder"


def test_clear_cache_puis_hit_sur_prochain_doublon(tmp_path):
    """Après vidage, un doublon d'appel redevient un hit (nouveau cycle)."""
    (tmp_path / "fr.json").write_text('{"x": "X"}', encoding="utf-8")
    load_catalog("fr", translations_dir=tmp_path)
    clear_translation_cache()
    load_catalog("fr", translations_dir=tmp_path)
    info = _load_catalog_cached.cache_info()
    assert info.hits == 0
    load_catalog("fr", translations_dir=tmp_path)
    info2 = _load_catalog_cached.cache_info()
    assert info2.hits == 1


# ── Isolation entre plusieurs translations_dir ───────────────────────────────


def test_deux_translations_dir_distincts_pas_de_pollution(tmp_path):
    """Deux translations_dir différents ont des entrées de cache distinctes."""
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    (dir_a / "fr.json").write_text('{"common.save": "Enregistrer"}', encoding="utf-8")
    (dir_b / "fr.json").write_text('{"common.save": "Save FR"}', encoding="utf-8")
    catalog_a = load_catalog("fr", translations_dir=dir_a)
    catalog_b = load_catalog("fr", translations_dir=dir_b)
    assert catalog_a["common.save"] == "Enregistrer"
    assert catalog_b["common.save"] == "Save FR"
    assert _load_catalog_cached.cache_info().currsize == 2


def test_str_et_path_identiques_produisent_meme_entree_cache(tmp_path):
    """Passer translations_dir en str ou Path pour le même répertoire => même entrée cache."""
    (tmp_path / "fr.json").write_text('{"x": "X"}', encoding="utf-8")
    load_catalog("fr", translations_dir=str(tmp_path))
    info_before = _load_catalog_cached.cache_info()
    load_catalog("fr", translations_dir=tmp_path)
    info_after = _load_catalog_cached.cache_info()
    assert info_after.hits == info_before.hits + 1
    assert info_after.currsize == info_before.currsize


# ── Comportement fallback conservé ───────────────────────────────────────────


def test_cache_naffecte_pas_le_fallback(tmp_path):
    """Le fallback locale fonctionne normalement avec le cache activé."""
    (tmp_path / "fr.json").write_text('{"common.save": "Enregistrer"}', encoding="utf-8")
    (tmp_path / "en.json").write_text('{"other.key": "Other"}', encoding="utf-8")
    result = trans("common.save", locale="en", translations_dir=tmp_path)
    assert result == "Enregistrer"


def test_cache_cle_absente_retourne_cle(tmp_path):
    """Une clé absente retourne la clé elle-même, cache ou non."""
    (tmp_path / "fr.json").write_text('{"common.save": "Enregistrer"}', encoding="utf-8")
    result = trans("inconnue.cle", locale="fr", translations_dir=tmp_path)
    assert result == "inconnue.cle"


def test_cache_locale_absente_leve_erreur(tmp_path):
    """Une locale absente lève TranslationCatalogError même avec le cache."""
    with pytest.raises(TranslationCatalogError):
        load_catalog("xx", translations_dir=tmp_path)


def test_cache_json_invalide_leve_erreur(tmp_path):
    """Un JSON invalide lève TranslationCatalogError."""
    (tmp_path / "fr.json").write_text("{invalid", encoding="utf-8")
    with pytest.raises(TranslationCatalogError):
        load_catalog("fr", translations_dir=tmp_path)


# ── Roadmap ───────────────────────────────────────────────────────────────────


def test_roadmap_reference_i18n_cache_001():
    """forge-roadmap.md référence I18N-CACHE-001."""
    from pathlib import Path
    content = (Path(__file__).resolve().parents[1] / "docs" / "roadmap" / "forge-roadmap.md").read_text(
        encoding="utf-8"
    )
    assert "I18N-CACHE-001" in content
