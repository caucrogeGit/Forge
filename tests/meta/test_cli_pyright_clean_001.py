"""Garde-fou TYPING-CLI-STRICT-001 / TYPING-STRICT-GATE-FINAL-001 : l'outillage
passe pyright sans erreur.

L'outillage (`cli/`, `forge.py`, `integrations/`, `tools/`, `skeleton/__init__.py`)
est hors du périmètre pyright déclaré dans `pyproject.toml` (qui cible le runtime
livré : cœur + opt-ins), et ce pyproject est protégé. Ce test gate néanmoins
l'ensemble en CI : `pyright cli forge.py integrations tools skeleton/__init__.py`
doit rester à **0 erreur**. Le module `skeleton` (paquet racine, ADR-065) porte
le matérialisateur ; son sous-arbre `skeleton/data/**` reste hors périmètre.

Chaque fichier porte `# pyright: strict` (chantier de typage strict complet
terminé), sauf `skeleton/data/**` (templates de code généré utilisateur,
typés comme du code applicatif et non comme du code de Forge).

Les warnings sont tolérés (ex. `reportMissingModuleSource` pour `gunicorn`, dont
le stub peut manquer selon l'environnement).
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
        [pyright, "cli", "forge.py", "integrations", "tools", "skeleton/__init__.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "pyright signale des erreurs dans l'outillage (cli/forge.py/integrations/tools) :\n"
        + result.stdout
        + result.stderr
    )
