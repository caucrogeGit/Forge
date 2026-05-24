"""Garde-fou CLI-HELP-FLAGS-DISPATCHER-001.

Vérifie que l'interception centrale de `--help`/`-h` dans `forge.py` :

1. répond avec exit 0 pour les 6 commandes à effets de bord critiques
   identifiées par l'audit (db:init, mail:init, i18n:init, upload:init,
   media:init, deploy:init) ;
2. n'exécute pas leur logique métier (aucun marqueur d'init/connexion
   dans la sortie) ;
3. honore aussi la forme courte `-h` ;
4. ne casse pas l'aide globale `forge --help` ;
5. ne casse pas les commandes qui ont déjà un `--help` natif
   (make:entity, auth:user:create) ;
6. laisse passer une commande inconnue avec son message d'erreur habituel.

Les tests invoquent `python forge.py` (et pas `forge`) pour ne dépendre
d'aucun entrypoint installé.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
FORGE_PY = PROJECT_ROOT / "forge.py"


# Les 6 commandes que l'audit a identifiées comme déclenchant des effets de
# bord (création de dossiers, tentative de connexion MariaDB, etc.) si --help
# n'est pas intercepté.
CRITICAL_COMMANDS = [
    "db:init",
    "mail:init",
    "i18n:init",
    "upload:init",
    "media:init",
    "deploy:init",
]


# Marqueurs qui apparaîtraient uniquement si la commande métier s'exécutait
# vraiment (par opposition à l'aide centralisée).
SIDE_EFFECT_MARKERS = [
    "[OK]",          # init de dossiers (upload/media/mail/i18n)
    "[ERREUR]",      # tentative de connexion DB échouée (db:init)
    "Provisioning",  # provisionnement DB (db:init)
    "[PRÉSERVÉ]",    # i18n:init / mail:init préservent des fichiers
    "Dossier prêt",
]


def _run_forge(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(FORGE_PY), *args],
        capture_output=True, text=True, timeout=15,
    )


class TestCriticalCommandsExitZero:
    """Les 6 commandes critiques retournent 0 avec --help / -h."""

    @pytest.mark.parametrize("command", CRITICAL_COMMANDS)
    def test_long_form_exits_zero(self, command: str):
        result = _run_forge(command, "--help")
        assert result.returncode == 0, (
            f"forge {command} --help doit retourner 0. "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )

    @pytest.mark.parametrize("command", ["db:init", "mail:init"])
    def test_short_form_exits_zero(self, command: str):
        result = _run_forge(command, "-h")
        assert result.returncode == 0, (
            f"forge {command} -h doit retourner 0. "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )


class TestCriticalCommandsShowHelp:
    """Les 6 commandes critiques affichent un texte d'aide cohérent."""

    @pytest.mark.parametrize("command", CRITICAL_COMMANDS)
    def test_help_text_mentions_usage_and_help_flag(self, command: str):
        result = _run_forge(command, "--help")
        output = result.stdout
        assert "Usage:" in output, (
            f"forge {command} --help doit afficher une ligne 'Usage:'. "
            f"Sortie : {output!r}"
        )
        assert f"forge {command}" in output, (
            f"forge {command} --help doit citer la commande. "
            f"Sortie : {output!r}"
        )
        assert "--help" in output, (
            f"forge {command} --help doit documenter le flag --help."
        )


class TestCriticalCommandsNoSideEffects:
    """L'interception ne doit déclencher aucun effet de bord métier."""

    @pytest.mark.parametrize("command", CRITICAL_COMMANDS)
    def test_no_side_effect_marker_in_output(self, command: str):
        result = _run_forge(command, "--help")
        combined = result.stdout + result.stderr
        offenders = [m for m in SIDE_EFFECT_MARKERS if m in combined]
        assert not offenders, (
            f"forge {command} --help a déclenché un effet de bord "
            f"(marqueurs trouvés : {offenders}). Sortie : {combined!r}"
        )


class TestGlobalHelpStillWorks:
    """Le `--help` global n'est pas affecté par l'interception centrale."""

    def test_global_help_exits_zero(self):
        result = _run_forge("--help")
        assert result.returncode == 0
        assert "Forge" in result.stdout
        assert "commande" in result.stdout.lower()

    def test_no_args_shows_global_help(self):
        result = _run_forge()
        assert result.returncode == 0
        assert "Forge" in result.stdout


class TestNativeHelpPreserved:
    """Les commandes avec --help natif gardent leur aide détaillée."""

    def test_make_entity_keeps_native_help(self):
        """make:entity a un `__doc__` détaillé, pas l'aide générique."""
        result = _run_forge("make:entity", "--help")
        assert result.returncode == 0
        # Marqueur de l'aide native (présent dans __doc__ de make_entity.py)
        # mais ABSENT du template générique (qui contient 'Description:')
        assert "Description:" not in result.stdout, (
            "L'interception centrale a écrasé l'aide native de make:entity. "
            f"Sortie : {result.stdout!r}"
        )

    def test_auth_user_create_keeps_argparse_help(self):
        """auth:user:create utilise argparse — doit afficher 'usage: forge ...'."""
        result = _run_forge("auth:user:create", "--help")
        assert result.returncode == 0
        # Argparse imprime 'usage:' en minuscules, l'interception 'Usage:' en
        # majuscule. La présence du minuscule prouve que argparse a tourné.
        assert "usage: forge auth:user:create" in result.stdout, (
            "L'interception centrale a écrasé l'aide argparse de "
            f"auth:user:create. Sortie : {result.stdout!r}"
        )


class TestUnknownCommandUnchanged:
    """Une commande inconnue conserve son message d'erreur habituel."""

    def test_unknown_command_still_errors(self):
        result = _run_forge("nope:nope", "--help")
        # Pas d'entrée dans HELP_DESCRIPTIONS → l'interception ne s'applique
        # pas, le dispatcher tombe sur cli_fail("commande inconnue").
        assert result.returncode != 0
        assert "commande inconnue" in (result.stdout + result.stderr).lower()
