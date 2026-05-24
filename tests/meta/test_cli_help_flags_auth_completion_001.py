"""Garde-fou CLI-HELP-FLAGS-AUTH-COMPLETION-001.

Vérifie que les 5 commandes Auth restantes (les auth:user:* gérées
nativement par argparse sont hors périmètre) ont une aide enrichie
cohérente et n'exécutent pas leur logique métier avec --help / -h :

    auth:init
    auth:doctor
    auth:status
    auth:list-sql
    auth:user:list

L'interception centrale (CLI-HELP-FLAGS-DISPATCHER-001) reste responsable
du fait que -h/--help ne lance rien. Ce test garantit que :
1. l'aide est utile et propre à chaque commande ;
2. auth:init annonce l'écriture de fichiers ;
3. auth:user:list annonce la dépendance à la base de données ;
4. les commandes auth:user:* natives (create/show/disable/enable/
   password/role:add/role:remove/roles) conservent leur aide argparse.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
FORGE_PY = PROJECT_ROOT / "forge.py"


AUTH_COMMANDS = [
    "auth:init",
    "auth:doctor",
    "auth:status",
    "auth:list-sql",
    "auth:user:list",
]


# Mot-clé propre à chaque commande (au moins un doit apparaître dans l'aide).
COMMAND_KEYWORDS = {
    "auth:init":      ["auth", "initialise", "sql"],
    "auth:doctor":    ["doctor", "diagnostic"],
    "auth:status":    ["status", "état", "etat"],
    "auth:list-sql":  ["sql"],
    "auth:user:list": ["utilisateur", "users", "comptes"],
}


# Marqueurs spécifiques aux SORTIES réelles des commandes Auth. Choisis
# pour ne PAS coïncider avec le vocabulaire normal (le mot « auth »,
# « sql » ou « utilisateur » peut figurer dans l'aide).
SIDE_EFFECT_MARKERS = [
    "[OK]",
    "[ERREUR]",
    "[WARN]",
    "[FAIL]",
    "[SKIP]",
    "[INFO]",
    "Forge auth:init",
    "Forge auth:doctor — diagnostic",
    "Forge auth:status — socle",
    "Forge auth:list-sql — SQL",
    "Forge auth:user:list",
    "Aucun utilisateur local.",
    "Aucun secret, token ou hash",
    "avertissement(s),",
]


# Liste de commandes auth:user:* natives argparse qui doivent rester
# inchangées (leur aide vient de argparse, pas du dispatcher).
ARGPARSE_NATIVE_USER_COMMANDS = [
    "auth:user:create",
    "auth:user:show",
    "auth:user:disable",
    "auth:user:enable",
    "auth:user:password",
    "auth:user:role:add",
    "auth:user:role:remove",
    "auth:user:roles",
]


def _run_forge(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(FORGE_PY), *args],
        capture_output=True, text=True, timeout=15,
    )


class TestAuthCommandsExitZero:
    """`--help` et `-h` retournent 0 pour chaque commande."""

    @pytest.mark.parametrize("command", AUTH_COMMANDS)
    def test_long_form(self, command: str):
        result = _run_forge(command, "--help")
        assert result.returncode == 0, (
            f"forge {command} --help doit retourner 0. "
            f"stderr={result.stderr!r}"
        )

    @pytest.mark.parametrize("command", AUTH_COMMANDS)
    def test_short_form(self, command: str):
        result = _run_forge(command, "-h")
        assert result.returncode == 0, (
            f"forge {command} -h doit retourner 0. "
            f"stderr={result.stderr!r}"
        )


class TestAuthCommandsHelpStructure:
    @pytest.mark.parametrize("command", AUTH_COMMANDS)
    def test_has_usage_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Usage:" in out, f"{command} : section Usage: manquante."
        assert f"forge {command}" in out, (
            f"{command} : l'aide doit citer `forge {command}`."
        )

    @pytest.mark.parametrize("command", AUTH_COMMANDS)
    def test_has_description_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Description:" in out, (
            f"{command} : section Description: manquante."
        )

    @pytest.mark.parametrize("command", AUTH_COMMANDS)
    def test_has_options_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Options:" in out, (
            f"{command} : section Options: manquante."
        )
        assert "--help" in out, (
            f"{command} : le flag --help doit être documenté."
        )

    @pytest.mark.parametrize("command", AUTH_COMMANDS)
    def test_mentions_no_execution(self, command: str):
        out = _run_forge(command, "--help").stdout.lower()
        assert "sans exécuter" in out, (
            f"{command} : l'aide doit rappeler que --help n'exécute rien."
        )


class TestAuthCommandsHelpHasKeyword:
    @pytest.mark.parametrize("command", AUTH_COMMANDS)
    def test_mentions_command_specific_keyword(self, command: str):
        out = _run_forge(command, "--help").stdout.lower()
        keywords = [k.lower() for k in COMMAND_KEYWORDS[command]]
        found = [k for k in keywords if k in out]
        assert found, (
            f"{command} : aucun mot-clé attendu trouvé ({keywords}) "
            f"dans l'aide."
        )


class TestAuthInitAnnouncesFileWrite:
    """auth:init écrit plusieurs fichiers SQL — l'aide doit le dire."""

    def test_help_mentions_write(self):
        out = _run_forge("auth:init", "--help").stdout.lower()
        write_markers = [
            "écrit", "crée", "génère", "write-if-new",
            "peut être modifié",
        ]
        found = [m for m in write_markers if m in out]
        assert found, (
            f"auth:init --help doit signaler qu'elle peut écrire des "
            f"fichiers (chercher un de : {write_markers}). Sortie : "
            f"{out[:300]!r}"
        )


