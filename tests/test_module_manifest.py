"""Tests MODULE-SYSTEM-001 — contrat et validation du manifeste de module Forge."""

from __future__ import annotations

import json

import pytest

from core.modules import (
    ALLOWED_PROVIDES,
    ModuleManifest,
    ModuleManifestError,
    load_module_manifest,
    validate_module_manifest,
    validate_module_name,
    validate_module_version,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _valid_data(**overrides) -> dict:
    base = {
        "name": "agenda",
        "label": "Agenda",
        "version": "0.1.0",
        "description": "Module générique d'agenda.",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Création d'un ModuleManifest valide
# ---------------------------------------------------------------------------


def test_creation_manifeste_minimal_valide():
    m = validate_module_manifest(_valid_data())
    assert isinstance(m, ModuleManifest)
    assert m.name == "agenda"
    assert m.label == "Agenda"
    assert m.version == "0.1.0"
    assert m.description == "Module générique d'agenda."


def test_valeurs_par_defaut_provides_est_tuple_vide():
    m = validate_module_manifest(_valid_data())
    assert m.provides == ()


def test_valeurs_par_defaut_paths_est_dict_vide():
    m = validate_module_manifest(_valid_data())
    assert m.paths == {}


def test_manifeste_complet_avec_provides_et_paths():
    data = _valid_data(
        provides=["entities", "controllers", "views", "routes", "docs"],
        paths={
            "entities": "entities",
            "controllers": "controllers",
            "views": "views",
            "routes": "routes.py",
            "docs": "docs",
        },
    )
    m = validate_module_manifest(data)
    assert "entities" in m.provides
    assert m.paths["routes"] == "routes.py"


def test_manifeste_est_immutable():
    m = validate_module_manifest(_valid_data())
    with pytest.raises((AttributeError, TypeError)):
        m.name = "autre"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Refus d'un manifeste non dictionnaire
# ---------------------------------------------------------------------------


def test_manifeste_non_dict_est_rejete():
    with pytest.raises(ModuleManifestError, match="dictionnaire"):
        validate_module_manifest(["agenda", "1.0.0"])


def test_manifeste_none_est_rejete():
    with pytest.raises(ModuleManifestError):
        validate_module_manifest(None)


def test_manifeste_chaine_est_rejete():
    with pytest.raises(ModuleManifestError):
        validate_module_manifest("agenda")


# ---------------------------------------------------------------------------
# Champs obligatoires
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("missing_key", ["name", "label", "version", "description"])
def test_champ_obligatoire_manquant_est_rejete(missing_key):
    data = _valid_data()
    del data[missing_key]
    with pytest.raises(ModuleManifestError, match=missing_key):
        validate_module_manifest(data)


# ---------------------------------------------------------------------------
# Validation — name
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("valid_name", [
    "agenda",
    "statistiques",
    "patrimoine",
    "commerces",
    "annuaire_local",
    "module_v2",
    "a",
    "abc123",
])
def test_name_valide_accepte(valid_name):
    m = validate_module_manifest(_valid_data(name=valid_name))
    assert m.name == valid_name


def test_name_vide_est_rejete():
    with pytest.raises(ModuleManifestError, match="name"):
        validate_module_manifest(_valid_data(name=""))


def test_name_espaces_seuls_est_rejete():
    with pytest.raises(ModuleManifestError, match="name"):
        validate_module_manifest(_valid_data(name="   "))


def test_name_avec_majuscule_est_rejete():
    with pytest.raises(ModuleManifestError, match="name"):
        validate_module_manifest(_valid_data(name="Agenda"))


def test_name_avec_tiret_est_rejete():
    with pytest.raises(ModuleManifestError, match="name"):
        validate_module_manifest(_valid_data(name="agenda-module"))


def test_name_commencant_par_chiffre_est_rejete():
    with pytest.raises(ModuleManifestError):
        validate_module_manifest(_valid_data(name="1agenda"))


def test_name_avec_chemin_est_rejete():
    with pytest.raises(ModuleManifestError):
        validate_module_manifest(_valid_data(name="../agenda"))


def test_name_avec_slash_est_rejete():
    with pytest.raises(ModuleManifestError):
        validate_module_manifest(_valid_data(name="modules/agenda"))


def test_name_url_est_rejete():
    with pytest.raises(ModuleManifestError):
        validate_module_validate = validate_module_name
        validate_module_validate("http://agenda")


def test_name_html_est_rejete():
    with pytest.raises(ModuleManifestError):
        validate_module_name("<script>alert(1)</script>")


def test_validate_module_name_retourne_le_nom():
    assert validate_module_name("agenda") == "agenda"


def test_validate_module_name_rejette_chaine_vide():
    with pytest.raises(ModuleManifestError):
        validate_module_name("")


# ---------------------------------------------------------------------------
# Validation — label
# ---------------------------------------------------------------------------


def test_label_vide_est_rejete():
    with pytest.raises(ModuleManifestError, match="label"):
        validate_module_manifest(_valid_data(label=""))


def test_label_html_est_rejete():
    with pytest.raises(ModuleManifestError, match="label"):
        validate_module_manifest(_valid_data(label="<b>Agenda</b>"))


def test_label_valide_accepte():
    m = validate_module_manifest(_valid_data(label="Mon Module Agenda"))
    assert m.label == "Mon Module Agenda"


# ---------------------------------------------------------------------------
# Validation — version
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("valid_version", ["0.1.0", "1.0.0", "2.3.1", "10.20.30"])
def test_version_valide_acceptee(valid_version):
    m = validate_module_manifest(_valid_data(version=valid_version))
    assert m.version == valid_version


def test_version_vide_est_rejetee():
    with pytest.raises(ModuleManifestError, match="version"):
        validate_module_manifest(_valid_data(version=""))


@pytest.mark.parametrize("invalid_version", [
    "1.0",
    "v1.0.0",
    "1.0.0.0",
    "latest",
    "1",
    "1.0.x",
])
def test_version_format_invalide_est_rejete(invalid_version):
    with pytest.raises(ModuleManifestError):
        validate_module_manifest(_valid_data(version=invalid_version))


def test_validate_module_version_retourne_version():
    assert validate_module_version("1.2.3") == "1.2.3"


def test_validate_module_version_rejette_format_invalide():
    with pytest.raises(ModuleManifestError):
        validate_module_version("1.0")


# ---------------------------------------------------------------------------
# Validation — description
# ---------------------------------------------------------------------------


def test_description_vide_est_rejetee():
    with pytest.raises(ModuleManifestError, match="description"):
        validate_module_manifest(_valid_data(description=""))


def test_description_html_est_rejetee():
    with pytest.raises(ModuleManifestError, match="description"):
        validate_module_manifest(_valid_data(description="<p>Module</p>"))


def test_description_valide_acceptee():
    m = validate_module_manifest(_valid_data(description="Un module simple."))
    assert m.description == "Un module simple."


# ---------------------------------------------------------------------------
# Validation — provides
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", ALLOWED_PROVIDES)
def test_provides_valeur_connue_acceptee(value):
    data = _valid_data(provides=[value])
    if value == "routes":
        data["paths"] = {"routes": "routes.py"}
    m = validate_module_manifest(data)
    assert value in m.provides


def test_provides_liste_complete_acceptee():
    provides = list(ALLOWED_PROVIDES)
    m = validate_module_manifest(_valid_data(provides=provides, paths={"routes": "routes.py"}))
    assert set(m.provides) == ALLOWED_PROVIDES


def test_provides_non_liste_est_rejete():
    with pytest.raises(ModuleManifestError, match="provides"):
        validate_module_manifest(_valid_data(provides="entities"))


def test_provides_dict_est_rejete():
    with pytest.raises(ModuleManifestError, match="provides"):
        validate_module_manifest(_valid_data(provides={"entities": True}))


def test_provides_valeur_inconnue_est_rejetee():
    with pytest.raises(ModuleManifestError, match="provides"):
        validate_module_manifest(_valid_data(provides=["entities", "widgets"]))


def test_provides_tuple_est_accepte():
    m = validate_module_manifest(_valid_data(provides=("entities", "views")))
    assert "entities" in m.provides
    assert "views" in m.provides


# ---------------------------------------------------------------------------
# Validation — paths
# ---------------------------------------------------------------------------


def test_paths_valide_accepte():
    data = _valid_data(paths={"entities": "entities", "routes": "routes.py"})
    m = validate_module_manifest(data)
    assert m.paths["entities"] == "entities"
    assert m.paths["routes"] == "routes.py"


def test_paths_routes_obligatoire_si_provides_routes():
    with pytest.raises(ModuleManifestError, match="paths.routes"):
        validate_module_manifest(_valid_data(provides=["routes"], paths={}))


def test_paths_non_dict_est_rejete():
    with pytest.raises(ModuleManifestError, match="paths"):
        validate_module_manifest(_valid_data(paths=["entities"]))


def test_paths_chemin_absolu_unix_est_rejete():
    with pytest.raises(ModuleManifestError):
        validate_module_manifest(_valid_data(paths={"entities": "/etc/entities"}))


def test_paths_chemin_absolu_windows_est_rejete():
    with pytest.raises(ModuleManifestError):
        validate_module_manifest(_valid_data(paths={"entities": "C:/entities"}))


def test_paths_double_point_est_rejete():
    with pytest.raises(ModuleManifestError):
        validate_module_manifest(_valid_data(paths={"entities": "../entities"}))


def test_paths_url_est_rejetee():
    with pytest.raises(ModuleManifestError):
        validate_module_manifest(_valid_data(paths={"docs": "https://example.com/docs"}))


def test_paths_double_point_en_sous_chemin_est_rejete():
    with pytest.raises(ModuleManifestError):
        validate_module_manifest(_valid_data(paths={"entities": "sub/../entities"}))


# ---------------------------------------------------------------------------
# load_module_manifest
# ---------------------------------------------------------------------------


def test_load_module_manifest_lit_fichier_valide(tmp_path):
    data = _valid_data(
        provides=["entities"],
        paths={"entities": "entities"},
    )
    f = tmp_path / "module.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    m = load_module_manifest(f)
    assert m.name == "agenda"
    assert "entities" in m.provides


def test_load_module_manifest_refuse_json_invalide(tmp_path):
    f = tmp_path / "module.json"
    f.write_text("{invalid json", encoding="utf-8")
    with pytest.raises(ModuleManifestError, match="JSON"):
        load_module_manifest(f)


def test_load_module_manifest_refuse_fichier_inexistant(tmp_path):
    with pytest.raises(ModuleManifestError):
        load_module_manifest(tmp_path / "absent.json")


def test_load_module_manifest_refuse_manifeste_invalide(tmp_path):
    f = tmp_path / "module.json"
    f.write_text(json.dumps({"name": "agenda"}), encoding="utf-8")
    with pytest.raises(ModuleManifestError):
        load_module_manifest(f)


# ---------------------------------------------------------------------------
# API publique importable depuis core.modules
# ---------------------------------------------------------------------------


def test_api_publique_importable():
    from core.modules import (
        ALLOWED_PROVIDES,
        ModuleManifest,
        ModuleManifestError,
        load_module_manifest,
        validate_module_manifest,
        validate_module_name,
        validate_module_version,
    )
    assert ModuleManifest is not None
    assert ModuleManifestError is not None
    assert callable(validate_module_name)
    assert callable(validate_module_version)
    assert callable(validate_module_manifest)
    assert callable(load_module_manifest)
    assert isinstance(ALLOWED_PROVIDES, frozenset)


# ---------------------------------------------------------------------------
# Audit : aucune commande CLI, aucun fichier mvc/ modifié, aucune installation
# ---------------------------------------------------------------------------


def test_aucune_commande_cli_dans_le_module():
    import core.modules.manifest as mod
    source = open(mod.__file__).read()
    assert "argparse" not in source
    assert "sys.argv" not in source
    assert "module:install" not in source
    assert "module:list" not in source


def test_aucun_acces_mvc_dans_le_module():
    import core.modules.manifest as mod
    source = open(mod.__file__).read()
    assert "mvc/" not in source
    assert "mvc/routes" not in source


def test_aucune_installation_de_fichiers_dans_le_module():
    import core.modules.manifest as mod
    source = open(mod.__file__).read()
    assert "shutil" not in source
    assert "copytree" not in source
    assert "copyfile" not in source
