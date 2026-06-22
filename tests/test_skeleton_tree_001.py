"""SKELETON-TREE-001 (ADR-024) — squelette de projet dédié et nu.

Le squelette curé vit dans cli/skeleton/data/. Il sert de source à
`forge new` (matérialisation locale, ticket NEW-MATERIALIZE-001). Ces tests
garantissent :

- l'INVENTAIRE attendu (fichiers présents) ;
- l'ABSENCE du contenu démo/opt-in (auth, mfa, media, mail, landing, core/…) ;
- la neutralité de mvc/routes.py (seule la route `/`) ;
- l'anti-dérive de app.py / config.py vis-à-vis de la racine (ADR-024) ;
- que requirements.txt épingle forge-mvc à la version courante ;
- un smoke test : le squelette démarre contre un `core` EXTERNE (pip), sans
  core/ local.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import forge

REPO_ROOT = Path(forge.__file__).resolve().parent
SKELETON = REPO_ROOT / "cli" / "skeleton" / "data"


# ── Inventaire : ce que le squelette DOIT contenir ───────────────────────────

REQUIRED_FILES = [
    "app.py",
    "config.py",
    "requirements.txt",
    "package.json",
    ".gitignore",
    "env/example",
    "static/tailwind.css",
    "static/favicon.ico",
    "static/favicon.svg",
    "static/src/input.css",
    "mvc/routes.py",
    "mvc/controllers/home_controller.py",
    "mvc/views/home/index.html",
    "mvc/forms/__init__.py",
    "mvc/validators/__init__.py",
    "mvc/entities/__init__.py",
    "mvc/helpers/__init__.py",
    "mvc/models/sql/.gitkeep",
    "storage/logs/.gitkeep",
    "storage/mail/.gitkeep",
    "storage/uploads/.gitkeep",
]

REQUIRED_ERROR_PAGES = ["400", "403", "404", "413", "422", "429", "500"]


@pytest.mark.parametrize("rel", REQUIRED_FILES)
def test_fichier_present(rel):
    assert (SKELETON / rel).is_file(), f"Fichier manquant dans le squelette : {rel}"


@pytest.mark.parametrize("code", REQUIRED_ERROR_PAGES)
def test_page_erreur_presente(code):
    assert (SKELETON / "mvc" / "views" / "errors" / f"{code}.html").is_file()


# ── Absence : ce que le squelette ne DOIT PAS contenir ───────────────────────

FORBIDDEN_PATHS = [
    "core",
    "cli",
    "integrations",
    "packages",
    "tests",
    "docs",
    "mkdocs.yml",
    "pyproject.toml",
    "conftest.py",
    "mvc/controllers/auth_controller.py",
    "mvc/controllers/mfa_challenge_controller.py",
    "mvc/controllers/welcome_controller.py",
    "mvc/models/auth_model.py",
    "mvc/views/auth",
    "mvc/views/landing",
    "mvc/entities/media",
    "mvc/mail",
]


@pytest.mark.parametrize("rel", FORBIDDEN_PATHS)
def test_chemin_absent(rel):
    assert not (SKELETON / rel).exists(), (
        f"{rel} ne doit pas être livré dans un projet nu (ADR-024)."
    )


# ── Neutralité du contenu ────────────────────────────────────────────────────

def test_routes_neutres():
    content = (SKELETON / "mvc" / "routes.py").read_text(encoding="utf-8")
    assert 'public.add("GET", "/", HomeController.index' in content
    # Aucune autre route pré-câblée.
    assert content.count("public.add(") == 1, "Le squelette ne câble que la route /."


def test_home_controller_rend_home_neutre():
    content = (SKELETON / "mvc" / "controllers" / "home_controller.py").read_text(
        encoding="utf-8"
    )
    assert 'render("home/index.html"' in content
    assert "landing" not in content


def test_home_view_sans_contenu_perime():
    content = (SKELETON / "mvc" / "views" / "home" / "index.html").read_text(
        encoding="utf-8"
    )
    # Pas de commandes périmées ni de lien d'auth dans une home neutre.
    for forbidden in ["cmd/make.py", "schema:create", "security:init", "/login"]:
        assert forbidden not in content, (
            f"{forbidden!r} ne doit pas apparaître dans la home neutre."
        )


# ── Dépendance core via pip + anti-dérive ────────────────────────────────────

def test_requirements_epingle_forge_mvc():
    content = (SKELETON / "requirements.txt").read_text(encoding="utf-8")
    assert f"forge-mvc=={forge._FORGE_VERSION}" in content, (
        "requirements.txt doit épingler forge-mvc à la version courante "
        f"({forge._FORGE_VERSION})."
    )


@pytest.mark.parametrize("name", ["app.py", "config.py"])
def test_anti_derive_avec_racine(name):
    """app.py / config.py du squelette restent identiques à la racine (ADR-024)."""
    racine = (REPO_ROOT / name).read_text(encoding="utf-8")
    squelette = (SKELETON / name).read_text(encoding="utf-8")
    assert racine == squelette, (
        f"{name} du squelette a dérivé de la version racine — resynchroniser."
    )


# ── Smoke test : démarrage contre un core EXTERNE (sans core/ local) ──────────

def test_squelette_demarre_contre_core_externe(tmp_path):
    """Copie le squelette dans un projet temporaire SANS core/ local et vérifie
    que app.py se charge et rend la home en important `core` depuis REPO_ROOT
    via PYTHONPATH (simule le paquet forge-mvc installé)."""
    proj = tmp_path / "proj"
    shutil.copytree(SKELETON, proj)
    assert not (proj / "core").exists()

    code = (
        "import app\n"
        "from core.http.helpers import html\n"
        "r = html('home/index.html', 200)\n"
        "assert b'Forge' in r.body, 'home non rendue'\n"
        "print('SMOKE_OK')\n"
    )
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT), "APP_ENV": "dev"}
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=proj,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Le squelette ne démarre pas contre un core externe :\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert "SMOKE_OK" in result.stdout
