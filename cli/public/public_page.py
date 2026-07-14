# pyright: strict
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

import cli._support.output as out
from cli.public._shared import (
    build_public_routes_file,
    ensure_routes_file as _ensure_routes_file,
    ensure_trailing_newline as _ensure_trailing_newline,
    has_router_factory as _has_router_factory,
    insert_import as _insert_import,
    public_routes_branchement,
)
from core.http.slug import slugify


TEMPLATE_DIR = Path("mvc/views/public")
CONTROLLER_PATH = Path("mvc/controllers/public_pages_controller.py")
# ADR-068 : le routage est un package ; l'injection cible la racine de composition.
ROUTES_PATH = Path("mvc/routes") / "__init__.py"
PUBLIC_LAYOUT = "layouts/base.html"
PUBLIC_TITLE_BLOCK = "title"
PUBLIC_CONTENT_BLOCK = "content"
PUBLIC_SCRIPTS_BLOCK = "scripts"


@dataclass
class PublicPageSpec:
    source: str
    slug: str
    method_name: str
    route_name: str
    title: str


@dataclass
class MakePublicPageResult:
    spec: PublicPageSpec
    template_path: Path
    controller_path: Path
    routes_path: Path
    created: list[str] = field(default_factory=list[str])
    preserved: list[str] = field(default_factory=list[str])
    warnings: list[str] = field(default_factory=list[str])


def _slugify(name: str) -> str:
    """Valide un nom de page et le réduit à une URL slug.

    Rejette explicitement les chemins (sécurité ``make:public-page`` : on ne
    crée pas une page à partir de ``../admin``), puis délègue la transformation
    au module URL-slug canonique ``core.http.slug`` (ADR-017, §11).
    """
    value = name.strip()
    if any(part in value for part in ("/", "\\", "..")):
        raise ValueError("Nom de page invalide : les chemins ne sont pas autorisés.")
    return slugify(value)


def build_public_page_spec(name: str) -> PublicPageSpec:
    slug = _slugify(name)
    method_name = slug.replace("-", "_")
    title = " ".join(part.capitalize() for part in slug.split("-"))
    return PublicPageSpec(
        source=name,
        slug=slug,
        method_name=method_name,
        route_name=f"public_pages-{method_name}",
        title=title,
    )


def build_public_template(spec: PublicPageSpec) -> str:
    return (
        f'{{% extends "{PUBLIC_LAYOUT}" %}}\n'
        "\n"
        f"{{% block {PUBLIC_TITLE_BLOCK} %}}{spec.title}{{% endblock %}}\n"
        "\n"
        f"{{% block {PUBLIC_CONTENT_BLOCK} %}}\n"
        '<section class="mx-auto max-w-5xl px-6 py-12">\n'
        f'    <h1 class="text-3xl font-bold">{spec.title}</h1>\n'
        '    <p class="mt-4 text-gray-600">\n'
        "        Page publique générée par Forge.\n"
        "    </p>\n"
        "</section>\n"
        "{% endblock %}\n"
    )


def build_controller_method(spec: PublicPageSpec) -> str:
    return (
        "\n"
        "    @staticmethod\n"
        f"    def {spec.method_name}(request: Request) -> Response:\n"
        f'        return BaseController.render("public/{spec.slug}.html", request=request)\n'
    )


def build_controller(spec: PublicPageSpec) -> str:
    return (
        "from core.http.request import Request\n"
        "from core.http.response import Response\n"
        "from core.mvc.controller.base_controller import BaseController\n"
        "\n"
        "\n"
        "class PublicPagesController(BaseController):\n"
        f"{build_controller_method(spec)}"
    )


_REQUEST_IMPORT_LINE = "from core.http.request import Request\n"
_RESPONSE_IMPORT_LINE = "from core.http.response import Response\n"


def _ensure_typed_imports(content: str) -> str:
    """Insère les imports Request/Response si manquants (DX-TYPED-SKELETONS-001).

    Insère AVANT la première importation `core.mvc...` repérée, ou à défaut en
    tête du fichier. Idempotent : ne dédouble jamais une ligne déjà présente.
    """
    needs_request = _REQUEST_IMPORT_LINE.rstrip() not in content
    needs_response = _RESPONSE_IMPORT_LINE.rstrip() not in content
    if not needs_request and not needs_response:
        return content

    lines = content.splitlines(keepends=True)
    anchor = next(
        (i for i, line in enumerate(lines)
         if line.startswith("from core.mvc.controller")),
        0,
    )
    insertion: list[str] = []
    if needs_request:
        insertion.append(_REQUEST_IMPORT_LINE)
    if needs_response:
        insertion.append(_RESPONSE_IMPORT_LINE)
    lines[anchor:anchor] = insertion
    return "".join(lines)


