"""Garde-fou PACKAGING-WHEEL-CONTENT-001.

Vérifie qu'une wheel buildée depuis le pyproject.toml racine contient
le code source nécessaire pour que pip install fonctionne réellement.

Origine : découverte pendant T2 que les wheels buildées depuis
packages/forge-mvc/ (forge_mvc-2.4.0, 3.0.0, 3.0.1) étaient toutes
vides — dist-info seul, 0 ligne de code Python. Forge n'était pas
installable depuis PyPI.

T2b a corrigé en consolidant le packaging sur le pyproject.toml racine
(where=["."]). Ce garde-fou empêche la régression.
"""
from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent

REQUIRED_PACKAGES = ["core", "forge_cli", "integrations"]


@pytest.fixture(scope="module")
def fresh_wheel(tmp_path_factory):
    """Build une wheel fraîche depuis le pyproject.toml racine."""
    out_dir = tmp_path_factory.mktemp("wheel_build")
    result = subprocess.run(
        [
            sys.executable, "-m", "build", "--wheel",
            "--outdir", str(out_dir),
            "--no-isolation",
            str(PROJECT_ROOT),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        pytest.fail(
            f"Build wheel a échoué (pyproject.toml racine) :\n"
            f"stdout : {result.stdout[-500:]}\n"
            f"stderr : {result.stderr[-500:]}"
        )
    wheels = list(out_dir.glob("forge_mvc-*.whl"))
    assert len(wheels) == 1, f"Attendu 1 wheel, trouvé {len(wheels)} : {wheels}"
    return wheels[0]


# ---------------------------------------------------------------------------
# Classe 1 — La wheel n'est pas vide
# ---------------------------------------------------------------------------

class TestWheelHasCode:

    def test_wheel_size_substantial(self, fresh_wheel):
        """La wheel fait au moins 200 KB (pas juste des dist-info)."""
        size = fresh_wheel.stat().st_size
        assert size > 200_000, (
            f"La wheel ne fait que {size} bytes. "
            f"Soupçon : wheel vide (dist-info seul). "
            f"Vérifier [tool.setuptools.packages.find] dans pyproject.toml."
        )

    @pytest.mark.parametrize("pkg", REQUIRED_PACKAGES)
    def test_wheel_contains_package(self, fresh_wheel, pkg):
        """La wheel contient au moins un fichier .py dans le package."""
        with zipfile.ZipFile(fresh_wheel) as zf:
            names = zf.namelist()
        has_files = any(
            name.startswith(f"{pkg}/") and name.endswith(".py")
            for name in names
        )
        assert has_files, (
            f"La wheel ne contient aucun fichier .py de '{pkg}/'. "
            f"Vérifier include = ['{pkg}*'] dans [tool.setuptools.packages.find]."
        )

    def test_wheel_contains_forge_py(self, fresh_wheel):
        """La wheel contient forge.py (module entry point)."""
        with zipfile.ZipFile(fresh_wheel) as zf:
            names = zf.namelist()
        assert "forge.py" in names, (
            "La wheel ne contient pas forge.py. "
            "Vérifier py-modules = ['forge'] dans [tool.setuptools]."
        )


# ---------------------------------------------------------------------------
# Classe 2 — Entry point CLI déclaré
# ---------------------------------------------------------------------------

class TestWheelEntryPoint:

    def test_entry_point_forge_declared(self, fresh_wheel):
        """forge_mvc-X.dist-info/entry_points.txt déclare forge = forge:cli_entrypoint."""
        with zipfile.ZipFile(fresh_wheel) as zf:
            ep_files = [n for n in zf.namelist() if n.endswith("entry_points.txt")]
            assert ep_files, "Pas de entry_points.txt dans la wheel"
            content = zf.read(ep_files[0]).decode("utf-8")
        assert "forge" in content and "cli_entrypoint" in content, (
            f"entry_points.txt ne déclare pas forge = forge:cli_entrypoint :\n{content}"
        )
