"""Tests du helper Jinja can(...) — AUTH-RBAC-003."""

from __future__ import annotations


from integrations.jinja2.renderer import Jinja2Renderer
import pytest
pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac import make_can
from tests.fake_request import FakeRequest


# ---------------------------------------------------------------------------
# make_can — callable lié à la request
# ---------------------------------------------------------------------------


def test_make_can_retourne_callable():
    req = FakeRequest()
    assert callable(make_can(req))


def test_make_can_true_si_permission_presente():
    req = FakeRequest()
    req.permissions = ["posts.edit"]
    assert make_can(req)("posts.edit") is True


def test_make_can_false_si_permission_absente():
    req = FakeRequest()
    req.permissions = ["posts.view"]
    assert make_can(req)("posts.edit") is False


def test_make_can_false_sans_permissions():
    req = FakeRequest()
    assert make_can(req)("posts.edit") is False


def test_make_can_normalise_code():
    req = FakeRequest()
    req.permissions = ["posts.edit"]
    assert make_can(req)("POSTS.EDIT") is True


def test_make_can_code_vide_retourne_false():
    req = FakeRequest()
    assert make_can(req)("") is False


def test_make_can_code_sans_point_retourne_false():
    req = FakeRequest()
    assert make_can(req)("postsedit") is False


def test_make_can_reutilise_has_permission():
    import inspect
    import forge_mvc_rbac.rbac as rbac_module
    src = inspect.getsource(rbac_module.make_can)
    assert "has_permission" in src


# ---------------------------------------------------------------------------
# Jinja2Renderer — global can disponible par défaut
# ---------------------------------------------------------------------------


def test_jinja_env_expose_can(tmp_path):
    r = Jinja2Renderer(str(tmp_path))
    assert "can" in r._env.globals


def test_can_global_retourne_false_par_defaut(tmp_path):
    r = Jinja2Renderer(str(tmp_path))
    assert r._env.globals["can"]("posts.edit") is False


def test_template_can_non_plante_sans_contexte(tmp_path):
    (tmp_path / "t.html").write_text('{% if can("posts.edit") %}oui{% else %}non{% endif %}')
    r = Jinja2Renderer(str(tmp_path))
    assert r.render("t.html", {}) == "non"


# ---------------------------------------------------------------------------
# Rendu Jinja avec can lié à la request
# ---------------------------------------------------------------------------


def test_template_can_true_avec_permission(tmp_path):
    (tmp_path / "t.html").write_text('{% if can("posts.edit") %}oui{% else %}non{% endif %}')
    req = FakeRequest()
    req.permissions = ["posts.edit"]
    r = Jinja2Renderer(str(tmp_path))
    assert r.render("t.html", {"can": make_can(req)}) == "oui"


def test_template_can_false_sans_permission(tmp_path):
    (tmp_path / "t.html").write_text('{% if can("posts.edit") %}oui{% else %}non{% endif %}')
    req = FakeRequest()
    r = Jinja2Renderer(str(tmp_path))
    assert r.render("t.html", {"can": make_can(req)}) == "non"


def test_template_can_normalise_code(tmp_path):
    (tmp_path / "t.html").write_text('{% if can("POSTS.EDIT") %}oui{% else %}non{% endif %}')
    req = FakeRequest()
    req.permissions = ["posts.edit"]
    r = Jinja2Renderer(str(tmp_path))
    assert r.render("t.html", {"can": make_can(req)}) == "oui"


def test_template_can_code_vide_ne_plante_pas(tmp_path):
    (tmp_path / "t.html").write_text('{% if can("") %}oui{% else %}non{% endif %}')
    req = FakeRequest()
    r = Jinja2Renderer(str(tmp_path))
    assert r.render("t.html", {"can": make_can(req)}) == "non"


def test_template_can_sans_utilisateur_authentifie(tmp_path):
    (tmp_path / "t.html").write_text('{% if can("posts.edit") %}oui{% else %}non{% endif %}')
    r = Jinja2Renderer(str(tmp_path))
    assert r.render("t.html", {}) == "non"


def test_template_can_coexiste_avec_trans(tmp_path):
    (tmp_path / "t.html").write_text(
        '{{ trans("common.save") }}{% if can("x.y") %} ok{% endif %}'
    )
    req = FakeRequest()
    req.permissions = ["x.y"]
    r = Jinja2Renderer(str(tmp_path))
    assert r.render("t.html", {"can": make_can(req)}) == "Enregistrer ok"


def test_template_can_plusieurs_permissions(tmp_path):
    (tmp_path / "t.html").write_text(
        '{% if can("admin.view") %}A{% endif %}{% if can("posts.edit") %}B{% endif %}'
    )
    req = FakeRequest()
    req.permissions = ["admin.view"]
    r = Jinja2Renderer(str(tmp_path))
    assert r.render("t.html", {"can": make_can(req)}) == "A"


# ---------------------------------------------------------------------------
# BaseController.render() — injection automatique de can
# ---------------------------------------------------------------------------


def test_base_controller_injecte_can_avec_permission(tmp_path):
    import core.forge as forge
    from core.mvc.controller.base_controller import BaseController
    from core.templating.manager import template_manager

    r = Jinja2Renderer(str(tmp_path))
    template_manager.register(r)
    forge._cfg["views_dir"] = str(tmp_path)

    (tmp_path / "t.html").write_text('{% if can("posts.edit") %}oui{% else %}non{% endif %}')
    req = FakeRequest()
    req.permissions = ["posts.edit"]

    response = BaseController.render("t.html", context={}, request=req)
    assert b"oui" in response.body


def test_base_controller_can_false_sans_permission(tmp_path):
    import core.forge as forge
    from core.mvc.controller.base_controller import BaseController
    from core.templating.manager import template_manager

    r = Jinja2Renderer(str(tmp_path))
    template_manager.register(r)
    forge._cfg["views_dir"] = str(tmp_path)

    (tmp_path / "t.html").write_text('{% if can("posts.edit") %}oui{% else %}non{% endif %}')
    req = FakeRequest()

    response = BaseController.render("t.html", context={}, request=req)
    assert b"non" in response.body


# ---------------------------------------------------------------------------
# Pas de dépendance base de données ni modèle utilisateur
# ---------------------------------------------------------------------------


def test_can_sans_base_de_donnees():
    """make_can ne fait aucune requête SQL — uniquement la session en mémoire."""
    req = FakeRequest()
    req.permissions = ["dashboard.view"]
    can = make_can(req)
    assert can("dashboard.view") is True


def test_can_sans_modele_user():
    """make_can fonctionne avec un simple attribut permissions sur le request."""
    req = FakeRequest()
    req.permissions = ["reports.export"]
    assert make_can(req)("reports.export") is True


# ---------------------------------------------------------------------------
# Absence de dépendance métier
# ---------------------------------------------------------------------------


def test_make_can_sans_terme_metier():
    import inspect
    import forge_mvc_rbac.rbac as rbac_module
    src = inspect.getsource(rbac_module)
    for term in ("commune", "sejour", "hebergement", "reservation"):
        assert term not in src.lower(), f"Terme métier '{term}' détecté dans rbac.py"
