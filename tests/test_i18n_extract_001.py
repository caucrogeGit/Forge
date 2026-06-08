"""Garde-fou I18N-EXTRACT-001 — extraction de l'i18n vers forge-mvc-i18n (ADR-027).

Vérifie que :
- le translator runtime n'est plus dans le core (`core/i18n/` absent) ;
- le paquet `forge-mvc-i18n` expose l'API publique attendue et fonctionne ;
- le renderer du noyau garde un repli `trans` no-op (retourne la clé) et
  n'importe pas le paquet au niveau module ;
- le pyproject du paquet est correct (nom, classifier Beta, dépendance core) ;
- les clés de configuration i18n restent dans le registre du noyau.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

import core.forge as forge

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Note : pas d'`importorskip` au niveau module. Les assertions sur l'arbre
# source et sur le noyau (absence de core/i18n, repli no-op, clés de config,
# pyproject du paquet) doivent valoir même en environnement core-only, où le
# paquet forge-mvc-i18n n'est pas installé. Seuls les tests qui importent
# réellement le paquet le gardent par un `importorskip` local.


# --- Absence dans le core -----------------------------------------------------


def test_core_i18n_absent_du_core():
    assert not (PROJECT_ROOT / "core" / "i18n").exists()


def test_renderer_n_importe_pas_i18n_au_niveau_module():
    src = (PROJECT_ROOT / "integrations" / "jinja2" / "renderer.py").read_text(
        encoding="utf-8"
    )
    # L'import du paquet doit être gardé par try/except, pas en tête de module.
    assert "from core.i18n import" not in src
    for line in src.splitlines():
        stripped = line.strip()
        if stripped.startswith(("from forge_mvc_i18n", "import forge_mvc_i18n")):
            # Toléré uniquement indenté (dans le try/except du constructeur).
            assert line.startswith(" "), f"import i18n au niveau module : {line!r}"


# --- API publique du paquet ---------------------------------------------------


def test_forge_mvc_i18n_expose_l_api_publique():
    i18n = pytest.importorskip("forge_mvc_i18n")
    for name in (
        "I18nError",
        "TranslationCatalogError",
        "trans",
        "load_catalog",
        "clear_translation_cache",
        "get_default_locale",
        "set_default_locale",
        "get_fallback_locale",
        "set_fallback_locale",
    ):
        assert name in i18n.__all__
        assert hasattr(i18n, name)


def test_forge_mvc_i18n_a_une_version():
    i18n = pytest.importorskip("forge_mvc_i18n")
    assert isinstance(i18n.__version__, str)
    assert i18n.__version__


def test_trans_fonctionne_depuis_le_paquet():
    i18n = pytest.importorskip("forge_mvc_i18n")
    assert i18n.trans("common.save") == "Enregistrer"
    assert i18n.trans("cle.absente.partout") == "cle.absente.partout"


# --- Repli no-op du noyau -----------------------------------------------------


def test_renderer_garde_un_repli_trans():
    from integrations.jinja2.renderer import _default_trans

    assert _default_trans("crud.edit") == "crud.edit"
    assert _default_trans("x", locale="en", translations_dir="/tmp") == "x"


def test_cles_config_i18n_restent_dans_le_noyau():
    assert forge.get("i18n_default_locale")
    assert "i18n_fallback_locale" in forge._cfg


# --- pyproject du paquet ------------------------------------------------------


def test_pyproject_i18n_correct():
    data = tomllib.loads(
        (PROJECT_ROOT / "packages" / "forge-mvc-i18n" / "pyproject.toml").read_text(
            encoding="utf-8"
        )
    )
    project = data["project"]
    assert project["name"] == "forge-mvc-i18n"
    assert any(
        c == "Development Status :: 4 - Beta" for c in project["classifiers"]
    )
    assert any(dep.startswith("forge-mvc>") for dep in project["dependencies"])
