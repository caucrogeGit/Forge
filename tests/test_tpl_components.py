"""Contrat des composants Jinja TPL-002."""

from __future__ import annotations

from pathlib import Path

import pytest


COMPONENTS_DIR = Path("tests/fixtures/app/mvc/views/components")
COMPONENTS = [
    "button.html",
    "alert.html",
    "form_field.html",
    "table.html",
    "badge.html",
    "pagination.html",
]
FORBIDDEN_TERMS = (
    "commune",
    "sejour",
    "séjour",
    "hebergement",
    "hébergement",
    "reservation",
    "réservation",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# --- Existence ---


def test_components_directory_existe():
    assert COMPONENTS_DIR.is_dir()


@pytest.mark.parametrize("name", COMPONENTS)
def test_composant_existe(name):
    assert (COMPONENTS_DIR / name).is_file()


# --- HTML minimal ---


@pytest.mark.parametrize("name", COMPONENTS)
def test_composant_contient_html(name):
    content = _read(COMPONENTS_DIR / name)
    assert "<" in content and ">" in content


# --- Pas de terme métier ---


@pytest.mark.parametrize("name", COMPONENTS)
def test_composant_sans_terme_metier(name):
    content = _read(COMPONENTS_DIR / name).lower()
    for term in FORBIDDEN_TERMS:
        assert term not in content, f"{name} contient le terme métier '{term}'"


# --- Pas de scripts HTMX/Alpine chargés ---


@pytest.mark.parametrize("name", COMPONENTS)
def test_composant_sans_htmx(name):
    content = _read(COMPONENTS_DIR / name)
    assert "htmx.min.js" not in content
    assert "htmx.org" not in content


@pytest.mark.parametrize("name", COMPONENTS)
def test_composant_sans_alpine(name):
    content = _read(COMPONENTS_DIR / name)
    assert "alpine.min.js" not in content
    assert "alpinejs" not in content


# --- Layouts non modifiés ---


def test_composants_ne_referencent_pas_les_layouts():
    for layout in ["base.html", "public.html", "admin.html"]:
        content = _read(Path("tests/fixtures/app/mvc/views/layouts") / layout)
        assert "components/" not in content


# --- make:crud : seul button.html est référencé (TPL-003) ---


def test_make_crud_utilise_la_macro_button_de_ui():
    # FORGE-11 : le bouton est la macro `button` de components/ui.html,
    # pas un fichier components/button.html (qui n'existe pas dans le squelette).
    src = _read(Path("cli/entities/crud/views_builder.py"))
    assert 'from "components/ui.html" import button' in src


def test_make_crud_ne_reference_pas_autres_composants():
    src = _read(Path("cli/entities/crud/views_builder.py"))
    for name in ("alert.html", "form_field.html", "table.html", "badge.html", "pagination.html", "button.html"):
        assert f"components/{name}" not in src


# --- Starters non modifiés ---


def test_starters_ne_referencent_pas_components():
    starters_dir = Path("cli/starters/data")
    for f in starters_dir.rglob("*.html"):
        content = f.read_text(encoding="utf-8")
        assert "components/" not in content, f"{f} référence components/"
