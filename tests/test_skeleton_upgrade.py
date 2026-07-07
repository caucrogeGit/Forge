"""FORGE-9 — `forge skeleton:upgrade` monte le squelette d'un projet existant.

Write-if-new strict : ajoute les fichiers du squelette manquants, ne modifie ni
n'écrase jamais un fichier existant. `--check` liste sans écrire.
"""
from __future__ import annotations

from pathlib import Path

from cli.commands import skeleton_upgrade as su
from skeleton import materialize


def _project(tmp_path: Path) -> Path:
    materialize(tmp_path)
    return tmp_path


def test_plan_et_apply_ajoutent_les_fichiers_manquants(tmp_path: Path):
    _project(tmp_path)
    (tmp_path / "Makefile").unlink(missing_ok=True)
    (tmp_path / ".editorconfig").unlink(missing_ok=True)

    to_add, present = su.plan_upgrade(tmp_path)
    assert "Makefile" in to_add and ".editorconfig" in to_add
    assert "config.py" in present  # un fichier déjà là

    added = su.apply_upgrade(tmp_path)
    assert "Makefile" in added and ".editorconfig" in added
    assert (tmp_path / "Makefile").exists()


def test_write_if_new_ne_modifie_pas_l_existant(tmp_path: Path):
    _project(tmp_path)
    config = tmp_path / "config.py"
    config.write_text("# mon édition\n", encoding="utf-8")

    added = su.apply_upgrade(tmp_path)
    assert "config.py" not in added
    assert config.read_text(encoding="utf-8") == "# mon édition\n"  # préservé


def test_idempotent(tmp_path: Path):
    _project(tmp_path)
    su.apply_upgrade(tmp_path)
    to_add, _ = su.plan_upgrade(tmp_path)
    assert to_add == []


def test_main_check_liste_sans_ecrire(tmp_path: Path, monkeypatch, capsys):
    _project(tmp_path)
    (tmp_path / "Makefile").unlink(missing_ok=True)
    monkeypatch.chdir(tmp_path)

    su.main(["--check"])
    out = capsys.readouterr().out
    assert "Makefile" in out and "CHECK" in out
    assert (tmp_path / "Makefile").exists() is False  # --check n'écrit pas


def test_main_hors_projet_erreur(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)  # dossier vide, pas un projet
    try:
        su.main([])
    except SystemExit as exc:
        assert exc.code == 1
    assert "aucun projet Forge" in capsys.readouterr().out
