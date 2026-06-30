"""Garde-fou CLI-NEW-UNKNOWN-ARGS-001.

`forge new` doit refuser explicitement tout argument inconnu (option mal
orthographiée ou positionnel parasite) au lieu de l'ignorer silencieusement.
Seuls le nom du projet et `--profile <valeur>` sont acceptés.
"""
from __future__ import annotations

import importlib.util
import pathlib
from unittest.mock import patch

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _import_forge():
    spec = importlib.util.spec_from_file_location("forge", ROOT / "forge.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_main(forge, argv):
    with patch.object(forge.sys, "argv", ["forge", *argv]):
        forge.main()


@pytest.mark.parametrize("argv", [
    ["new", "Demo", "--no-git"],          # option inconnue
    ["new", "Demo", "--force"],           # option inconnue
    ["new", "Demo", "Extra"],             # positionnel parasite
    ["new", "Demo", "--profile", "minimal", "--no-git"],  # inconnu après --profile
])
def test_new_rejette_argument_inconnu(argv):
    """Un argument non reconnu fait échouer la commande sans créer de projet."""
    forge = _import_forge()
    with patch.object(forge, "cmd_new") as cmd_new:
        with pytest.raises(SystemExit) as exc:
            _run_main(forge, argv)
    cmd_new.assert_not_called()
    assert exc.value.code != 0


def test_new_message_mentionne_argument_inconnu(capsys):
    """Le message d'erreur nomme l'argument fautif (pas un échec silencieux)."""
    forge = _import_forge()
    with patch.object(forge, "cmd_new"):
        with pytest.raises(SystemExit):
            _run_main(forge, ["new", "Demo", "--no-git"])
    err = capsys.readouterr().err.lower()
    assert "inconnu" in err and "--no-git" in err


@pytest.mark.parametrize("argv,expected_profile", [
    (["new", "Demo"], None),
    (["new", "Demo", "--profile", "minimal"], "minimal"),
])
def test_new_accepte_arguments_valides(argv, expected_profile):
    """Le nom seul ou avec `--profile <valeur>` reste accepté."""
    forge = _import_forge()
    with patch.object(forge, "cmd_new") as cmd_new:
        _run_main(forge, argv)
    cmd_new.assert_called_once()
    if expected_profile is not None:
        assert cmd_new.call_args.kwargs.get("profile") == expected_profile