class TestAuthUserListAnnouncesDbDependency:
    """auth:user:list lit la base — l'aide doit l'annoncer."""

    def test_help_mentions_db_dependency(self):
        out = _run_forge("auth:user:list", "--help").stdout.lower()
        db_markers = [
            "base", "db_app", "connexion", "select", "users",
        ]
        found = [m for m in db_markers if m in out]
        assert found, (
            f"auth:user:list --help doit signaler la dépendance à la "
            f"base de données (chercher un de : {db_markers}). Sortie : "
            f"{out[:300]!r}"
        )


class TestAuthCommandsNoSideEffects:
    @pytest.mark.parametrize("command", AUTH_COMMANDS)
    def test_no_execution_marker_in_output(self, command: str):
        result = _run_forge(command, "--help")
        combined = result.stdout + result.stderr
        offenders = [m for m in SIDE_EFFECT_MARKERS if m in combined]
        assert not offenders, (
            f"{command} : marqueurs d'exécution trouvés ({offenders}). "
            f"Sortie : {combined!r}"
        )


class TestArgparseNativeUserCommandsUnchanged:
    """Les auth:user:* natives argparse doivent garder leur aide argparse."""

    @pytest.mark.parametrize("command", ARGPARSE_NATIVE_USER_COMMANDS)
    def test_keeps_argparse_help(self, command: str):
        result = _run_forge(command, "--help")
        assert result.returncode == 0
        # Argparse imprime 'usage:' (minuscule) ; notre gabarit central
        # imprime 'Usage:' (majuscule + capitalisation Description:/
        # Options:). La présence du minuscule prouve qu'argparse a tourné.
        assert "usage: forge " + command in result.stdout, (
            f"{command} a perdu son aide argparse native. "
            f"Sortie : {result.stdout[:200]!r}"
        )
        # Garde-fou : aucune section « Description: » majuscule
        # caractéristique du gabarit du dispatcher.
        assert "Description:" not in result.stdout, (
            f"{command} a été indûment intercepté par le dispatcher "
            f"central, écrasant son aide argparse."
        )
