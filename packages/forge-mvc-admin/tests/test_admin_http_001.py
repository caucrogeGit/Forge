"""Tests de l'intégration HTTP du dashboard (ADMIN-DASHBOARD-MINIMAL-001).

- `register_admin_routes` branche `GET /admin`, nommée et non publique ;
- le template embarqué `admin/dashboard.html` rend la liste des ressources
  (résolu via le loader d'opt-in enregistré par le paquet, ADR-046) ;
- l'état vide affiche un message d'invite.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_admin")

from core.http.router import Router
from integrations.jinja2.renderer import Jinja2Renderer
from forge_mvc_admin import AdminRegistry, AdminResource, register_admin_routes


def _resource(slug: str = "articles", entity: str = "Article") -> AdminResource:
    return AdminResource(
        entity=entity,
        slug=slug,
        label=entity,
        plural_label=f"{entity}s",
        list_fields=("title",),
        form_fields=("title",),
        table=slug.replace("-", "_"),
    )


def test_register_admin_routes_dashboard_protege():
    router = Router()
    register_admin_routes(router, registry=AdminRegistry())
    matched = router.match("GET", "/admin")
    assert matched is not None, "GET /admin doit être enregistrée"
    route, _params = matched
    assert route.name == "admin-dashboard"
    assert route.public is False, "/admin ne doit jamais être publique"


def test_register_admin_routes_liste_protegee():
    router = Router()
    register_admin_routes(router, registry=AdminRegistry())
    matched = router.match("GET", "/admin/articles")
    assert matched is not None, "GET /admin/<slug> doit être enregistrée"
    route, params = matched
    assert route.name == "admin-resource-list"
    assert route.public is False, "/admin/<slug> ne doit jamais être publique"
    assert params.get("slug") == "articles"


def test_dashboard_template_liste_les_ressources(tmp_path: Path):
    views = tmp_path / "views"
    views.mkdir()
    renderer = Jinja2Renderer(str(views))
    html = renderer.render("admin/dashboard.html", {"resources": (_resource(),)})
    assert "Articles" in html
    assert "/admin/articles" in html


def test_dashboard_etat_vide(tmp_path: Path):
    views = tmp_path / "views"
    views.mkdir()
    renderer = Jinja2Renderer(str(views))
    html = renderer.render("admin/dashboard.html", {"resources": ()})
    assert "Aucune ressource déclarée" in html


def test_list_template_affiche_lignes_et_colonnes(tmp_path: Path):
    views = tmp_path / "views"
    views.mkdir()
    renderer = Jinja2Renderer(str(views))
    html = renderer.render(
        "admin/list.html",
        {
            "resource": _resource(),
            "columns": ("title",),
            "rows": [{"title": "Bonjour"}, {"title": "Forge"}],
            "pagination": {"page": 1, "nb_pages": 1, "has_prev": False, "has_next": False},
        },
    )
    assert "<th>title</th>" in html
    assert "Bonjour" in html and "Forge" in html


def test_list_template_etat_vide(tmp_path: Path):
    views = tmp_path / "views"
    views.mkdir()
    renderer = Jinja2Renderer(str(views))
    html = renderer.render(
        "admin/list.html",
        {
            "resource": _resource(),
            "columns": ("title",),
            "rows": [],
            "pagination": {"page": 1, "nb_pages": 1, "has_prev": False, "has_next": False},
        },
    )
    assert "Aucune ligne" in html
