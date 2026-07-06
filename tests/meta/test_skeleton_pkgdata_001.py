"""Garde-fou SKELETON-PKGDATA-001 (ADR-024).

Le squelette de projet (skeleton/data/) doit voyager dans le wheel
ET le sdist, sinon un `forge` installé via pip/pipx ne pourrait pas
matérialiser un projet (ticket NEW-MATERIALIZE-001). Les dotfiles (.gitignore,
.gitkeep) doivent être présents ; aucun bytecode (.pyc) ne doit remonter.
"""
from __future__ import annotations

import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
SK = "skeleton/data"


def _clean_build_dirs() -> None:
    import shutil

    if (PROJECT_ROOT / "build").exists():
        shutil.rmtree(PROJECT_ROOT / "build")
    for egg in PROJECT_ROOT.glob("*.egg-info"):
        shutil.rmtree(egg)


@pytest.fixture(scope="module")
def wheel_names(tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("sk_wheel")
    _clean_build_dirs()
    result = subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(out_dir),
         "--no-isolation", str(PROJECT_ROOT)],
        capture_output=True, text=True, timeout=180,
    )
    if result.returncode != 0:
        pytest.fail(f"Build wheel échoué :\n{result.stdout[-500:]}\n{result.stderr[-500:]}")
    wheels = list(out_dir.glob("forge_mvc-*.whl"))
    assert len(wheels) == 1, f"Attendu 1 wheel, trouvé {wheels}"
    with zipfile.ZipFile(wheels[0]) as zf:
        return zf.namelist()


@pytest.fixture(scope="module")
def sdist_names(tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("sk_sdist")
    _clean_build_dirs()
    result = subprocess.run(
        [sys.executable, "-m", "build", "--sdist", "--outdir", str(out_dir),
         "--no-isolation", str(PROJECT_ROOT)],
        capture_output=True, text=True, timeout=180,
    )
    if result.returncode != 0:
        pytest.fail(f"Build sdist échoué :\n{result.stdout[-500:]}\n{result.stderr[-500:]}")
    sdists = list(out_dir.glob("forge_mvc-*.tar.gz"))
    assert len(sdists) == 1, f"Attendu 1 sdist, trouvé {sdists}"
    with tarfile.open(sdists[0]) as tf:
        return tf.getnames()


# ── Fichiers clés présents dans le wheel ─────────────────────────────────────

WHEEL_REQUIRED = [
    f"{SK}/app.py",
    f"{SK}/config.py",
    f"{SK}/requirements.txt",
    f"{SK}/package.json",
    f"{SK}/env/example",
    f"{SK}/mvc/routes.py",
    f"{SK}/mvc/controllers/home_controller.py",
    f"{SK}/mvc/views/home/index.html",
    f"{SK}/mvc/views/errors/404.html",
    f"{SK}/static/tailwind.css",
]


@pytest.mark.parametrize("rel", WHEEL_REQUIRED)
def test_wheel_contient_fichier(wheel_names, rel):
    assert rel in wheel_names, f"{rel} absent du wheel (package-data manquant ?)"


def test_wheel_contient_dotfiles(wheel_names):
    """Les dotfiles du squelette doivent voyager (sinon projet incomplet)."""
    assert f"{SK}/.gitignore" in wheel_names, ".gitignore du squelette absent du wheel."
    gitkeeps = [n for n in wheel_names if n.startswith(SK) and n.endswith(".gitkeep")]
    assert gitkeeps, "Aucun .gitkeep du squelette dans le wheel (dossiers vides perdus)."


def test_wheel_sans_bytecode_squelette(wheel_names):
    offenders = [n for n in wheel_names if n.startswith(SK) and n.endswith((".pyc", ".pyo"))]
    assert not offenders, f"Bytecode dans le wheel : {offenders[:5]}"


# ── Fichiers clés présents dans le sdist ─────────────────────────────────────

def test_sdist_contient_squelette(sdist_names):
    assert any(n.endswith(f"{SK}/app.py") for n in sdist_names), (
        "Le sdist doit contenir le squelette (app.py)."
    )
    assert any(n.endswith(f"{SK}/.gitignore") for n in sdist_names), (
        "Le sdist doit contenir les dotfiles du squelette (.gitignore)."
    )
    assert any(n.endswith(".gitkeep") and f"/{SK}/" in n for n in sdist_names), (
        "Le sdist doit contenir les .gitkeep du squelette."
    )
