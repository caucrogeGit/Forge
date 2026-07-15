# pyright: strict
from __future__ import annotations

from pathlib import Path

import cli._support.output as out
from cli.public._shared import build_public_routes_file, public_routes_branchement, scaffold_into
from cli.public.public_page import (
    CONTROLLER_PATH,
    PUBLIC_CONTENT_BLOCK,
    PUBLIC_LAYOUT,
    PUBLIC_SCRIPTS_BLOCK,
    PUBLIC_TITLE_BLOCK,
    TEMPLATE_DIR,
    MakePublicPageResult,
    build_public_page_spec,
    ensure_controller_method as _ensure_controller_method,
)

_CONTACT_SLUG = "contact"
_CONTACT_TEMPLATE_REL = TEMPLATE_DIR / "contact.html"


def build_contact_template() -> str:
    return (
        f'{{% extends "{PUBLIC_LAYOUT}" %}}\n'
        "\n"
        f"{{% block {PUBLIC_TITLE_BLOCK} %}}Contact{{% endblock %}}\n"
        "\n"
        f"{{% block {PUBLIC_CONTENT_BLOCK} %}}\n"
        '<section class="mx-auto max-w-4xl px-6 py-12">\n'
        '    <h1 class="text-3xl font-bold text-gray-900">Contact</h1>\n'
        '    <p class="mt-4 text-gray-600">\n'
        "        Vous pouvez nous contacter avec les informations ci-dessous.\n"
        "    </p>\n"
        '    <div class="mt-8 grid gap-6 md:grid-cols-2">\n'
        '        <div class="rounded-lg border border-gray-200 bg-white p-6">\n'
        "            <h2 class=\"text-xl font-semibold text-gray-800\">Coordonnées</h2>\n"
        '            <p class="mt-4 text-gray-700">Email :\n'
        '                <a href="mailto:contact@example.com"'
        ' class="text-indigo-600 hover:underline">contact@example.com</a>\n'
        "            </p>\n"
        "            <p class=\"mt-2 text-gray-700\">Téléphone : 00 00 00 00 00</p>\n"
        "        </div>\n"
        '        <div class="rounded-lg border border-gray-200 bg-white p-6">\n'
        "            <h2 class=\"text-xl font-semibold text-gray-800\">Adresse</h2>\n"
        "            <p class=\"mt-4 text-gray-700\">Adresse à compléter</p>\n"
        "        </div>\n"
        "    </div>\n"
        "</section>\n"
        "{% endblock %}\n"
        "\n"
        f"{{% block {PUBLIC_SCRIPTS_BLOCK} %}}{{% endblock %}}\n"
    )


def make_public_contact(*, root: Path | None = None) -> MakePublicPageResult:
    spec = build_public_page_spec(_CONTACT_SLUG)
    project_root = (root or Path.cwd()).resolve()
    routes_rel = Path("mvc/routes") / f"{_CONTACT_SLUG}_routes.py"
    template_path = project_root / _CONTACT_TEMPLATE_REL
    controller_path = project_root / CONTROLLER_PATH
    routes_path = project_root / routes_rel

    result = MakePublicPageResult(
        spec=spec,
        template_path=template_path,
        controller_path=controller_path,
        routes_path=routes_path,
    )

    scaffold_into(template_path, build_contact_template(), _CONTACT_TEMPLATE_REL.as_posix(), result)

    controller_changed, controller_warning = _ensure_controller_method(controller_path, spec)
    if controller_changed:
        result.created.append(CONTROLLER_PATH.as_posix())
    else:
        result.preserved.append(CONTROLLER_PATH.as_posix())
    if controller_warning:
        result.warnings.append(controller_warning)

    # ADR-085 : fichier de routes dédié + affichage, jamais d'injection.
    scaffold_into(
        routes_path,
        build_public_routes_file(
            _CONTACT_SLUG,
            "from mvc.controllers.public_pages_controller import PublicPagesController",
            [
                f'public.add("GET", "/{spec.slug}", '
                f'PublicPagesController.{spec.method_name}, name="{spec.route_name}")'
            ],
        ),
        routes_rel.as_posix(), result,
    )

    return result


def print_result(result: MakePublicPageResult) -> None:
    rel_template = _CONTACT_TEMPLATE_REL.as_posix()
    print("Page contact générée")
    print("Route : /contact")
    print(f"Template : {rel_template}")
    print(f"Contrôleur : {CONTROLLER_PATH.as_posix()}")
    for path in result.created:
        print(out.created(path))
    for path in result.preserved:
        print(out.preserved(path))
    if rel_template in result.preserved:
        print(f"Page contact déjà existante : {rel_template}")
        print("Aucun écrasement effectué.")
    for warning in result.warnings:
        print(out.warn(warning))
    print()
    print(public_routes_branchement(_CONTACT_SLUG))


def main(args: list[str] | None = None, *, root: Path | None = None) -> MakePublicPageResult:
    if args is None:
        args = []
    if args:
        raise SystemExit("Usage : forge make:public-contact  (aucun argument attendu)")
    result = make_public_contact(root=root)
    print_result(result)
    return result
