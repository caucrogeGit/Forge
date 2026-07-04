"""SKELETON-GUARD-001 (ADR-024) — neutralité du squelette DISTRIBUÉ.

Équivalent de test_skeleton_routes_neutral_001 (qui garde le mvc/routes.py du
dépôt) appliqué au squelette embarqué `cli/skeleton/data/`, et étendu :
aucun fichier du squelette n'importe ni ne pré-câble un opt-in.

Charte : principe 8 (noyau minimal, briques opt-in), principe 1 (séparer
framework et application métier), principe 3 (refuser la magie cachée).
"""
from __future__ import annotations

import ast

import pytest

from cli.skeleton import DATA_DIR, iter_skeleton_files

ROUTES = DATA_DIR / "mvc" / "routes.py"
HOME_CONTROLLER = DATA_DIR / "mvc" / "controllers" / "home_controller.py"

# Chemins de routes qui ne doivent jamais être pré-câblés dans routes.py.
ROUTE_FORBIDDEN_PATHS = ['"/login"', '"/logout"', '"/login/mfa"', '"/welcome"']

# Marqueurs de CODE opt-in / app métier interdits dans toute la couche mvc/.
# (Les chemins d'URL en dur dans des gabarits d'erreur ne comptent pas : ce ne
# sont pas du câblage de route. On vise imports d'opt-ins et contrôleurs métier.)
OPTIN_CODE_TOKENS = [
    "AuthController",
    "WelcomeController",
    "MfaChallengeController",
    "register_mfa_routes",
    "register_rbac_routes",
    "register_iot_routes",
    # register_optins n'est PAS interdit (ADR-061) : c'est le hook générique du
    # registre d'opt-ins, toujours présent et vide par défaut, pas du code
    # d'opt-in spécifique.
    "forge_mvc_",  # tout import d'un paquet opt-in
    "forge-starter:",
]


@pytest.fixture(scope="module")
def routes_source() -> str:
    return ROUTES.read_text(encoding="utf-8")


def test_routes_home_sur_racine(routes_source):
    assert "HomeController" in routes_source
    assert '"GET", "/"' in routes_source


def test_routes_imports_minimaux(routes_source):
    """Router, HomeController et le registre d'opt-ins (ADR-061) au niveau module."""
    tree = ast.parse(routes_source)
    modules = [
        node.module or ""
        for node in ast.iter_child_nodes(tree)
        if isinstance(node, ast.ImportFrom)
    ]
    assert modules == [
        "core.http.router",
        "mvc.controllers.home_controller",
        "optins.registry",
    ], f"Imports inattendus dans le routes.py du squelette : {modules}"


def test_home_controller_neutre():
    src = HOME_CONTROLLER.read_text(encoding="utf-8")
    assert 'render("home/index.html"' in src
    assert "landing" not in src
    # N'importe que du core.
    tree = ast.parse(src)
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").startswith("core."), (
                f"home_controller ne doit importer que core.* : {node.module}"
            )


@pytest.mark.parametrize("path", ROUTE_FORBIDDEN_PATHS)
def test_aucune_route_auth_ou_welcome_precablee(routes_source, path):
    """routes.py ne pré-câble aucune route d'auth / welcome."""
    assert path not in routes_source, (
        f"La route {path} ne doit pas être pré-câblée dans le squelette nu."
    )


@pytest.mark.parametrize("token", OPTIN_CODE_TOKENS)
def test_aucun_code_optin_dans_la_couche_mvc(token):
    """Aucun fichier de la couche applicative mvc/ n'importe ni ne câble d'opt-in.

    Le scan vise mvc/ (routes, contrôleurs, vues, modèles). app.py / config.py
    sont de la plomberie core (copies verbatim, gardées par l'anti-dérive de
    test_skeleton_tree_001) : ils référencent légitimement forge_mvc_files
    (service média optionnel, import paresseux) — hors périmètre de ce scan.
    """
    offenders = []
    for path in iter_skeleton_files():
        rel = path.relative_to(DATA_DIR).as_posix()
        if not rel.startswith("mvc/"):
            continue
        if path.suffix not in {".py", ".html", ".snippet"}:
            continue
        if token in path.read_text(encoding="utf-8"):
            offenders.append(rel)
    assert not offenders, (
        f"{token!r} présent dans la couche mvc/ du squelette nu : {offenders} "
        "(les opt-ins s'ajoutent via starters / forge starter:build)."
    )
