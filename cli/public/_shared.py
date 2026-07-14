# pyright: strict
"""Utilitaires de scaffolding partagés des générateurs de pages publiques
(CLI-PUBLIC-SHARED-001).

`make:public-page/list/show/form/contact` partagent des helpers purs de
manipulation de source (insertion d'imports, fabrique de routes, humanisation)
qui étaient définis dans `public_page`/`public_list` et importés en privé par
les autres modules (sous `# pyright: reportPrivateUsage=false`). Ils vivent
désormais ici, en API interne assumée du sous-paquet, sans reach-in privé
cross-module. Ce module ne dépend d'aucun générateur : pas de cycle.
"""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path


def humanize(name: str) -> str:
    """Transforme un identifiant snake_case en libellé lisible."""
    return name.replace("_", " ").capitalize()


def ensure_trailing_newline(content: str) -> str:
    """Garantit que `content` se termine par un saut de ligne."""
    return content if content.endswith("\n") else content + "\n"


def insert_import(content: str, import_line: str) -> str:
    """Insère `import_line` après le bloc d'imports de tête, si absente."""
    if import_line in content:
        return content

    lines = ensure_trailing_newline(content).splitlines(keepends=True)
    insert_at = 0
    for index, line in enumerate(lines):
        if line.startswith("from ") or line.startswith("import "):
            insert_at = index + 1
            continue
        if line.strip() == "":
            continue
        break
    lines.insert(insert_at, import_line + "\n")
    return "".join(lines)


def ensure_import(content: str, import_line: str) -> tuple[str, bool]:
    """Insère `import_line` si absente. Retourne (contenu, a_été_ajoutée)."""
    if import_line in content:
        return content, False
    return insert_import(content, import_line), True


def ensure_routes_file(routes_path: Path) -> bool:
    """Crée `routes_path` avec un routeur nu s'il n'existe pas. True si créé."""
    if routes_path.exists():
        return False
    routes_path.parent.mkdir(parents=True, exist_ok=True)
    routes_path.write_text(
        "from core.http.router import Router\n"
        "\n"
        "router = Router()\n",
        encoding="utf-8",
    )
    return True


def has_router_factory(content: str) -> bool:
    """Vrai si `content` contient une affectation module-level `router = Router(...)`.

    Détection par AST plutôt que par sous-chaîne : un commentaire ou une chaîne
    contenant « router = Router() » ne doit pas être pris pour la vraie fabrique
    (sinon on injecte un bloc référençant un `router` inexistant, ce qui casse
    `routes.py` à l'import), et une affectation réelle écrite différemment
    (espaces, arguments) doit bien être reconnue.
    """
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return False
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "router" for t in node.targets):
            continue
        call = node.value
        if isinstance(call, ast.Call):
            func = call.func
            if isinstance(func, ast.Name) and func.id == "Router":
                return True
            if isinstance(func, ast.Attribute) and func.attr == "Router":
                return True
    return False


def require_entities_module() -> None:
    """Échoue proprement si le moteur d'entités (forge-mvc-entities) est absent.

    make:public-list/show/form lisent le contrat JSON de l'entité via ce moteur
    (ADR-070) ; sans l'opt-in, on rend un message d'installation plutôt qu'une
    traceback brute d'import (principes 8 et 10).
    """
    if importlib.util.find_spec("forge_mvc_entities") is None:
        from cli._support.errors import cli_fail
        cli_fail(
            "module forge-mvc-entities non installé.",
            hint="installe le moteur d'entités : pip install --pre forge-mvc-entities",
        )
