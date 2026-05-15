"""Tests MODULE-SYSTEM-002 — découverte de modules Forge locaux."""

from __future__ import annotations

import json
from pathlib import Path


from core.modules import (
    ModuleManifest,
    discover_module_manifests,
    list_module_manifests,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_manifest(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def _valid_data(name: str = "agenda", **overrides) -> dict:
    base = {
        "name": name,
        "label": name.capitalize(),
        "version": "0.1.0",
        "description": f"Module {name}.",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Cas limites : dossier absent ou vide
# ---------------------------------------------------------------------------


def test_dossier_absent_retourne_listes_vides(tmp_path):
    valid, invalid = discover_module_manifests(tmp_path / "absent")
    assert valid == []
    assert invalid == []


def test_dossier_vide_retourne_listes_vides(tmp_path):
    valid, invalid = discover_module_manifests(tmp_path)
    assert valid == []
    assert invalid == []


def test_sous_dossier_sans_module_json_est_ignore(tmp_path):
    (tmp_path / "agenda").mkdir()
    valid, invalid = discover_module_manifests(tmp_path)
    assert valid == []
    assert invalid == []


# ---------------------------------------------------------------------------
# Détection de modules valides
# ---------------------------------------------------------------------------


def test_module_valide_est_detecte(tmp_path):
    mod = tmp_path / "agenda"
    mod.mkdir()
    _write_manifest(mod / "module.json", _valid_data("agenda"))
    valid, invalid = discover_module_manifests(tmp_path)
    assert len(valid) == 1
    assert valid[0].name == "agenda"


def test_plusieurs_modules_valides_sont_detectes(tmp_path):
    for name in ("agenda", "patrimoine"):
        d = tmp_path / name
        d.mkdir()
        _write_manifest(d / "module.json", _valid_data(name))
    valid, invalid = discover_module_manifests(tmp_path)
    assert len(valid) == 2


def test_retourne_des_module_manifest(tmp_path):
    mod = tmp_path / "agenda"
    mod.mkdir()
    _write_manifest(mod / "module.json", _valid_data("agenda"))
    valid, _ = discover_module_manifests(tmp_path)
    assert isinstance(valid[0], ModuleManifest)


def test_modules_retournes_par_ordre_alphabetique(tmp_path):
    for name in ("statistiques", "agenda", "patrimoine"):
        d = tmp_path / name
        d.mkdir()
        _write_manifest(d / "module.json", _valid_data(name))
    valid, _ = discover_module_manifests(tmp_path)
    names = [m.name for m in valid]
    assert names == sorted(names)


# ---------------------------------------------------------------------------
# Gestion des modules invalides
# ---------------------------------------------------------------------------


def test_module_json_invalide_est_signale(tmp_path):
    mod = tmp_path / "broken"
    mod.mkdir()
    _write_manifest(mod / "module.json", {"name": "broken"})
    valid, invalid = discover_module_manifests(tmp_path)
    assert valid == []
    assert len(invalid) == 1
    assert invalid[0][0] == "broken"
    assert isinstance(invalid[0][1], str)


def test_module_invalide_ne_bloque_pas_les_valides(tmp_path):
    (tmp_path / "broken").mkdir()
    _write_manifest((tmp_path / "broken") / "module.json", {"name": "broken"})
    (tmp_path / "agenda").mkdir()
    _write_manifest((tmp_path / "agenda") / "module.json", _valid_data("agenda"))
    valid, invalid = discover_module_manifests(tmp_path)
    assert len(valid) == 1
    assert len(invalid) == 1


def test_json_invalide_est_signale(tmp_path):
    mod = tmp_path / "syntaxerror"
    mod.mkdir()
    (mod / "module.json").write_text("{invalid json", encoding="utf-8")
    valid, invalid = discover_module_manifests(tmp_path)
    assert valid == []
    assert len(invalid) == 1
    assert invalid[0][0] == "syntaxerror"


# ---------------------------------------------------------------------------
# Pas de scan récursif
# ---------------------------------------------------------------------------


def test_pas_de_scan_recursif(tmp_path):
    nested = tmp_path / "parent" / "enfant"
    nested.mkdir(parents=True)
    _write_manifest(nested / "module.json", _valid_data("agenda"))
    valid, _ = discover_module_manifests(tmp_path)
    assert len(valid) == 0


def test_fichiers_a_la_racine_ignores(tmp_path):
    _write_manifest(tmp_path / "module.json", _valid_data("agenda"))
    valid, invalid = discover_module_manifests(tmp_path)
    assert valid == []
    assert invalid == []


# ---------------------------------------------------------------------------
# Aucune modification de fichiers
# ---------------------------------------------------------------------------


def test_aucun_fichier_cree(tmp_path):
    before = set(tmp_path.iterdir())
    discover_module_manifests(tmp_path)
    after = set(tmp_path.iterdir())
    assert before == after


def test_aucun_fichier_cree_avec_module_valide(tmp_path):
    mod = tmp_path / "agenda"
    mod.mkdir()
    _write_manifest(mod / "module.json", _valid_data("agenda"))
    before = set(tmp_path.rglob("*"))
    discover_module_manifests(tmp_path)
    after = set(tmp_path.rglob("*"))
    assert before == after


# ---------------------------------------------------------------------------
# list_module_manifests
# ---------------------------------------------------------------------------


def test_list_module_manifests_retourne_seulement_valides(tmp_path):
    (tmp_path / "broken").mkdir()
    _write_manifest((tmp_path / "broken") / "module.json", {"name": "broken"})
    (tmp_path / "agenda").mkdir()
    _write_manifest((tmp_path / "agenda") / "module.json", _valid_data("agenda"))
    result = list_module_manifests(tmp_path)
    assert len(result) == 1
    assert result[0].name == "agenda"


def test_list_module_manifests_dossier_absent(tmp_path):
    result = list_module_manifests(tmp_path / "absent")
    assert result == []


def test_list_module_manifests_retourne_liste(tmp_path):
    result = list_module_manifests(tmp_path)
    assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Audit : aucun accès mvc/, aucune écriture, aucune installation
# ---------------------------------------------------------------------------


def test_aucun_acces_mvc_dans_discovery():
    import core.modules.discovery as mod
    source = open(mod.__file__).read()
    assert "mvc/" not in source
    assert "shutil" not in source
    assert "copytree" not in source


def test_aucune_execution_de_code_module():
    import core.modules.discovery as mod
    source = open(mod.__file__).read()
    assert "importlib" not in source
    assert "exec(" not in source
    assert "eval(" not in source


# ---------------------------------------------------------------------------
# API publique importable depuis core.modules
# ---------------------------------------------------------------------------


def test_api_publique_importable():
    from core.modules import discover_module_manifests, list_module_manifests
    assert callable(discover_module_manifests)
    assert callable(list_module_manifests)
