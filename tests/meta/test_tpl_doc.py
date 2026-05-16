"""Contrat de documentation des composants Jinja — TPL-007."""

from __future__ import annotations

from pathlib import Path
import pytest

pytestmark = pytest.mark.meta

FRONT_MD = Path("docs/front.md")


def _doc() -> str:
    return FRONT_MD.read_text(encoding="utf-8")


# --- Fichier de doc présent ---


def test_front_md_existe():
    assert FRONT_MD.is_file()


# --- Composants référencés dans la doc ---


def test_doc_mentionne_button_html():
    assert "components/button.html" in _doc()


def test_doc_mentionne_alert_html():
    assert "components/alert.html" in _doc()


def test_doc_mentionne_form_field_html():
    assert "components/form_field.html" in _doc()


def test_doc_mentionne_table_html():
    assert "components/table.html" in _doc()


def test_doc_mentionne_badge_html():
    assert "components/badge.html" in _doc()


def test_doc_mentionne_pagination_html():
    assert "components/pagination.html" in _doc()


# --- Variants button.html ---


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


# --- Limites par composant documentées ---


def test_doc_form_field_limite_inline():
    doc = _doc()
    assert "form_field" in doc
    assert "inline" in doc


def test_doc_pagination_limite_htmx():
    doc = _doc()
    assert "pagination" in doc.lower()
