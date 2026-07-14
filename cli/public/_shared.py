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

import importlib.util


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


def build_public_routes_file(register_name: str, controller_import: str, add_lines: list[str]) -> str:
    """Contenu d'un fichier `mvc/routes/<register_name>_routes.py` (ADR-068/085).

    Un générateur `make:public-*` produit ses routes dans un fichier dédié plutôt
    que de les injecter dans `mvc/routes/__init__.py` (ADR-085) : Forge ne réécrit
    jamais un fichier utilisateur. `add_lines` sont les instructions
    `public.add(...)` (sans indentation), branchées dans un groupe public.
    """
    body = "\n".join(f"        {line}" for line in add_lines)
    return "\n".join([
        f'"""Routes publiques {register_name} (ADR-068)."""',
        "from core.http.router import Router",
        controller_import,
        "",
        "",
        f"def register_{register_name}_routes(router: Router) -> None:",
        '    with router.group("", public=True) as public:',
        body,
        "",
    ])


def public_routes_branchement(register_name: str) -> str:
    """Les deux lignes de branchement à afficher (ADR-085 : jamais injectées)."""
    return "\n".join([
        "Branchement à ajouter dans mvc/routes/__init__.py :",
        "─" * 70,
        f"  from mvc.routes.{register_name}_routes import register_{register_name}_routes",
        f"  register_{register_name}_routes(router)",
    ])


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
