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
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "requirements-docs.txt",
    "pytest.ini",
    "mkdocs.yml",
    "tests/conftest.py",
    "tests/test_smoke_001.py",
    "docs/index.md",
    "package.json",
    ".gitignore",
    "env/example",
    "static/tailwind.css",
    "static/favicon.ico",
    "static/favicon.png",
    "static/forge-nav.png",
    "static/src/input.css",
    "mvc/routes.py",
    "mvc/controllers/home_controller.py",
    "mvc/views/layouts/base.html",
    "mvc/views/components/ui.html",
    "mvc/views/components/forms.html",
    "mvc/views/components/data.html",
    "mvc/views/components/interactive.html",
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
    "conftest.py",
    "mvc/controllers/auth_controller.py",
    "mvc/controllers/mfa_challenge_controller.py",
    "mvc/controllers/welcome_controller.py",
    "mvc/models/auth_model.py",
    "mvc/views/auth",
    "mvc/views/landing",
    "mvc/entities/media",
    "mvc/mail",
    # docs/ est livré (chaîne MkDocs, ADR-063), mais le parcours welcome-projet
    # (ex-ADR-048) faisait double emploi avec la documentation officielle.
    "docs/welcome",
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


def test_home_view_sans_cartes_optin():
    """La home nue ne présente plus de cartes d'opt-in (principe 8).

    Les opt-ins se découvrent via la documentation, pas via une vitrine
    dans la page d'accueil du projet généré.
    """
    content = (SKELETON / "mvc" / "views" / "home" / "index.html").read_text(
        encoding="utf-8"
    )
    assert "forgemvc.com/docs/forge/" not in content, (
        "la home nue ne doit plus lister de cartes d'opt-in."
    )
    assert "Pour aller plus loin" not in content


def test_layout_base_affiche_version_courante():
    """Le layout partagé affiche la version de Forge sur laquelle le squelette
    est généré (pied de page commun à toutes les vues).

    La version est figée en littéral (même convention que requirements.txt)
    et tenue synchrone avec forge._FORGE_VERSION par ce garde-fou.
    """
    content = (SKELETON / "mvc" / "views" / "layouts" / "base.html").read_text(
        encoding="utf-8"
    )
    assert f"Forge {forge._FORGE_VERSION}" in content, (
        "layouts/base.html doit afficher la version courante "
        f"({forge._FORGE_VERSION})."
    )


def test_home_view_etend_le_layout():
    """La home étend le layout partagé (démontre le pattern, pas de duplication)."""
    content = (SKELETON / "mvc" / "views" / "home" / "index.html").read_text(
        encoding="utf-8"
    )
    assert '{% extends "layouts/base.html" %}' in content


def test_input_css_porte_la_charte_et_pas_la_landing():
    """input.css définit la charte (@theme) et n'embarque plus le CSS de la landing."""
    content = (SKELETON / "static" / "src" / "input.css").read_text(encoding="utf-8")
    assert "@theme" in content, "input.css doit définir la charte via @theme"
    # Primaire = orange Forge (signature de la marque, forge-tokens.css --forge-accent).
    assert "--color-forge" in content, "la charte doit définir ses tokens couleur (primaire orange Forge)"
    # Plus aucune trace du CSS de la landing ni de @source vers des fichiers
    # supprimés (landing/, docs/index.html).
    assert "landing-" not in content
    assert ".sec-dark" not in content
    assert "views/landing" not in content


def test_package_json_fournit_watch_css():
    content = (SKELETON / "package.json").read_text(encoding="utf-8")
    assert "watch:css" in content, (
        "package.json doit fournir un script watch:css (rebuild Tailwind continu)."
    )


def test_bibliotheque_de_composants_expose_les_macros():
    comp = SKELETON / "mvc" / "views" / "components"
    ui = (comp / "ui.html").read_text(encoding="utf-8")
    forms = (comp / "forms.html").read_text(encoding="utf-8")
    data = (comp / "data.html").read_text(encoding="utf-8")
    interactive = (comp / "interactive.html").read_text(encoding="utf-8")
    for macro in ("macro button", "macro card", "macro badge", "macro alert",
                  "macro flash_messages", "macro page_header", "macro empty_state",
                  "macro stat", "macro breadcrumb", "macro navbar"):
        assert macro in ui, f"components/ui.html doit définir {macro!r}"
    for macro in ("macro field", "macro select_field", "macro radio_group",
                  "macro file_field", "macro fieldset", "macro form_errors",
                  "macro checkbox", "macro submit"):
        assert macro in forms, f"components/forms.html doit définir {macro!r}"
    for macro in ("macro table", "macro pagination"):
        assert macro in data, f"components/data.html doit définir {macro!r}"
    for macro in ("macro accordion", "macro dropdown", "macro modal", "macro modal_trigger"):
        assert macro in interactive, f"components/interactive.html doit définir {macro!r}"


# ── Dépendance core via pip + anti-dérive ────────────────────────────────────

def test_requirements_epingle_forge_mvc():
    content = (SKELETON / "requirements.txt").read_text(encoding="utf-8")
    assert f"forge-mvc=={forge._FORGE_VERSION}" in content, (
        "requirements.txt doit épingler forge-mvc à la version courante "
        f"({forge._FORGE_VERSION})."
    )


def test_requirements_ne_pin_aucun_backend_bdd():
    # ADR-060 : révise la trajectoire d'ADR-054. Le squelette est livré SANS
    # backend BDD ; l'utilisateur choisit et installe le sien. Aucune ligne de
    # dépendance ne doit épingler un backend (ils restent en commentaire).
    content = (SKELETON / "requirements.txt").read_text(encoding="utf-8")
    lignes_dep = [
        ligne.strip()
        for ligne in content.splitlines()
        if ligne.strip() and not ligne.lstrip().startswith("#")
    ]
    for backend in ("forge-mvc-mariadb", "forge-mvc-sqlite", "forge-mvc-postgres", "forge-mvc-mssql"):
        assert not any(ligne.startswith(backend) for ligne in lignes_dep), (
            f"Le squelette ne doit pas épingler {backend} (ADR-060) : "
            "le backend est un choix de l'utilisateur, mentionné en commentaire."
        )


def test_env_example_sans_config_bdd():
    # ADR-060 : le gabarit env/example ne porte plus de bloc de connexion BDD.
    # Ces variables appartiennent au backend installé, pas au squelette.
    content = (SKELETON / "env" / "example").read_text(encoding="utf-8")
    lignes = [
        ligne.strip()
        for ligne in content.splitlines()
        if ligne.strip() and not ligne.lstrip().startswith("#")
    ]
    for prefixe in ("DB_ADMIN_", "DB_APP_", "DB_NAME", "DB_CHARSET", "DB_COLLATION", "DB_POOL_SIZE"):
        assert not any(ligne.startswith(prefixe) for ligne in lignes), (
            f"env/example ne doit plus déclarer {prefixe} (ADR-060)."
        )


# ADR-044 : l'application racine de dogfooding a été retirée (relocalisée en
# fixture de test). L'anti-dérive app.py/config.py « racine vs squelette »
# d'ADR-024 n'a plus d'objet : le squelette est l'unique source.


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