def ensure_controller_method(controller_path: Path, spec: PublicPageSpec) -> tuple[bool, str | None]:
    if not controller_path.exists():
        controller_path.parent.mkdir(parents=True, exist_ok=True)
        controller_path.write_text(build_controller(spec), encoding="utf-8")
        return True, None

    content = controller_path.read_text(encoding="utf-8")
    if re.search(rf"^\s+def\s+{re.escape(spec.method_name)}\s*\(", content, re.MULTILINE):
        return False, None

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return False, f"Contrôleur non modifié automatiquement : {controller_path.as_posix()}"

    target_class = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "PublicPagesController"
        ),
        None,
    )
    if target_class is None or target_class.end_lineno is None:
        return False, f"Contrôleur à compléter manuellement : {controller_path.as_posix()}"

    lines = _ensure_trailing_newline(content).splitlines(keepends=True)
    insert_at = target_class.end_lineno
    lines.insert(insert_at, build_controller_method(spec))
    new_content = _ensure_typed_imports("".join(lines))
    controller_path.write_text(new_content, encoding="utf-8")
    return True, None


def _route_exists(content: str, spec: PublicPageSpec) -> bool:
    route_path = f'"/{spec.slug}"'
    route_name = f'name="{spec.route_name}"'
    return route_path in content or route_name in content


def build_route_block(spec: PublicPageSpec) -> str:
    return (
        "\n"
        "with router.group(\"\", public=True) as public:\n"
        f'    public.add("GET", "/{spec.slug}", PublicPagesController.{spec.method_name}, '
        f'name="{spec.route_name}")\n'
    )


def ensure_route(routes_path: Path, spec: PublicPageSpec) -> tuple[bool, str | None]:
    _ensure_routes_file(routes_path)
    content = routes_path.read_text(encoding="utf-8")
    import_line = "from mvc.controllers.public_pages_controller import PublicPagesController"
    changed = import_line not in content
    content = _insert_import(content, import_line)

    if _route_exists(content, spec):
        routes_path.write_text(_ensure_trailing_newline(content), encoding="utf-8")
        return changed, None

    if not _has_router_factory(content):
        return False, f"Route à ajouter manuellement dans {routes_path.as_posix()} : GET /{spec.slug}"

    content = _ensure_trailing_newline(content) + build_route_block(spec)
    routes_path.write_text(content, encoding="utf-8")
    return True, None


def _page_register_name(spec: PublicPageSpec) -> str:
    """Nom de la fonction/fichier de routes d'une page (slug kebab → snake)."""
    return spec.slug.replace("-", "_")


def make_public_page(name: str, *, root: Path | None = None) -> MakePublicPageResult:
    project_root = (root or Path.cwd()).resolve()
    spec = build_public_page_spec(name)
    register_name = _page_register_name(spec)
    routes_rel = Path("mvc/routes") / f"{register_name}_routes.py"
    template_path = project_root / TEMPLATE_DIR / f"{spec.slug}.html"
    controller_path = project_root / CONTROLLER_PATH
    routes_path = project_root / routes_rel
    result = MakePublicPageResult(
        spec=spec,
        template_path=template_path,
        controller_path=controller_path,
        routes_path=routes_path,
    )

    template_path.parent.mkdir(parents=True, exist_ok=True)
    if template_path.exists():
        result.preserved.append(TEMPLATE_DIR.joinpath(f"{spec.slug}.html").as_posix())
    else:
        template_path.write_text(build_public_template(spec), encoding="utf-8")
        result.created.append(TEMPLATE_DIR.joinpath(f"{spec.slug}.html").as_posix())

    controller_changed, controller_warning = ensure_controller_method(controller_path, spec)
    if controller_changed:
        result.created.append(CONTROLLER_PATH.as_posix())
    else:
        result.preserved.append(CONTROLLER_PATH.as_posix())
    if controller_warning:
        result.warnings.append(controller_warning)

    # ADR-085 : fichier de routes dédié + affichage du branchement, jamais
    # d'injection dans mvc/routes/__init__.py.
    routes_path.parent.mkdir(parents=True, exist_ok=True)
    if routes_path.exists():
        result.preserved.append(routes_rel.as_posix())
    else:
        routes_path.write_text(
            build_public_routes_file(
                register_name,
                "from mvc.controllers.public_pages_controller import PublicPagesController",
                [
                    f'public.add("GET", "/{spec.slug}", '
                    f'PublicPagesController.{spec.method_name}, name="{spec.route_name}")'
                ],
            ),
            encoding="utf-8",
        )
        result.created.append(routes_rel.as_posix())

    return result


def print_result(result: MakePublicPageResult) -> None:
    spec = result.spec
    rel_template = TEMPLATE_DIR.joinpath(f"{spec.slug}.html").as_posix()
    print(f"Page publique générée : {spec.slug}")
    print(f"Route : /{spec.slug}")
    print(f"Template : {rel_template}")
    print(f"Contrôleur : {CONTROLLER_PATH.as_posix()}")
    for path in result.created:
        print(out.created(path))
    for path in result.preserved:
        print(out.preserved(path))
    if rel_template in result.preserved:
        print(f"Page publique déjà existante : {rel_template}")
        print("Aucun écrasement effectué.")
    for warning in result.warnings:
        print(out.warn(warning))
    print()
    print(public_routes_branchement(_page_register_name(spec)))


def main(args: list[str], *, root: Path | None = None) -> MakePublicPageResult:
    if len(args) != 1:
        raise SystemExit("Usage : forge make:public-page <nom>")
    try:
        result = make_public_page(args[0], root=root)
    except ValueError as exc:
        raise SystemExit(f"Erreur : {exc}") from exc
    print_result(result)
    return result
