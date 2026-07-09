"""Tests pour les conseils de récupération dans les erreurs CLI Forge.

Ces tests vérifient que les erreurs fréquentes contiennent des conseils
d'action concrets, pas seulement un message d'erreur brut.
"""

from __future__ import annotations

import sys

import pytest

import forge


# ── Commande inconnue ─────────────────────────────────────────────────────────

def test_commande_inconnue_contient_erreur(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forge", "commande:inconnue"])
    with pytest.raises(SystemExit):
        forge.main()
    assert "Erreur :" in capsys.readouterr().err


def test_commande_inconnue_conseil_pointe_help(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forge", "commande:inconnue"])
    with pytest.raises(SystemExit):
        forge.main()
    assert "Conseil :" in capsys.readouterr().err


def test_commande_inconnue_mentionne_forge_help(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forge", "truc:invalide"])
    with pytest.raises(SystemExit):
        forge.main()
    err = capsys.readouterr().err
    assert "forge help" in err or "--help" in err


# ── forge new — argument manquant ─────────────────────────────────────────────

def test_forge_new_sans_arg_conseil_avec_exemple(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forge", "new"])
    with pytest.raises(SystemExit) as exc_info:
        forge.main()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "Erreur :" in err
    assert "Conseil :" in err
    assert "forge new" in err


def test_forge_new_sans_arg_exemple_concret(monkeypatch, capsys):
    """L'exemple dans le conseil doit contenir un nom de projet plausible."""
    monkeypatch.setattr(sys, "argv", ["forge", "new"])
    with pytest.raises(SystemExit):
        forge.main()
    err = capsys.readouterr().err
    assert "Exemple" in err or "exemple" in err


def test_forge_new_profile_sans_valeur_conseil(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forge", "new", "MonProjet", "--profile"])
    with pytest.raises(SystemExit) as exc_info:
        forge.main()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "Conseil :" in err
    assert "profil" in err.lower() or "profile" in err.lower()


# ── forge make:entity — argument manquant ─────────────────────────────────────

# make:entity / make:crud sont gatées sur forge-mvc-entities (ADR-070), mais le
# cœur garde un garde d'argument : sans nom d'entité, il conseille l'usage avant
# de déléguer au moteur d'entités (le handler basculerait sinon en interactif).

def test_forge_make_entity_sans_arg_conseil(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forge", "make:entity"])
    with pytest.raises(SystemExit) as exc_info:
        forge.main()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "Erreur :" in err
    assert "Conseil :" in err


def test_forge_make_entity_sans_arg_exemple_avec_nom(monkeypatch, capsys):
    """L'exemple dans le conseil doit contenir un nom d'entité."""
    monkeypatch.setattr(sys, "argv", ["forge", "make:entity"])
    with pytest.raises(SystemExit):
        forge.main()
    err = capsys.readouterr().err
    assert "make:entity" in err
    assert "Contact" in err or "Exemple" in err


# ── forge make:crud — argument manquant ───────────────────────────────────────

def test_forge_make_crud_sans_arg_conseil(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forge", "make:crud"])
    with pytest.raises(SystemExit) as exc_info:
        forge.main()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "Erreur :" in err
    assert "Conseil :" in err


def test_forge_make_crud_sans_arg_exemple_avec_nom(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forge", "make:crud"])
    with pytest.raises(SystemExit):
        forge.main()
    err = capsys.readouterr().err
    assert "Contact" in err or "Exemple" in err


# ── forge routes:list — trop d'arguments ──────────────────────────────────────

def test_forge_routes_list_trop_args_conseil(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forge", "routes:list", "extra"])
    with pytest.raises(SystemExit) as exc_info:
        forge.main()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "Erreur :" in err
    assert "Conseil :" in err


# ── forge project:check — hors projet ─────────────────────────────────────────

def test_project_check_hors_projet_conseil_forge_new(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        forge.cmd_project_check()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "Conseil :" in err
    assert "forge new" in err


def test_project_check_hors_projet_code_sortie_1(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        forge.cmd_project_check()
    assert exc_info.value.code == 1


# ── codes de sortie inchangés ─────────────────────────────────────────────────

def test_codes_sortie_erreurs_restent_a_1(monkeypatch, capsys):
    """Les conseils de récupération ne changent pas le code de sortie."""
    for command in (["new"], ["make:entity"], ["make:crud"]):
        monkeypatch.setattr(sys, "argv", ["forge"] + command)
        with pytest.raises(SystemExit) as exc_info:
            forge.main()
        assert exc_info.value.code == 1, f"code attendu 1 pour forge {' '.join(command)}"
