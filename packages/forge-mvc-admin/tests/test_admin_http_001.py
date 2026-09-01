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


def test_register_admin_routes_detail_protege():
    router = Router()
    register_admin_routes(router, registry=AdminRegistry())
    matched = router.match("GET", "/admin/articles/5")
    assert matched is not None, "GET /admin/<slug>/<id> doit être enregistrée"
    route, params = matched
    assert route.name == "admin-resource-detail"
    assert route.public is False
    assert params.get("slug") == "articles"
    assert params.get("id") == "5"


def test_register_admin_routes_formulaire_creation():
    router = Router()
    register_admin_routes(router, registry=AdminRegistry())
    get_new = router.match("GET", "/admin/articles/new")
    assert get_new is not None
    assert get_new[0].name == "admin-resource-new"
    assert get_new[0].public is False
    post_new = router.match("POST", "/admin/articles/new")
    assert post_new is not None
    assert post_new[0].name == "admin-resource-create"
    assert post_new[0].public is False


def test_route_new_litterale_avant_detail():
    # GET /admin/<slug>/new doit matcher la route `new`, pas la route détail {id}.
    router = Router()
    register_admin_routes(router, registry=AdminRegistry())
    matched = router.match("GET", "/admin/articles/new")
    assert matched is not None
    assert matched[0].name == "admin-resource-new", (
        "le littéral /new doit primer sur /{id}"
    )


def test_register_admin_routes_edition():
    router = Router()
    register_admin_routes(router, registry=AdminRegistry())
    get_edit = router.match("GET", "/admin/articles/5/edit")
    assert get_edit is not None
    assert get_edit[0].name == "admin-resource-edit"
    assert get_edit[0].public is False
    assert get_edit[1].get("slug") == "articles"
    assert get_edit[1].get("id") == "5"
    post_edit = router.match("POST", "/admin/articles/5/edit")
    assert post_edit is not None
    assert post_edit[0].name == "admin-resource-update"
    assert post_edit[0].public is False


def test_register_admin_routes_suppression():
    router = Router()
    register_admin_routes(router, registry=AdminRegistry())
    get_confirm = router.match("GET", "/admin/articles/5/delete")
    assert get_confirm is not None
    assert get_confirm[0].name == "admin-resource-delete-confirm"
    assert get_confirm[0].public is False
    post_delete = router.match("POST", "/admin/articles/5/delete")
    assert post_delete is not None
    assert post_delete[0].name == "admin-resource-delete"
    assert post_delete[0].public is False


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
    # L'en-tête porte un lien de tri depuis ADMIN-LIST-FILTERS-001 : c'est le
    # nom de colonne qui compte, pas la forme exacte de la cellule.
    assert "<th>" in html and "title" in html
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


def test_detail_template_affiche_les_champs(tmp_path: Path):
    views = tmp_path / "views"
    views.mkdir()
    renderer = Jinja2Renderer(str(views))
    html = renderer.render(
        "admin/detail.html",
        {
            "resource": _resource(),
            "columns": ("id", "title"),
            "row": {"id": 5, "title": "Bonjour"},
        },
    )
    assert "<dt>title</dt>" in html
    assert "Bonjour" in html
    # liens vers l'édition et la suppression (clé primaire = id)
    assert "/admin/articles/5/edit" in html
    assert "/admin/articles/5/delete" in html


def test_delete_template_confirmation(tmp_path: Path):
    views = tmp_path / "views"
    views.mkdir()
    renderer = Jinja2Renderer(str(views))
    html = renderer.render(
        "admin/delete.html",
        {
            "resource": _resource(),
            "columns": ("id", "title"),
            "row": {"id": 5, "title": "Bonjour"},
            "action": "/admin/articles/5/delete",
            "csrf_token": "tok123",
        },
    )
    assert "irréversible" in html
    assert 'method="post"' in html
    assert 'action="/admin/articles/5/delete"' in html
    assert "tok123" in html


def test_form_template_affiche_les_champs_et_csrf(tmp_path: Path):
    views = tmp_path / "views"
    views.mkdir()
    renderer = Jinja2Renderer(str(views))
    html = renderer.render(
        "admin/form.html",
        {
            "resource": _resource(),
            "fields": ("title", "body"),
            "action": "/admin/articles/new",
            "values": {"title": "", "body": ""},
            "error": "",
            "title": "Nouveau : Article",
            "csrf_token": "tok123",
        },
    )
    assert 'name="title"' in html and 'name="body"' in html
    assert 'name="csrf_token"' in html and "tok123" in html
    assert 'method="post"' in html
