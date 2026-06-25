"""Garde-fou TYPING-CLI-STRICT-001 : cli/ passe pyright sans erreur.

L'outillage `cli/` est hors du périmètre pyright déclaré dans `pyproject.toml`
(qui cible le runtime livré : cœur + opt-ins), et ce pyproject est protégé. Ce
test gate néanmoins `cli/` en CI : `pyright cli` doit rester à **0 erreur**.

Les warnings sont tolérés (ex. `reportMissingModuleSource` pour `gunicorn`, dont
le stub peut manquer selon l'environnement). Le passage en mode strict complet de
`cli/` (en-têtes `# pyright: strict` par fichier) reste un chantier ultérieur.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parent.parent.parent


def test_cli_pyright_sans_erreur():
    pyright = shutil.which("pyright")
    if pyright is None:
        pytest.skip("pyright non disponible dans cet environnement")
    result = subprocess.run(
        [pyright, "cli"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "pyright signale des erreurs dans cli/ :\n" + result.stdout + result.stderr
    )
