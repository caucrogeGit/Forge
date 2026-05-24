"""Garde-fou CLI-HELP-FLAGS-MIGRATIONS-001.

Vérifie que les 3 commandes Migrations restantes (migration:make a déjà
un --help natif) ont une aide enrichie cohérente et n'exécutent pas
leur logique métier avec --help / -h :

    migration:status
    migration:apply
    migration:diff

L'interception centrale (CLI-HELP-FLAGS-DISPATCHER-001) reste responsable
du fait que -h/--help ne lance rien. Ce test garantit que :
1. l'aide est utile et propre à chaque commande ;
2. migration:apply rappelle explicitement qu'elle modifie la base.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
FORGE_PY = PROJECT_ROOT / "forge.py"


MIGRATION_COMMANDS = [
    "migration:status",
    "migration:apply",
    "migration:diff",
]


# Mot-clé propre à chaque commande (au moins un doit apparaître dans l'aide).
COMMAND_KEYWORDS = {
    "migration:status": ["status", "état", "statut"],
    "migration:apply":  ["applique", "base de données"],
    "migration:diff":   ["diff", "comparaison", "compare"],
}


# Marqueurs spécifiques aux SORTIES réelles des commandes. Choisis pour
# ne pas coïncider avec le vocabulaire de description. Les mots normaux
# comme « base de données » sont tolérés.
SIDE_EFFECT_MARKERS = [
    "[OK]",
    "[ERREUR]",
    "[INFO]",
    "[EXECUTE]",
    "Statut des migrations.",
    "Application des migrations.",
    "migration(s) appliquée(s)",
    "Aucune migration à appliquer.",
    "Aucune migration trouvée.",
    "Dossier mvc/migrations absent",
]


def _run_forge(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(FORGE_PY), *args],
        capture_output=True, text=True, timeout=15,
    )


class TestMigrationCommandsExitZero:
    """`--help` et `-h` retournent 0 pour chaque commande."""

    @pytest.mark.parametrize("command", MIGRATION_COMMANDS)
    def test_long_form(self, command: str):
        result = _run_forge(command, "--help")
        assert result.returncode == 0, (
            f"forge {command} --help doit retourner 0. "
            f"stderr={result.stderr!r}"
        )

    @pytest.mark.parametrize("command", MIGRATION_COMMANDS)
    def test_short_form(self, command: str):
        result = _run_forge(command, "-h")
        assert result.returncode == 0, (
            f"forge {command} -h doit retourner 0. "
            f"stderr={result.stderr!r}"
        )


class TestMigrationCommandsHelpStructure:
    """Chaque aide contient les sections attendues."""

    @pytest.mark.parametrize("command", MIGRATION_COMMANDS)
    def test_has_usage_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Usage:" in out, f"{command} : section Usage: manquante."
        assert f"forge {command}" in out, (
            f"{command} : l'aide doit citer `forge {command}`."
        )

    @pytest.mark.parametrize("command", MIGRATION_COMMANDS)
    def test_has_description_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Description:" in out, (
            f"{command} : section Description: manquante."
        )

    @pytest.mark.parametrize("command", MIGRATION_COMMANDS)
    def test_has_options_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Options:" in out, (
            f"{command} : section Options: manquante."
        )
        assert "--help" in out, (
            f"{command} : le flag --help doit être documenté."
        )

    @pytest.mark.parametrize("command", MIGRATION_COMMANDS)
    def test_mentions_no_execution(self, command: str):
        out = _run_forge(command, "--help").stdout.lower()
        assert "sans exécuter" in out, (
            f"{command} : l'aide doit rappeler que --help n'exécute rien."
        )


class TestMigrationCommandsHelpHasKeyword:
    @pytest.mark.parametrize("command", MIGRATION_COMMANDS)
    def test_mentions_command_specific_keyword(self, command: str):
        out = _run_forge(command, "--help").stdout.lower()
        keywords = [k.lower() for k in COMMAND_KEYWORDS[command]]
        found = [k for k in keywords if k in out]
        assert found, (
            f"{command} : aucun mot-clé attendu trouvé ({keywords}) "
            f"dans l'aide."
        )


class TestMigrationCommandsNoSideEffects:
    """L'enrichissement n'a pas réintroduit d'effet de bord."""

    @pytest.mark.parametrize("command", MIGRATION_COMMANDS)
    def test_no_execution_marker_in_output(self, command: str):
        result = _run_forge(command, "--help")
        combined = result.stdout + result.stderr
        offenders = [m for m in SIDE_EFFECT_MARKERS if m in combined]
        assert not offenders, (
            f"{command} : marqueurs d'exécution trouvés ({offenders}). "
            f"Sortie : {combined!r}"
        )


class TestMigrationApplyMentionsRealRisk:
    """migration:apply doit clarifier qu'elle modifie réellement la base."""

    def test_help_mentions_real_db_modification(self):
        out = _run_forge("migration:apply", "--help").stdout.lower()
        risk_markers = ["modifie", "base de données", "sql", "applique"]
        found = [m for m in risk_markers if m in out]
        assert found, (
            "migration:apply --help doit clarifier qu'elle modifie la "
            f"base (chercher un de : {risk_markers}). Sortie : {out!r}"
        )
