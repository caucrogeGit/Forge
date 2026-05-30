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


def _clean_build_dirs() -> None:
    """Supprime build/ et *.egg-info pour un build représentatif.

    PKG-WHEEL-NO-PYC-001 : ``python -m build --no-isolation`` réutilise
    ``./build/lib`` sans en purger les fichiers obsolètes. Un build
    enchaîné après un ``compileall`` y laisse des ``__pycache__/*.pyc``
    qui remontent ensuite dans la wheel. On reproduit ici le nettoyage
    fait par ``scripts/release_check.sh --full`` pour tester l'artefact
    réellement publiable.
    """
    import shutil

    if (PROJECT_ROOT / "build").exists():
        shutil.rmtree(PROJECT_ROOT / "build")
    for egg in PROJECT_ROOT.glob("*.egg-info"):
        shutil.rmtree(egg)


@pytest.fixture(scope="module")
def fresh_wheel(tmp_path_factory):
    """Build une wheel fraîche depuis le pyproject.toml racine."""
    out_dir = tmp_path_factory.mktemp("wheel_build")
    _clean_build_dirs()
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


@pytest.fixture(scope="module")
def fresh_sdist(tmp_path_factory):
    """Build un sdist frais depuis le pyproject.toml racine."""
    import tarfile

    out_dir = tmp_path_factory.mktemp("sdist_build")
    _clean_build_dirs()
    result = subprocess.run(
        [
            sys.executable, "-m", "build", "--sdist",
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
            f"Build sdist a échoué :\n"
            f"stdout : {result.stdout[-500:]}\n"
            f"stderr : {result.stderr[-500:]}"
        )
    sdists = list(out_dir.glob("forge_mvc-*.tar.gz"))
    assert len(sdists) == 1, f"Attendu 1 sdist, trouvé {len(sdists)} : {sdists}"
    with tarfile.open(sdists[0]) as tf:
        return tf.getnames()


class TestSdistContent:
    """Garde-fou PKG-SDIST-TESTS-DECISION-001.

    Le sdist distribué embarque le code installable mais PAS la suite de
    tests Forge (outil de dev, exécuté depuis le monorepo). Décision
    documentée dans MANIFEST.in (``prune tests``).
    """

    def test_sdist_excludes_tests(self, fresh_sdist):
        offenders = [
            n for n in fresh_sdist
            if "/tests/" in n or n.split("/")[1:2] == ["tests"]
        ]
        assert not offenders, (
            f"Le sdist embarque {len(offenders)} fichier(s) de tests "
            f"(décision PKG-SDIST-TESTS-DECISION-001 : prune tests). "
            f"Exemples : {offenders[:5]}"
        )

    def test_sdist_contains_core_and_entrypoint(self, fresh_sdist):
        assert any("/core/" in n for n in fresh_sdist), (
            "Le sdist doit contenir le package core/."
        )
        assert any(n.endswith("/forge.py") for n in fresh_sdist), (
            "Le sdist doit contenir forge.py (module entry point)."
        )


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

class TestWheelIsClean:
    """Garde-fou PKG-WHEEL-NO-PYC-001 — pas de bytecode dans la wheel.

    Une wheel propre ne doit embarquer que des sources : aucun
    ``.pyc``/``.pyo`` ni dossier ``__pycache__``. Sinon l'artefact
    dépend du poste de build et n'est pas reproductible.
    """

    def test_wheel_has_no_bytecode(self, fresh_wheel):
        with zipfile.ZipFile(fresh_wheel) as zf:
            names = zf.namelist()
        bytecode = [
            n for n in names
            if n.endswith((".pyc", ".pyo")) or "__pycache__/" in n
        ]
        assert not bytecode, (
            "La wheel contient du bytecode compilé "
            f"({len(bytecode)} fichiers) — build non propre. "
            f"Exemples : {bytecode[:5]}. "
            "Nettoyer build/ avant python -m build (cf. release_check.sh --full)."
        )


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
