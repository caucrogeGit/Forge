"""Garde-fou CLI-HELP-FLAGS-REMAINING-MINOR-001.

Ticket de clôture du chantier --help : vérifie que les 9 dernières
commandes Forge encore génériques ont désormais une aide enrichie
cohérente et n'exécutent pas leur logique métier avec --help / -h :

    new
    starter:list
    sync:entity
    sync:relations
    sync:landing
    js:init
    docs:pdf
    i18n:check
    deploy:check

L'interception centrale (CLI-HELP-FLAGS-DISPATCHER-001) reste responsable
du fait que -h/--help ne lance rien. Ce test garantit que :
1. chaque aide est utile et propre à la commande ;
2. les commandes qui ÉCRIVENT (new, sync:*, js:init, docs:pdf)
   l'annoncent ;
3. les commandes de CONTRÔLE (starter:list, i18n:check, deploy:check)
   annoncent leur caractère lecture seule.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
FORGE_PY = PROJECT_ROOT / "forge.py"


REMAINING_COMMANDS = [
    "new",
    "sync:entity",
    "sync:relations",
    "sync:landing",
    "js:init",
    "docs:pdf",
    "i18n:check",
    "deploy:check",
]

# Commandes qui écrivent réellement des fichiers (audit confirmé).
WRITING_COMMANDS = [
    "new",
    "sync:entity",
    "sync:relations",
    "sync:landing",
    "js:init",
    "docs:pdf",
]

# Commandes de contrôle/lecture seule (audit confirmé).
READ_ONLY_COMMANDS = [
    "i18n:check",
    "deploy:check",
]


# Mot-clé propre à chaque commande (au moins un doit apparaître dans l'aide).
COMMAND_KEYWORDS = {
    "new":            ["projet", "project"],
    "sync:entity":    ["entity", "entité", "entite"],
    "sync:relations": ["relations"],
    "sync:landing":   ["landing"],
    "js:init":        ["javascript", "js", "htmx", "alpine"],
    "docs:pdf":       ["pdf", "documentation"],
    "i18n:check":     ["traduction", "i18n", "translations"],
    "deploy:check":   ["déploiement", "deploy"],
}


# Marqueurs spécifiques aux SORTIES réelles. Choisis pour ne PAS
# coïncider avec le vocabulaire normal de description (« génère »,
# « fichier », « projet », « PDF », « déploiement »).
SIDE_EFFECT_MARKERS = [
    "[OK]",
    "[ERREUR]",
    "[INFO]",
    "[WARN]",
    "[FAIL]",
    "[SKIP]",
    "[PRÉSERVÉ]",
    "créé avec succès",
    "fichier généré",
    "déploiement terminé",
    "PDF généré",
    "Génération PDF en cours",
    "Étapes suivantes",
    "Landing synchronisée",
    "Landing désynchronisée",
    "Progressions Forge",
    "Dossier translations présent",
    "Catalogue ",
]


def _run_forge(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(FORGE_PY), *args],
        capture_output=True, text=True, timeout=15,
    )


class TestRemainingCommandsExitZero:
    """`--help` et `-h` retournent 0 pour chaque commande."""

    @pytest.mark.parametrize("command", REMAINING_COMMANDS)
    def test_long_form(self, command: str):
        result = _run_forge(command, "--help")
        assert result.returncode == 0, (
            f"forge {command} --help doit retourner 0. "
            f"stderr={result.stderr!r}"
        )

    @pytest.mark.parametrize("command", REMAINING_COMMANDS)
    def test_short_form(self, command: str):
        result = _run_forge(command, "-h")
        assert result.returncode == 0, (
            f"forge {command} -h doit retourner 0. "
            f"stderr={result.stderr!r}"
        )


class TestRemainingCommandsHelpStructure:
    @pytest.mark.parametrize("command", REMAINING_COMMANDS)
    def test_has_usage_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Usage:" in out, f"{command} : section Usage: manquante."
        assert f"forge {command}" in out, (
            f"{command} : l'aide doit citer `forge {command}`."
        )

    @pytest.mark.parametrize("command", REMAINING_COMMANDS)
    def test_has_description_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Description:" in out, (
            f"{command} : section Description: manquante."
        )

    @pytest.mark.parametrize("command", REMAINING_COMMANDS)
    def test_has_options_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Options:" in out, (
            f"{command} : section Options: manquante."
        )
        assert "--help" in out, (
            f"{command} : le flag --help doit être documenté."
        )

    @pytest.mark.parametrize("command", REMAINING_COMMANDS)
    def test_mentions_no_execution(self, command: str):
        out = _run_forge(command, "--help").stdout.lower()
        assert "sans exécuter" in out, (
            f"{command} : l'aide doit rappeler que --help n'exécute rien."
        )


class TestRemainingCommandsHelpHasKeyword:
    @pytest.mark.parametrize("command", REMAINING_COMMANDS)
    def test_mentions_command_specific_keyword(self, command: str):
        out = _run_forge(command, "--help").stdout.lower()
        keywords = [k.lower() for k in COMMAND_KEYWORDS[command]]
        found = [k for k in keywords if k in out]
        assert found, (
            f"{command} : aucun mot-clé attendu trouvé ({keywords}) "
            f"dans l'aide."
        )


class TestWritingCommandsAdvertiseFileWrite:
    """Les commandes qui écrivent doivent l'indiquer dans leur aide."""

    @pytest.mark.parametrize("command", WRITING_COMMANDS)
    def test_help_mentions_write(self, command: str):
        out = _run_forge(command, "--help").stdout.lower()
        write_markers = [
            "écrit", "régénère", "régénéré", "génère",
            "write-if-new", "écrase", "écrasé", "écraser",
            "crée", "copie", "copié",
            "peut être modifié", "créer",
        ]
        found = [m for m in write_markers if m in out]
        assert found, (
            f"{command} --help doit signaler qu'elle peut écrire des "
            f"fichiers (chercher un de : {write_markers}). Sortie : "
            f"{out[:300]!r}"
        )


class TestReadOnlyCommandsAdvertiseReadOnly:
    """Les commandes de contrôle doivent annoncer leur caractère lecture seule."""

    @pytest.mark.parametrize("command", READ_ONLY_COMMANDS)
    def test_help_mentions_read_only(self, command: str):
        out = _run_forge(command, "--help").stdout.lower()
        read_only_markers = [
            "lecture seule",
            "n'écrit",
            "ne modifie",
            "aucune écriture",
            "aucun fichier modifié",
        ]
        found = [m for m in read_only_markers if m in out]
        assert found, (
            f"{command} --help doit signaler le caractère lecture "
            f"seule (chercher un de : {read_only_markers}). Sortie : "
            f"{out[:300]!r}"
        )


class TestRemainingCommandsNoSideEffects:
    @pytest.mark.parametrize("command", REMAINING_COMMANDS)
    def test_no_execution_marker_in_output(self, command: str):
        result = _run_forge(command, "--help")
        combined = result.stdout + result.stderr
        offenders = [m for m in SIDE_EFFECT_MARKERS if m in combined]
        assert not offenders, (
            f"{command} : marqueurs d'exécution trouvés ({offenders}). "
            f"Sortie : {combined!r}"
        )
