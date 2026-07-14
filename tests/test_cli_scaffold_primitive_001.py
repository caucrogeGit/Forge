"""Tests — CLI-SCAFFOLD-PRIMITIVE-001 : primitive write-if-new partagée.

Verrouille la sémantique décidée : créé / préservé (identique) / averti
(différent, jamais écrasé), plus le mode dry-run.
"""
from __future__ import annotations

from pathlib import Path

from cli._support.scaffold import CREATED, PRESERVED, WARNED, write_if_new


def test_fichier_absent_est_cree(tmp_path: Path):
    target = tmp_path / "sub" / "f.py"
    assert write_if_new(target, "contenu\n") == CREATED
    assert target.read_text(encoding="utf-8") == "contenu\n"


def test_fichier_identique_est_preserve(tmp_path: Path):
    target = tmp_path / "f.py"
    target.write_text("contenu\n", encoding="utf-8")
    assert write_if_new(target, "contenu\n") == PRESERVED
    assert target.read_text(encoding="utf-8") == "contenu\n"


def test_fichier_different_est_averti_jamais_ecrase(tmp_path: Path):
    target = tmp_path / "f.py"
    target.write_text("# modifié par l'utilisateur\n", encoding="utf-8")
    assert write_if_new(target, "contenu généré\n") == WARNED
    # Jamais écrasé.
    assert target.read_text(encoding="utf-8") == "# modifié par l'utilisateur\n"


class TestDryRun:
    def test_absent_annonce_created_sans_ecrire(self, tmp_path: Path):
        target = tmp_path / "sub" / "f.py"
        assert write_if_new(target, "contenu\n", dry_run=True) == CREATED
        assert not target.exists()
        assert not target.parent.exists()  # pas de mkdir non plus

    def test_present_identique_reste_preserved(self, tmp_path: Path):
        target = tmp_path / "f.py"
        target.write_text("contenu\n", encoding="utf-8")
        assert write_if_new(target, "contenu\n", dry_run=True) == PRESERVED

    def test_present_different_reste_warned(self, tmp_path: Path):
        target = tmp_path / "f.py"
        target.write_text("autre\n", encoding="utf-8")
        assert write_if_new(target, "contenu\n", dry_run=True) == WARNED
        assert target.read_text(encoding="utf-8") == "autre\n"
