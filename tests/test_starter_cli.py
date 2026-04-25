"""Tests pour forge starter:list."""

from __future__ import annotations

import sys

import pytest

from forge_cli.starters import STARTERS, cmd_starter_list


def test_quatre_starters_definis():
    assert len(STARTERS) == 4


def test_niveaux_ordonnes_de_1_a_4():
    levels = [s[0] for s in STARTERS]
    assert levels == [1, 2, 3, 4]


def test_starter_list_affiche_les_4_niveaux(capsys):
    cmd_starter_list()
    output = capsys.readouterr().out
    for level, _, name, _ in STARTERS:
        assert str(level) in output
        assert name in output


def test_starter_list_contient_docs_urls(capsys):
    cmd_starter_list()
    output = capsys.readouterr().out
    assert "caucrogegit.github.io" in output
    assert "starter-app" in output


def test_starter_list_contient_niveau_mot_cle(capsys):
    cmd_starter_list()
    output = capsys.readouterr().out
    assert "Niveau" in output


def test_entrypoint_starter_list_accessible(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forge", "starter:list"])
    import forge
    forge.main()
    output, _ = capsys.readouterr()
    assert "Niveau" in output
    assert "Niveau 4" in output
