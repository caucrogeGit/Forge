"""Garde-fou CLI-HELP-FLAGS-INIT-COMMANDS-001.

Vérifie que les 6 commandes `*:init` à effets de bord critiques ont une
aide enrichie cohérente, et que cette aide ne déclenche aucune logique
métier (l'interception centrale du dispatcher fait son travail).

Le test étend CLI-HELP-FLAGS-DISPATCHER-001 :
- DISPATCHER-001 garantit `exit 0` + pas d'effet de bord.
- INIT-COMMANDS-001 garantit en plus que l'aide est utile : sections
  Usage / Description / Options, et un mot-clé propre à chaque commande
  (MariaDB pour db:init, storage/mail pour mail:init, etc.).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
FORGE_PY = PROJECT_ROOT / "forge.py"


INIT_COMMANDS = [
    "db:init",
    "mail:init",
    "i18n:init",
    "upload:init",
    "media:init",
    "deploy:init",
]


# Mot-clé propre à chaque commande (vérifie que l'aide est bien celle
# attendue, pas le template générique d'une autre commande).
COMMAND_KEYWORDS = {
    "db:init":     ["mariadb", "base"],
    "mail:init":   ["mail", "storage/mail"],
    "i18n:init":   ["translations", "traduction"],
    "upload:init": ["storage/uploads", "upload"],
    "media:init":  ["media", "uploads"],
    "deploy:init": ["deploy", "déploiement"],
}


# Marqueurs qui apparaîtraient si la logique métier s'était exécutée.
# Tolère les emplois en *texte d'aide* (« Provisionne MariaDB », « crée
# storage/mail/ ») mais bannit les marqueurs de sortie exécution :
# [OK], [ERREUR], [PRÉSERVÉ], « Dossier prêt », « Provisioning MariaDB
# impossible » (caractéristique d'un vrai échec d'init).
SIDE_EFFECT_MARKERS = [
    "[OK]",
    "[ERREUR]",
    "[PRÉSERVÉ]",
    "Dossier prêt",
    "Provisioning MariaDB impossible",
    "exécutée",
]


def _run_forge(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(FORGE_PY), *args],
        capture_output=True, text=True, timeout=15,
    )


class TestInitCommandsExitZero:
    """`--help` et `-h` retournent 0 pour chaque commande init."""

    @pytest.mark.parametrize("command", INIT_COMMANDS)
    def test_long_form(self, command: str):
        result = _run_forge(command, "--help")
        assert result.returncode == 0, (
            f"forge {command} --help doit retourner 0. "
            f"stderr={result.stderr!r}"
        )

    @pytest.mark.parametrize("command", INIT_COMMANDS)
    def test_short_form(self, command: str):
        result = _run_forge(command, "-h")
        assert result.returncode == 0, (
            f"forge {command} -h doit retourner 0. "
            f"stderr={result.stderr!r}"
        )


class TestInitCommandsHelpStructure:
    """Chaque aide contient les sections attendues."""

    @pytest.mark.parametrize("command", INIT_COMMANDS)
    def test_help_has_usage_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Usage:" in out, f"{command} : section Usage: manquante."
        assert f"forge {command}" in out, (
            f"{command} : l'aide doit citer `forge {command}`."
        )

    @pytest.mark.parametrize("command", INIT_COMMANDS)
    def test_help_has_description_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Description:" in out, (
            f"{command} : section Description: manquante."
        )

    @pytest.mark.parametrize("command", INIT_COMMANDS)
    def test_help_has_options_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Options:" in out, (
            f"{command} : section Options: manquante."
        )
        assert "--help" in out, (
            f"{command} : le flag --help doit être documenté."
        )


class TestInitCommandsHelpHasKeyword:
    """Chaque aide contient au moins un mot-clé propre à la commande."""

    @pytest.mark.parametrize("command", INIT_COMMANDS)
    def test_help_mentions_command_specific_keyword(self, command: str):
        out = _run_forge(command, "--help").stdout.lower()
        keywords = [k.lower() for k in COMMAND_KEYWORDS[command]]
        found = [k for k in keywords if k in out]
        assert found, (
            f"{command} : aucun mot-clé attendu trouvé ({keywords}) "
            f"dans l'aide. Indication d'un copier-coller incorrect entre "
            f"commandes."
        )


class TestInitCommandsNoSideEffects:
    """L'enrichissement n'a pas réintroduit d'effet de bord."""

    @pytest.mark.parametrize("command", INIT_COMMANDS)
    def test_no_execution_marker_in_output(self, command: str):
        result = _run_forge(command, "--help")
        combined = result.stdout + result.stderr
        offenders = [m for m in SIDE_EFFECT_MARKERS if m in combined]
        assert not offenders, (
            f"{command} : marqueurs d'exécution trouvés ({offenders}). "
            f"Sortie : {combined!r}"
        )


class TestInitCommandsHelpReminder:
    """L'aide rappelle que --help n'exécute rien."""

    @pytest.mark.parametrize("command", INIT_COMMANDS)
    def test_help_text_mentions_no_execution(self, command: str):
        out = _run_forge(command, "--help").stdout.lower()
        # Phrase canonique du gabarit riche : « Affiche cette aide sans
        # exécuter la commande. »
        assert "sans exécuter" in out, (
            f"{command} : l'aide doit rappeler que --help n'exécute rien."
        )
