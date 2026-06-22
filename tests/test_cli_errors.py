"""Tests unitaires pour cli._support.errors — helpers standardisés d'erreur CLI."""

from __future__ import annotations

import sys

import pytest

from cli._support.errors import cli_error, cli_fail


# ── cli_error ─────────────────────────────────────────────────────────────────

def test_cli_error_ecrit_sur_stderr(capsys):
    cli_error("quelque chose a mal tourné")
    err = capsys.readouterr().err
    assert "Erreur :" in err
    assert "quelque chose a mal tourné" in err


def test_cli_error_pas_de_conseil_si_hint_vide(capsys):
    cli_error("problème")
    err = capsys.readouterr().err
    assert "Conseil" not in err


def test_cli_error_avec_hint_ecrit_conseil(capsys):
    cli_error("problème", hint="vérifiez ceci")
    err = capsys.readouterr().err
    assert "Conseil :" in err
    assert "vérifiez ceci" in err


def test_cli_error_ne_termine_pas_le_processus(capsys):
    cli_error("ne doit pas quitter")
    # Si on arrive ici, pas de SystemExit — c'est le comportement attendu


# ── cli_fail ──────────────────────────────────────────────────────────────────

def test_cli_fail_quitte_avec_code_1(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli_fail("erreur fatale")
    assert exc_info.value.code == 1


def test_cli_fail_code_personnalise(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli_fail("erreur fatale", code=2)
    assert exc_info.value.code == 2


def test_cli_fail_ecrit_erreur_sur_stderr(capsys):
    with pytest.raises(SystemExit):
        cli_fail("chose impossible")
    err = capsys.readouterr().err
    assert "Erreur :" in err
    assert "chose impossible" in err


def test_cli_fail_avec_hint_ecrit_conseil(capsys):
    with pytest.raises(SystemExit):
        cli_fail("problème", hint="essayez cela")
    err = capsys.readouterr().err
    assert "Conseil :" in err
    assert "essayez cela" in err


def test_cli_fail_sans_hint_pas_de_conseil(capsys):
    with pytest.raises(SystemExit):
        cli_fail("problème sans conseil")
    err = capsys.readouterr().err
    assert "Conseil" not in err


# ── intégration : commande inconnue ───────────────────────────────────────────

def test_commande_inconnue_quitte_avec_code_1(monkeypatch):
    import forge
    monkeypatch.setattr(sys, "argv", ["forge", "commande:inexistante"])
    with pytest.raises(SystemExit) as exc_info:
        forge.main()
    assert exc_info.value.code == 1


def test_commande_inconnue_ecrit_erreur_sur_stderr(monkeypatch, capsys):
    import forge
    monkeypatch.setattr(sys, "argv", ["forge", "commande:inexistante"])
    with pytest.raises(SystemExit):
        forge.main()
    err = capsys.readouterr().err
    assert "Erreur :" in err
