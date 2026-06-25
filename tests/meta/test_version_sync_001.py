"""Garde-fou PKG-VERSION-SYNC-CHECK-001 : version cohérente sur tout le dépôt.

Exécute `tools/check_version_sync.py` dans la suite de tests, pour attraper une
désynchronisation de version dès le push (et pas seulement au moment de la
release). Le checker dérive la version canonique du pyproject racine et vérifie
les sous-paquets, les pins `forge-mvc`, les extras, le squelette, `core/__init__`,
`forge.py` et `package.json` (forme SemVer).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parent.parent.parent
CHECKER = ROOT / "tools" / "check_version_sync.py"


def test_checker_present():
    assert CHECKER.is_file(), "tools/check_version_sync.py est attendu (PKG-VERSION-SYNC-CHECK-001)"


def test_versions_synchronisees():
    result = subprocess.run(
        [sys.executable, str(CHECKER)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, (
        "Désynchronisation de version détectée :\n" + result.stdout + result.stderr
    )
