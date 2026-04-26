"""Opérations sur mvc/routes.py : injection, marqueurs, snippet, bloc généré."""

from __future__ import annotations

import re
from pathlib import Path

from forge_cli.starters._exceptions import StarterBuildError
from forge_cli.starters.file_ops import to_snake


def build_route_block(meta: dict, *, public: bool) -> str:
    """Construit le bloc de routes à injecter pour un starter CRUD simple."""
    routes = meta.get("routes", {})
    prefix = routes.get("prefix", "")
    actions = routes.get("actions", [])
    entity = meta["entity"]
    controller_class = f"{entity}Controller"
    marker = meta["routes_marker"]
    snake = to_snake(entity)

    group_args = f'"{prefix}", public=True, csrf=False' if public else f'"{prefix}"'

    lines = [
        f"# forge-starter:{marker}:start",
        f"from mvc.controllers.{snake}_controller import {controller_class}",
        "",
        f"with router.group({group_args}) as g:",
    ]
    for action in actions:
        lines.append(
            f'    g.add("{action["method"]}", {action["path"]!r:<16},'
            f' {controller_class}.{action["action"]:<10}, name="{action["name"]}")'
        )
    lines.append(f"# forge-starter:{marker}:end")
    return "\n".join(lines) + "\n"


def read_snippet(meta: dict) -> str:
    """Lit le fichier routes.py.snippet du starter."""
    path = meta["_dir"] / meta.get("routes_snippet", "routes.py.snippet")
    if not path.exists():
        raise StarterBuildError(f"Snippet de routes introuvable : {path}")
    content = path.read_text(encoding="utf-8")
    return content if content.endswith("\n") else content + "\n"


def routes_from_snippet(snippet: str) -> list[tuple[str, str]]:
    """Extrait les paires (méthode, chemin complet) depuis un snippet de routes."""
    routes: list[tuple[str, str]] = []
    current_prefix = ""
    group_re = re.compile(r'with router\.group\("([^"]*)"')
    route_re = re.compile(r'\.add\("([^"]+)",\s+"([^"]*)"')
    for line in snippet.splitlines():
        m = group_re.search(line)
        if m:
            current_prefix = m.group(1)
            continue
        m = route_re.search(line)
        if m:
            method, path = m.groups()
            full = (current_prefix.rstrip("/") + "/" + path.lstrip("/")).rstrip("/") or "/"
            routes.append((method, full))
    return routes


def marker_present(routes_py: Path, marker: str) -> bool:
    if not routes_py.exists():
        return False
    return f"# forge-starter:{marker}:start" in routes_py.read_text(encoding="utf-8")


def remove_marker(routes_py: Path, marker: str) -> None:
    if not routes_py.exists():
        return
    content = routes_py.read_text(encoding="utf-8")
    pattern = (
        rf"\n# forge-starter:{re.escape(marker)}:start"
        rf".*?# forge-starter:{re.escape(marker)}:end\n"
    )
    routes_py.write_text(re.sub(pattern, "\n", content, flags=re.DOTALL), encoding="utf-8")


def inject_block(routes_py: Path, block: str) -> None:
    content = routes_py.read_text(encoding="utf-8")
    if not content.endswith("\n"):
        content += "\n"
    routes_py.write_text(content + "\n" + block, encoding="utf-8")


def replace_home_route(routes_py: Path, home_route: str) -> None:
    """Remplace GET / → HomeController.index par une redirection vers home_route.

    La route nommée "home" est conservée mais son handler devient une lambda
    qui émet un 302. L'import HomeController est retiré s'il n'est plus utilisé.
    Idempotent : sans effet si le handler n'est plus HomeController.index.
    """
    if not routes_py.exists() or home_route == "/":
        return
    content = routes_py.read_text(encoding="utf-8")

    old_handler = 'pub.add("GET", "/", HomeController.index, name="home")'
    if old_handler not in content:
        return

    bc_import = "from core.mvc.controller.base_controller import BaseController"
    if bc_import not in content:
        content = bc_import + "\n" + content

    new_handler = (
        f'pub.add("GET", "/", '
        f'lambda req: BaseController.redirect("{home_route}"), '
        f'name="home")'
    )
    content = content.replace(old_handler, new_handler)

    hc_import = "from mvc.controllers.home_controller import HomeController\n"
    if hc_import in content and "HomeController" not in content.replace(hc_import, ""):
        content = content.replace(hc_import, "")

    routes_py.write_text(content, encoding="utf-8")


def remove_legacy_auth_block(routes_py: Path) -> None:
    """Retire le bloc auth public livré par le squelette Forge neuf."""
    if not routes_py.exists():
        return
    content = routes_py.read_text(encoding="utf-8")
    legacy = (
        '\nwith router.group("", public=True) as pub:\n'
        '    pub.add("GET",  "/login",  AuthController.login_form, name="login_form")\n'
        '    pub.add("POST", "/login",  AuthController.login,      name="login")\n'
        '    pub.add("POST", "/logout", AuthController.logout,     name="logout")\n'
    )
    if legacy not in content:
        return
    content = content.replace(
        "from mvc.controllers.auth_controller import AuthController\n", ""
    )
    routes_py.write_text(content.replace(legacy, "\n"), encoding="utf-8")
