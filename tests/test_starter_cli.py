"""Tests pour forge starter:list et forge starter:build."""

from __future__ import annotations

import sys

import pytest

from forge_cli.starters import cmd_starter_build, cmd_starter_list
from forge_cli.starters.registry import all_starters, resolve


def test_quatre_starters_definis():
    assert len(all_starters()) == 4


def test_niveaux_ordonnes_de_1_a_4():
    levels = [s["number"] for s in all_starters()]
    assert levels == [1, 2, 3, 4]


def test_starter_list_affiche_les_4_niveaux(capsys):
    cmd_starter_list()
    output = capsys.readouterr().out
    for starter in all_starters():
        assert str(starter["number"]) in output
        assert starter["name"] in output


def test_starter_list_contient_docs_urls(capsys):
    cmd_starter_list()
    output = capsys.readouterr().out
    assert "caucrogegit.github.io" in output
    assert "starter-app" in output


def test_starter_list_contient_niveau_mot_cle(capsys):
    cmd_starter_list()
    output = capsys.readouterr().out
    assert "Starter apps Forge" in output
    assert "disponible" in output
    assert "à venir" in output


def test_alias_contacts_resolvent_le_meme_starter():
    ids = [resolve(identifier)["id"] for identifier in ("1", "contacts", "contact-simple")]
    assert ids == ["contact-simple", "contact-simple", "contact-simple"]


def test_starter_2_disponible_et_3_4_coming_soon():
    statuses = {starter["number"]: starter["status"] for starter in all_starters()}
    assert statuses[1] == "available"
    assert statuses[2] == "available"
    assert statuses[3] == "coming_soon"
    assert statuses[4] == "coming_soon"


def test_alias_utilisateurs_auth_resolvent_le_meme_starter():
    ids = [
        resolve(identifier)["id"]
        for identifier in ("2", "auth", "utilisateurs", "utilisateurs-auth")
    ]
    assert ids == [
        "utilisateurs-auth",
        "utilisateurs-auth",
        "utilisateurs-auth",
        "utilisateurs-auth",
    ]


@pytest.mark.parametrize("identifier", ["2", "auth", "utilisateurs-auth"])
def test_starter_build_auth_dry_run_fonctionne(identifier, capsys):
    cmd_starter_build([identifier, "--dry-run"])
    output = capsys.readouterr().out
    assert "Utilisateurs / authentification" in output
    assert "mvc/controllers/auth_controller.py" in output
    assert "Aucun fichier écrit" in output


def test_starter_build_auth_public_refuse(capsys):
    with pytest.raises(SystemExit) as exc:
        cmd_starter_build(["2", "--public"])

    assert exc.value.code == 1
    output = capsys.readouterr().out
    assert "--public n'est pas applicable" in output


def test_starter_build_refuse_un_starter_coming_soon(capsys):
    with pytest.raises(SystemExit) as exc:
        cmd_starter_build(["3", "--dry-run"])

    assert exc.value.code == 1
    output = capsys.readouterr().out
    assert "n'est pas encore disponible" in output
    assert "forge starter:list" in output


def test_entrypoint_starter_list_accessible(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forge", "starter:list"])
    import forge
    forge.main()
    output, _ = capsys.readouterr()
    assert "Starter apps Forge" in output
    assert "Suivi comportement élèves" in output
