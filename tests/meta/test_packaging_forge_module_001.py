"""Garde-fou PACKAGING-FORGE-MODULE-001.

Vérifie que le packaging CLI de Forge est cohérent :
- forge.py existe à la racine avec cli_entrypoint()
- pyproject.toml déclare l'entry point [project.scripts]
- python forge.py --version fonctionne
- python -m forge --version fonctionne (module invocation)

Décision G6 (option C) : forge.py reste le module unique — créer forge/
comme package nécessiterait de supprimer forge.py et de migrer 236 imports
de forge_cli dans les tests. Les deux modes d'invocation sont déjà
opérationnels via py-modules = ["forge"] et if __name__ == "__main__".
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import tomllib

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FORGE_SCRIPT = PROJECT_ROOT / "forge.py"
PYPROJECT = PROJECT_ROOT / "pyproject.toml"


class TestForgeScriptStructure:
    """forge.py à la racine a la structure attendue pour le packaging."""

    def test_forge_script_exists(self):
        assert FORGE_SCRIPT.exists(), (
            "forge.py doit exister à la racine — point d'entrée CLI officiel."
        )

    def test_cli_entrypoint_defined(self):
        text = FORGE_SCRIPT.read_text(encoding="utf-8")
        assert "def cli_entrypoint" in text, (
            "forge.py doit définir cli_entrypoint() — "
            "cible de [project.scripts] dans pyproject.toml."
        )

    def test_main_guard_present(self):
        text = FORGE_SCRIPT.read_text(encoding="utf-8")
        assert 'if __name__ == "__main__"' in text, (
            "forge.py doit avoir un bloc if __name__ == '__main__': "
            "pour que python -m forge fonctionne."
        )

    def test_forge_version_defined(self):
        text = FORGE_SCRIPT.read_text(encoding="utf-8")
        assert "_FORGE_VERSION" in text, (
            "forge.py doit déclarer _FORGE_VERSION — version du framework."
        )


class TestPyprojectEntryPoint:
    """pyproject.toml déclare les métadonnées de packaging correctement."""

    def test_entry_point_declared(self):
        data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
        scripts = data.get("project", {}).get("scripts", {})
        assert "forge" in scripts, (
            "pyproject.toml [project.scripts] doit déclarer l'entry point `forge`."
        )

    def test_entry_point_targets_cli_entrypoint(self):
        data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
        scripts = data.get("project", {}).get("scripts", {})
        target = scripts.get("forge", "")
        assert "cli_entrypoint" in target, (
            f"[project.scripts].forge doit cibler cli_entrypoint, got: {target!r}"
        )

    def test_py_modules_or_packages_includes_forge(self):
        data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
        setuptools = data.get("tool", {}).get("setuptools", {})
        py_modules = setuptools.get("py-modules", [])
        packages = setuptools.get("packages", {})
        included = (
            "forge" in py_modules
            or "forge" in packages
            or (isinstance(packages, dict) and "find" in packages)
        )
        assert included, (
            "pyproject.toml doit inclure le module/package 'forge' "
            "via py-modules ou packages."
        )


class TestCLIInvocations:
    """Les deux modes d'invocation CLI fonctionnent."""

    def _env(self) -> dict:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT)
        return env

    def test_python_forge_py_version(self):
        """`python forge.py --version` retourne la version Forge."""
        result = subprocess.run(
            [sys.executable, str(FORGE_SCRIPT), "--version"],
            capture_output=True, text=True, timeout=15, env=self._env(),
        )
        assert result.returncode == 0, (
            f"python forge.py --version a échoué (rc={result.returncode}):\n{result.stderr}"
        )
        assert "Forge" in result.stdout, (
            f"Sortie attendue : 'Forge ...' — obtenu : {result.stdout!r}"
        )

    def test_python_m_forge_version(self):
        """`python -m forge --version` retourne la version Forge."""
        result = subprocess.run(
            [sys.executable, "-m", "forge", "--version"],
            capture_output=True, text=True, timeout=15, env=self._env(),
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0, (
            f"python -m forge --version a échoué (rc={result.returncode}):\n{result.stderr}"
        )
        assert "Forge" in result.stdout, (
            f"Sortie attendue : 'Forge ...' — obtenu : {result.stdout!r}"
        )

    def test_both_invocations_return_same_version(self):
        """forge.py et python -m forge retournent la même version."""
        r1 = subprocess.run(
            [sys.executable, str(FORGE_SCRIPT), "--version"],
            capture_output=True, text=True, timeout=15, env=self._env(),
        )
        r2 = subprocess.run(
            [sys.executable, "-m", "forge", "--version"],
            capture_output=True, text=True, timeout=15, env=self._env(),
            cwd=str(PROJECT_ROOT),
        )
        assert r1.stdout.strip() == r2.stdout.strip(), (
            f"Versions incohérentes :\n  forge.py: {r1.stdout.strip()!r}\n"
            f"  -m forge: {r2.stdout.strip()!r}"
        )
