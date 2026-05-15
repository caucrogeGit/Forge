from __future__ import annotations

from pathlib import Path

import forge_cli.output as out
from forge_cli.public_page import (
    CONTROLLER_PATH,
    PUBLIC_CONTENT_BLOCK,
    PUBLIC_LAYOUT,
    PUBLIC_SCRIPTS_BLOCK,
    PUBLIC_TITLE_BLOCK,
    ROUTES_PATH,
    TEMPLATE_DIR,
    MakePublicPageResult,
    build_public_page_spec,
    _ensure_controller_method,
    _ensure_route,
)

_CONTACT_SLUG = "contact"
_CONTACT_TEMPLATE_REL = TEMPLATE_DIR / "contact.html"


def build_contact_template() -> str:
    return (
        f'{{% extends "{PUBLIC_LAYOUT}" %}}\n'
        "\n"
        f"{{% block {PUBLIC_TITLE_BLOCK} %}}{{{{ trans('public.contact.title') }}}}{{% endblock %}}\n"
        "\n"
        f"{{% block {PUBLIC_CONTENT_BLOCK} %}}\n"
        '<section class="mx-auto max-w-4xl px-6 py-12">\n'
        '    <h1 class="text-3xl font-bold text-gray-900">{{ trans(\'public.contact.title\') }}</h1>\n'
        '    <p class="mt-4 text-gray-600">\n'
        "        {{ trans('public.contact.intro') }}\n"
        "    </p>\n"
        '    <div class="mt-8 grid gap-6 md:grid-cols-2">\n'
        '        <div class="rounded-lg border border-gray-200 bg-white p-6">\n'
        "            <h2 class=\"text-xl font-semibold text-gray-800\">{{ trans('public.contact.coordinates') }}</h2>\n"
        '            <p class="mt-4 text-gray-700">{{ trans(\'public.contact.email_label\') }} :\n'
        '                <a href="mailto:contact@example.com"'
        ' class="text-indigo-600 hover:underline">contact@example.com</a>\n'
        "            </p>\n"
        "            <p class=\"mt-2 text-gray-700\">{{ trans('public.contact.phone') }} : 00 00 00 00 00</p>\n"
        "        </div>\n"
        '        <div class="rounded-lg border border-gray-200 bg-white p-6">\n'
        "            <h2 class=\"text-xl font-semibold text-gray-800\">{{ trans('public.contact.address') }}</h2>\n"
        "            <p class=\"mt-4 text-gray-700\">{{ trans('public.contact.address_placeholder') }}</p>\n"
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
    template_path = project_root / _CONTACT_TEMPLATE_REL
    controller_path = project_root / CONTROLLER_PATH
    routes_path = project_root / ROUTES_PATH

    result = MakePublicPageResult(
        spec=spec,
        template_path=template_path,
        controller_path=controller_path,
        routes_path=routes_path,
    )

    template_path.parent.mkdir(parents=True, exist_ok=True)
    if template_path.exists():
        result.preserved.append(_CONTACT_TEMPLATE_REL.as_posix())
    else:
        template_path.write_text(build_contact_template(), encoding="utf-8")
        result.created.append(_CONTACT_TEMPLATE_REL.as_posix())

    controller_changed, controller_warning = _ensure_controller_method(controller_path, spec)
    if controller_changed:
        result.created.append(CONTROLLER_PATH.as_posix())
    else:
        result.preserved.append(CONTROLLER_PATH.as_posix())
    if controller_warning:
        result.warnings.append(controller_warning)

    route_changed, route_warning = _ensure_route(routes_path, spec)
    if route_changed:
        result.created.append(ROUTES_PATH.as_posix())
    else:
        result.preserved.append(ROUTES_PATH.as_posix())
    if route_warning:
        result.warnings.append(route_warning)

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


def main(args: list[str] | None = None, *, root: Path | None = None) -> MakePublicPageResult:
    if args is None:
        args = []
    if args:
        raise SystemExit("Usage : forge make:public-contact  (aucun argument attendu)")
    result = make_public_contact(root=root)
    print_result(result)
    return result
