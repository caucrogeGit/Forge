from __future__ import annotations

from pathlib import Path

from forge_cli.public_page import (
    PUBLIC_CONTENT_BLOCK,
    PUBLIC_LAYOUT,
    PUBLIC_SCRIPTS_BLOCK,
    PUBLIC_TITLE_BLOCK,
    build_public_page_spec,
    build_public_template,
    make_public_page,
)


PUBLIC_LAYOUT_PATH = Path("mvc/views/layouts/public.html")
COMPONENTS_DIR = Path("mvc/views/components")


def _prepare_project(root: Path) -> None:
    (root / "mvc" / "views" / "layouts").mkdir(parents=True, exist_ok=True)
    (root / "mvc" / "views" / "layouts" / "public.html").write_text(
        PUBLIC_LAYOUT_PATH.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (root / "mvc" / "routes.py").parent.mkdir(parents=True, exist_ok=True)
    (root / "mvc" / "routes.py").write_text(
        "from core.http.router import Router\n"
        "\n"
        "router = Router()\n",
        encoding="utf-8",
    )


def test_layout_public_existe_dans_le_squelette():
    assert PUBLIC_LAYOUT_PATH.is_file()


def test_layout_public_expose_les_blocs_stables():
    layout = PUBLIC_LAYOUT_PATH.read_text(encoding="utf-8")

    assert f"{{% block {PUBLIC_TITLE_BLOCK} %}}" in layout
    assert f"{{% block {PUBLIC_CONTENT_BLOCK} %}}" in layout
    assert f"{{% block {PUBLIC_SCRIPTS_BLOCK} %}}" in layout


def test_layout_public_est_compatible_tailwind_et_sans_dependance_front_forcee():
    layout = PUBLIC_LAYOUT_PATH.read_text(encoding="utf-8")

    assert '<link rel="stylesheet" href="/static/tailwind.css">' in layout
    assert "htmx" not in layout.lower()
    assert "alpine" not in layout.lower()
    assert "trans(" not in layout
    assert "_(" not in layout


def test_layout_public_reste_separe_du_layout_admin_et_crud():
    layout = PUBLIC_LAYOUT_PATH.read_text(encoding="utf-8")

    assert "<nav" not in layout
    assert "csrf_token" not in layout
    assert "crud-results" not in layout
    assert "layouts/admin.html" not in layout


def test_dossier_components_public_compatible_existe():
    assert COMPONENTS_DIR.is_dir()
    assert (COMPONENTS_DIR / "button.html").is_file()
    assert (COMPONENTS_DIR / "alert.html").is_file()


def test_template_public_genere_utilise_layout_et_blocs_documentes():
    template = build_public_template(build_public_page_spec("accueil"))

    assert f'{{% extends "{PUBLIC_LAYOUT}" %}}' in template
    assert f"{{% block {PUBLIC_TITLE_BLOCK} %}}Accueil{{% endblock %}}" in template
    assert f"{{% block {PUBLIC_CONTENT_BLOCK} %}}" in template
    assert "{% block contenu %}" not in template


def test_template_public_genere_nest_pas_lie_au_crud_admin_ni_aux_dependances_optionnelles():
    template = build_public_template(build_public_page_spec("accueil"))

    assert "make:crud" not in template
    assert "crud" not in template.lower()
    assert "layouts/admin.html" not in template
    assert "htmx" not in template.lower()
    assert "hx-" not in template
    assert "alpine" not in template.lower()
    assert "_(" not in template
    assert "<script" not in template
    assert "<form" not in template


def test_generation_public_page_respecte_le_contrat_et_reste_idempotente(tmp_path):
    _prepare_project(tmp_path)

    make_public_page("accueil", root=tmp_path)
    first_template = (tmp_path / "mvc" / "views" / "public" / "accueil.html").read_text(
        encoding="utf-8"
    )
    first_routes = (tmp_path / "mvc" / "routes.py").read_text(encoding="utf-8")
    make_public_page("accueil", root=tmp_path)

    assert (tmp_path / "mvc" / "views" / "public" / "accueil.html").read_text(
        encoding="utf-8"
    ) == first_template
    routes = (tmp_path / "mvc" / "routes.py").read_text(encoding="utf-8")
    assert routes.count('"/accueil"') == 1
    assert routes.count('name="public_accueil"') == 1
    assert first_routes.count('"/accueil"') == 1
