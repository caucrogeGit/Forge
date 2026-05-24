"""Garde-fou DEV-SERVER-SCRIPT-001.

Vérifie que `scripts/dev-server.sh` :

1. existe et est exécutable ;
2. utilise un shebang bash et `set -euo pipefail` ;
3. ne contient pas de commande de terminaison de processus automatique
   (kill / pkill / killall), même conditionnelle ;
4. lance bien `python app.py` ;
5. référence les trois variables d'environnement attendues
   (APP_HOST, APP_PORT, APP_SSL_ENABLED).

Les tests sont volontairement statiques : ils n'exécutent pas le script
et ne dépendent pas de l'état réel du port 8000.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "dev-server.sh"


@pytest.fixture(scope="module")
def script_text() -> str:
    return SCRIPT_PATH.read_text(encoding="utf-8")


class TestScriptPresence:
    def test_script_exists(self):
        assert SCRIPT_PATH.is_file(), (
            f"{SCRIPT_PATH.relative_to(PROJECT_ROOT)} doit exister."
        )

    def test_script_is_executable(self):
        assert os.access(SCRIPT_PATH, os.X_OK), (
            f"{SCRIPT_PATH.relative_to(PROJECT_ROOT)} doit être exécutable "
            f"(chmod +x)."
        )


class TestScriptShape:
    def test_shebang_is_bash(self, script_text: str):
        first_line = script_text.splitlines()[0]
        assert first_line.startswith("#!"), "Le script doit avoir un shebang."
        assert "bash" in first_line, (
            f"Shebang doit cibler bash. Trouvé : {first_line!r}"
        )

    def test_strict_mode(self, script_text: str):
        assert "set -euo pipefail" in script_text, (
            "Le script doit activer `set -euo pipefail`."
        )

    def test_bash_syntax_valid(self):
        result = subprocess.run(
            ["bash", "-n", str(SCRIPT_PATH)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, (
            f"bash -n a échoué :\n{result.stderr}"
        )


class TestNoProcessKilling:
    """Aucune commande automatique de terminaison ne doit apparaître."""

    @pytest.mark.parametrize("forbidden", ["kill", "killall", "pkill"])
    def test_no_kill_command(self, script_text: str, forbidden: str):
        pattern = re.compile(rf"\b{re.escape(forbidden)}\b")
        offenders = [
            (i + 1, line)
            for i, line in enumerate(script_text.splitlines())
            if pattern.search(line)
        ]
        assert not offenders, (
            f"Le script ne doit pas contenir `{forbidden}` (lignes : "
            f"{[n for n, _ in offenders]}). Voir la règle anti-dérive "
            f"du ticket DEV-SERVER-SCRIPT-001."
        )


class TestLaunchesApp:
    def test_invokes_python_app(self, script_text: str):
        assert "python app.py" in script_text, (
            "Le script doit lancer `python app.py` (ou `exec python app.py`)."
        )


class TestConfigVariablesReferenced:
    @pytest.mark.parametrize(
        "var", ["APP_HOST", "APP_PORT", "APP_SSL_ENABLED"]
    )
    def test_variable_referenced(self, script_text: str, var: str):
        assert var in script_text, (
            f"Le script doit référencer la variable {var} (lecture depuis "
            f"env/dev ou affichage du diagnostic)."
        )


