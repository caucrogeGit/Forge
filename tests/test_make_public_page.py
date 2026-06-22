from __future__ import annotations

from pathlib import Path

import pytest

from cli.public.public_page import (
    _has_router_factory,
    build_public_page_spec,
    main,
    make_public_page,
)


def _prepare_project(root: Path) -> None:
    (root / "mvc" / "views" / "layouts").mkdir(parents=True, exist_ok=True)
    (root / "mvc" / "views" / "layouts" / "public.html").write_text(
        '{% block title %}Forge{% endblock %}\n'
        "{% block content %}{% endblock %}\n",
        encoding="utf-8",
    )
    (root / "mvc" / "routes.py").parent.mkdir(parents=True, exist_ok=True)
    (root / "mvc" / "routes.py").write_text(
        "from core.http.router import Router\n"
        "from mvc.controllers.home_controller import HomeController\n"
        "\n"
        "router = Router()\n"
        "\n"
        "with router.group(\"\", public=True) as public:\n"
        "    public.add(\"GET\", \"/\", HomeController.index, name=\"home\")\n",
        encoding="utf-8",
    )


def _read(root: Path, path: str) -> str:
    return (root / path).read_text(encoding="utf-8")


def test_make_public_page_genere_template_public(tmp_path):
    _prepare_project(tmp_path)

    make_public_page("accueil", root=tmp_path)

    template = _read(tmp_path, "mvc/views/public/accueil.html")
    assert '{% extends "layouts/public.html" %}' in template
    assert "{% block title %}Accueil{% endblock %}" in template
    assert "{% block content %}" in template
    assert "trans('public.page.generated')" in template


def test_make_public_page_ajoute_route_publique(tmp_path):
    _prepare_project(tmp_path)

    make_public_page("accueil", root=tmp_path)

    routes = _read(tmp_path, "mvc/routes.py")
    assert "from mvc.controllers.public_pages_controller import PublicPagesController" in routes
    assert 'public.add("GET", "/accueil", PublicPagesController.accueil, name="public_pages-accueil")' in routes
    assert 'router.group("", public=True)' in routes


def test_make_public_page_ajoute_controleur_public(tmp_path):
    _prepare_project(tmp_path)

    make_public_page("accueil", root=tmp_path)

    controller = _read(tmp_path, "mvc/controllers/public_pages_controller.py")
    assert "class PublicPagesController(BaseController):" in controller
    assert "def accueil(request: Request) -> Response:" in controller
    assert 'BaseController.render("public/accueil.html", request=request)' in controller


def test_make_public_page_ne_duplique_pas_route_existante(tmp_path):
    _prepare_project(tmp_path)

    make_public_page("accueil", root=tmp_path)
    make_public_page("accueil", root=tmp_path)

    routes = _read(tmp_path, "mvc/routes.py")
    assert routes.count('"/accueil"') == 1
    assert routes.count('name="public_pages-accueil"') == 1


def test_make_public_page_necrase_pas_template_existant(tmp_path):
    _prepare_project(tmp_path)
    template = tmp_path / "mvc" / "views" / "public" / "accueil.html"
    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_text("contenu utilisateur\n", encoding="utf-8")

    result = make_public_page("accueil", root=tmp_path)

    assert template.read_text(encoding="utf-8") == "contenu utilisateur\n"
    assert "mvc/views/public/accueil.html" in result.preserved


def test_make_public_page_affiche_resume_et_preservation(tmp_path, capsys):
    _prepare_project(tmp_path)
    main(["accueil"], root=tmp_path)
    main(["accueil"], root=tmp_path)

    output = capsys.readouterr().out
    assert "Page publique générée : accueil" in output
    assert "Route : /accueil" in output
    assert "Template : mvc/views/public/accueil.html" in output
    assert "Contrôleur : mvc/controllers/public_pages_controller.py" in output
    assert "Page publique déjà existante : mvc/views/public/accueil.html" in output
    assert "Aucun écrasement effectué." in output


def test_make_public_page_normalise_les_noms_valides():
    assert build_public_page_spec("accueil").slug == "accueil"
    assert build_public_page_spec("ma-page").slug == "ma-page"
    assert build_public_page_spec("MaPage").slug == "ma-page"
    assert build_public_page_spec("MaPage").method_name == "ma_page"
    assert build_public_page_spec("MaPage").route_name == "public_pages-ma_page"


@pytest.mark.parametrize("name", ["../test", "/admin", "a/b", "..", "", "-", "admin/secret"])
def test_make_public_page_refuse_les_chemins_dangereux(name):
    with pytest.raises(ValueError):
        build_public_page_spec(name)


# --- Garde-fou B2 : détection de la fabrique `router` par AST (anti-corruption) ---


def test_has_router_factory_detecte_affectation_reelle():
    assert _has_router_factory("from core.http.router import Router\nrouter = Router()\n")


def test_has_router_factory_tolere_espaces_et_arguments():
    assert _has_router_factory("router  =  Router()\n")
    assert _has_router_factory("router = Router(prefix='/x')\n")


def test_has_router_factory_ignore_le_marqueur_en_commentaire():
    # Cause racine B2 : un commentaire contenant le marqueur ne doit pas leurrer
    # le générateur, sinon il injecte un bloc référençant un `router` inexistant.
    content = "from core.http.router import Router\n# exemple : router = Router()\n"
    assert not _has_router_factory(content)


def test_has_router_factory_ignore_le_marqueur_en_chaine():
    content = 'HELP = "router = Router()"\n'
    assert not _has_router_factory(content)


def test_has_router_factory_faux_si_syntaxe_invalide():
    assert not _has_router_factory("def (:\n")


def test_make_public_page_ninjecte_pas_si_router_seulement_en_commentaire(tmp_path):
    """Si `routes.py` ne contient le marqueur que dans un commentaire, la route
    n'est pas injectée (avertissement) et le fichier reste un module valide."""
    (tmp_path / "mvc" / "views" / "layouts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "mvc" / "views" / "layouts" / "public.html").write_text(
        "{% block title %}{% endblock %}{% block content %}{% endblock %}\n",
        encoding="utf-8",
    )
    routes_path = tmp_path / "mvc" / "routes.py"
    routes_path.write_text(
        "from core.http.router import Router\n"
        "# pensez a creer : router = Router()\n",
        encoding="utf-8",
    )

    result = make_public_page("accueil", root=tmp_path)

    routes = routes_path.read_text(encoding="utf-8")
    assert "PublicPagesController.accueil" not in routes  # pas de bloc injecté
    assert any("à ajouter manuellement" in w for w in result.warnings)
    compile(routes, "routes.py", "exec")  # toujours un module valide


def test_make_public_page_routes_resultantes_compilent(tmp_path):
    """Après injection sur un `routes.py` valide, le fichier produit compile
    (aucune référence `router` orpheline)."""
    _prepare_project(tmp_path)

    make_public_page("accueil", root=tmp_path)

    routes = _read(tmp_path, "mvc/routes.py")
    compile(routes, "routes.py", "exec")


def test_make_public_page_reste_independante_du_crud_admin(tmp_path):
    _prepare_project(tmp_path)

    make_public_page("accueil", root=tmp_path)

    generated = "\n".join(
        [
            _read(tmp_path, "mvc/views/public/accueil.html"),
            _read(tmp_path, "mvc/controllers/public_pages_controller.py"),
            _read(tmp_path, "mvc/routes.py"),
        ]
    )
    assert "make:crud" not in generated
    assert "Crud" not in generated
    assert "HTMX" not in generated
    assert "hx-" not in generated
    assert "<form" not in generated
    assert "<script" not in generated
