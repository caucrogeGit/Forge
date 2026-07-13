"""Contrat de documentation des composants Jinja — TPL-007."""

from __future__ import annotations

from pathlib import Path
import pytest

pytestmark = pytest.mark.meta

FRONT_MD = Path("docs/features/front.md")


def _doc() -> str:
    return FRONT_MD.read_text(encoding="utf-8")


# --- Fichier de doc présent ---


def test_front_md_existe():
    assert FRONT_MD.is_file()


# --- Fichiers de macros référencés dans la doc (macros groupées) ---


def test_doc_mentionne_ui_html():
    # ui.html porte button, alert, badge, flash_messages.
    doc = _doc()
    assert "components/ui.html" in doc
    assert "button" in doc
    assert "alert" in doc
    assert "badge" in doc
    assert "flash_messages" in doc


def test_doc_mentionne_forms_html():
    # forms.html porte field, select_field, checkbox, textarea_field.
    doc = _doc()
    assert "components/forms.html" in doc
    assert "field" in doc


def test_doc_mentionne_data_html():
    # data.html porte table et pagination.
    doc = _doc()
    assert "components/data.html" in doc
    assert "table" in doc
    assert "pagination" in doc.lower()


def test_doc_macros_importees_pas_incluses():
    # Les macros s'importent ({% from %}) et s'appellent, on n'inclut plus de
    # fichier par composant.
    doc = _doc()
    assert '{% from "components/ui.html" import' in doc


# --- Variants du bouton ---


def test_doc_mentionne_variant_primary():
    assert "primary" in _doc()


def test_doc_mentionne_variant_secondary():
    assert "secondary" in _doc()


def test_doc_mentionne_variant_danger():
    assert "danger" in _doc()


# --- Variants alert.html ---


def test_doc_mentionne_variant_info():
    assert "info" in _doc()


def test_doc_mentionne_variant_success():
    assert "success" in _doc()


def test_doc_mentionne_variant_warning():
    assert "warning" in _doc()


def test_doc_mentionne_variant_error():
    assert "error" in _doc()


# --- Liens avec les fonctionnalités Forge ---


def test_doc_mentionne_make_crud():
    assert "make:crud" in _doc()


def test_doc_mentionne_messages_flash():
    assert "flash" in _doc()


def test_doc_mentionne_etats_vides():
    assert "vide" in _doc()


# --- Mentions HTMX et Alpine ---


def test_doc_mentionne_htmx():
    doc = _doc()
    assert "HTMX" in doc or "htmx" in doc


def test_doc_mentionne_alpine():
    doc = _doc()
    assert "Alpine" in doc or "alpine" in doc


# --- Règles composants ---


def test_doc_composants_pas_logique_metier():
    assert "logique métier" in _doc()


def test_doc_composants_pas_mini_framework():
    assert "mini-framework" in _doc()


# --- Section Règles Forge présente ---


def test_doc_section_regles_forge():
    assert "Règles Forge pour les composants" in _doc()


# --- Section Limites actuelles présente ---


def test_doc_section_limites_actuelles():
    assert "Limites actuelles" in _doc()


# --- Usage des macros dans les templates CRUD ---


def test_doc_crud_utilise_macro_field():
    # make:crud branche désormais les champs sur la macro field (plus d'inline).
    doc = _doc()
    assert "field" in doc
    assert "make:crud" in doc


def test_doc_mentionne_pagination():
    doc = _doc()
    assert "pagination" in doc.lower()
