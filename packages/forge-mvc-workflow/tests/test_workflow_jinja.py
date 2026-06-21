from __future__ import annotations

from markupsafe import Markup

import pytest
pytest.importorskip("forge_mvc_workflow")

from forge_mvc_workflow import (
    make_status,
    make_workflow_jinja_helpers,
    workflow_status_badge,
    workflow_status_badge_class,
    workflow_status_color,
    workflow_status_label,
)


# ---------------------------------------------------------------------------
# workflow_status_label
# ---------------------------------------------------------------------------


def test_label_retourne_label_du_statut():
    s = make_status("pending", label="En attente")
    assert workflow_status_label(s) == "En attente"


def test_label_fallback_vers_name_si_label_vide():
    s = make_status("draft")
    assert workflow_status_label(s) == "draft"


def test_label_accepte_chaine_brute():
    assert workflow_status_label("published") == "published"


def test_label_retourne_chaine_vide_pour_none():
    assert workflow_status_label(None) == ""


def test_label_statut_initial():
    s = make_status("new", label="Nouveau", is_initial=True)
    assert workflow_status_label(s) == "Nouveau"


def test_label_statut_final():
    s = make_status("archived", label="Archivé", is_final=True)
    assert workflow_status_label(s) == "Archivé"


# ---------------------------------------------------------------------------
# workflow_status_color
# ---------------------------------------------------------------------------


def test_color_retourne_couleur_definie():
    s = make_status("pending", color="yellow")
    assert workflow_status_color(s) == "yellow"


def test_color_fallback_gray_si_couleur_vide():
    s = make_status("draft")
    assert workflow_status_color(s) == "gray"


def test_color_fallback_gray_pour_chaine_brute():
    assert workflow_status_color("unknown") == "gray"


def test_color_fallback_gray_pour_none():
    assert workflow_status_color(None) == "gray"


def test_color_toutes_couleurs_connues():
    for color in ("gray", "blue", "green", "yellow", "red", "purple"):
        s = make_status("s", color=color)
        assert workflow_status_color(s) == color


# ---------------------------------------------------------------------------
# workflow_status_badge_class
# ---------------------------------------------------------------------------


def test_badge_class_contient_classes_de_base():
    s = make_status("pending", color="yellow")
    css = workflow_status_badge_class(s)
    assert "inline-flex" in css
    assert "rounded-full" in css
    assert "text-xs" in css


def test_badge_class_couleur_yellow():
    s = make_status("pending", color="yellow")
    css = workflow_status_badge_class(s)
    assert "yellow" in css


def test_badge_class_couleur_green():
    s = make_status("published", color="green")
    css = workflow_status_badge_class(s)
    assert "green" in css


def test_badge_class_couleur_red():
    s = make_status("rejected", color="red")
    css = workflow_status_badge_class(s)
    assert "red" in css


def test_badge_class_couleur_inconnue_fallback_gray():
    s = make_status("custom", color="orange")
    css = workflow_status_badge_class(s)
    assert "gray" in css


def test_badge_class_sans_couleur_fallback_gray():
    s = make_status("draft")
    css = workflow_status_badge_class(s)
    assert "gray" in css


def test_badge_class_pour_none_retourne_gray():
    css = workflow_status_badge_class(None)
    assert "gray" in css


# ---------------------------------------------------------------------------
# workflow_status_badge
# ---------------------------------------------------------------------------


def test_badge_retourne_markup():
    s = make_status("pending", label="En attente", color="yellow")
    result = workflow_status_badge(s)
    assert isinstance(result, Markup)


def test_badge_contient_label():
    s = make_status("pending", label="En attente", color="yellow")
    result = str(workflow_status_badge(s))
    assert "En attente" in result


def test_badge_contient_balise_span():
    s = make_status("draft")
    result = str(workflow_status_badge(s))
    assert result.startswith("<span")
    assert result.endswith("</span>")


def test_badge_echappe_les_caracteres_speciaux():
    s = make_status("draft")
    object.__setattr__(s, "label", "<script>alert(1)</script>")
    result = str(workflow_status_badge(s))
    assert "<script>" not in result
    assert "&lt;script&gt;" in result


def test_badge_pour_none_est_markup_vide():
    result = workflow_status_badge(None)
    assert isinstance(result, Markup)
    assert "<span" in str(result)


# ---------------------------------------------------------------------------
# make_workflow_jinja_helpers
# ---------------------------------------------------------------------------


def test_make_workflow_jinja_helpers_retourne_dict():
    helpers = make_workflow_jinja_helpers()
    assert isinstance(helpers, dict)


def test_make_workflow_jinja_helpers_contient_label():
    assert "workflow_status_label" in make_workflow_jinja_helpers()


def test_make_workflow_jinja_helpers_contient_color():
    assert "workflow_status_color" in make_workflow_jinja_helpers()


def test_make_workflow_jinja_helpers_contient_badge_class():
    assert "workflow_status_badge_class" in make_workflow_jinja_helpers()


def test_make_workflow_jinja_helpers_contient_badge():
    assert "workflow_status_badge" in make_workflow_jinja_helpers()


def test_make_workflow_jinja_helpers_sont_appelables():
    for fn in make_workflow_jinja_helpers().values():
        assert callable(fn)


# ---------------------------------------------------------------------------
# Helpers n'exécutent aucune transition ni modification
# ---------------------------------------------------------------------------


def test_helpers_ne_modifient_pas_le_statut():
    s = make_status("draft", label="Brouillon", color="gray")
    workflow_status_label(s)
    workflow_status_color(s)
    workflow_status_badge_class(s)
    workflow_status_badge(s)
    assert s.name == "draft"
    assert s.label == "Brouillon"
    assert s.color == "gray"


def test_helpers_sans_acces_base_de_donnees():
    s = make_status("pending", color="blue")
    assert workflow_status_label(s) == "pending"
    assert workflow_status_color(s) == "blue"


# ---------------------------------------------------------------------------
# API importable depuis core.workflow
# ---------------------------------------------------------------------------


def test_api_jinja_importable():
    from forge_mvc_workflow import (
        make_workflow_jinja_helpers,
        workflow_status_badge,
        workflow_status_badge_class,
        workflow_status_color,
        workflow_status_label,
    )
    assert callable(workflow_status_label)
    assert callable(workflow_status_color)
    assert callable(workflow_status_badge_class)
    assert callable(workflow_status_badge)
    assert callable(make_workflow_jinja_helpers)


# ---------------------------------------------------------------------------
# Injection dans Jinja2Renderer
# ---------------------------------------------------------------------------


def test_renderer_expose_helpers_workflow():
    from integrations.jinja2.renderer import Jinja2Renderer
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        renderer = Jinja2Renderer(tmpdir)
        assert "workflow_status_label" in renderer._env.globals
        assert "workflow_status_color" in renderer._env.globals
        assert "workflow_status_badge_class" in renderer._env.globals
        assert "workflow_status_badge" in renderer._env.globals


def test_renderer_helpers_sont_appelables_depuis_globals():
    from integrations.jinja2.renderer import Jinja2Renderer
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        renderer = Jinja2Renderer(tmpdir)
        fn = renderer._env.globals["workflow_status_label"]
        s = make_status("draft")
        assert fn(s) == "draft"
