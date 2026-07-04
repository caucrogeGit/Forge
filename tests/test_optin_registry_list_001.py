"""OPTIN-REGISTRY-LIST-001 (ADR-061) — opt-in:list lit le registre du projet.

`forge opt-in:list` affiche l'état de tous les opt-ins d'après `optins/registry.py`
(inscrit / absent) et marque le backend BDD choisi (`BACKEND`). Lecture seule,
analyse de texte, sans importer de module de projet.
"""
from __future__ import annotations

from pathlib import Path


from cli.optins import enable, list as optin_list
from cli.optins.registry_format import REGISTRY_TEMPLATE


def _project(tmp_path: Path) -> Path:
    (tmp_path / "optins").mkdir()
    (tmp_path / "optins" / "registry.py").write_text(REGISTRY_TEMPLATE, encoding="utf-8")
    return tmp_path


def test_optin_library_absent_par_defaut(tmp_path, capsys):
    _project(tmp_path)
    optin_list.list_optins(project_root=tmp_path)
    out = capsys.readouterr().out
    # qrcode (library) non inscrit -> absent + conseil.
    assert "qrcode" in out
    assert "absent" in out
    assert "forge opt-in:enable qrcode --apply" in out


def test_optin_library_inscrit_apres_enable(tmp_path, monkeypatch, capsys):
    _project(tmp_path)
    monkeypatch.chdir(tmp_path)
    enable.main(["qrcode", "--apply"])
    capsys.readouterr()  # vide la sortie de enable
    optin_list.list_optins(project_root=tmp_path)
    out = capsys.readouterr().out
    lignes = [l for l in out.splitlines() if l.strip().startswith("qrcode")]
    assert lignes and "inscrit" in lignes[0]


def test_backend_choisi_marque(tmp_path, capsys):
    (tmp_path / "optins").mkdir()
    reg = REGISTRY_TEMPLATE.replace("BACKEND: str | None = None", 'BACKEND: str | None = "sqlite"')
    (tmp_path / "optins" / "registry.py").write_text(reg, encoding="utf-8")
    optin_list.list_optins(project_root=tmp_path)
    out = capsys.readouterr().out
    lignes = [l for l in out.splitlines() if l.strip().startswith("sqlite")]
    assert lignes and "choisi" in lignes[0]


def test_sans_registre_aucune_erreur(tmp_path, capsys):
    # Projet sans optins/registry.py : list reste en lecture seule, code 0.
    assert optin_list.list_optins(project_root=tmp_path) == 0
