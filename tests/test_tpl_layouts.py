"""Contrat des layouts TPL-001 : public.html et admin.html."""

from __future__ import annotations

from pathlib import Path


PUBLIC = Path("mvc/views/layouts/public.html")
ADMIN = Path("mvc/views/layouts/admin.html")
BASE = Path("mvc/views/layouts/base.html")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# --- Existence ---


def test_public_layout_existe():
    assert PUBLIC.is_file()


def test_admin_layout_existe():
    assert ADMIN.is_file()


def test_base_layout_conserve():
    assert BASE.is_file()


# --- Block title ---


def test_public_layout_a_block_title():
    assert "{% block title %}" in _read(PUBLIC)


def test_admin_layout_a_block_title():
    assert "{% block title %}" in _read(ADMIN)


# --- Navigation ---


def test_public_layout_sans_navigation():
    assert "<nav" not in _read(PUBLIC)


def test_admin_layout_avec_navigation():
    assert "<nav" in _read(ADMIN)


def test_admin_layout_bouton_deconnexion():
    assert "Déconnexion" in _read(ADMIN)


def test_admin_layout_logout_form_action():
    assert 'action="/logout"' in _read(ADMIN)


# --- Block content ---


def test_public_layout_a_block_content():
    assert "{% block content %}" in _read(PUBLIC)


def test_admin_layout_a_block_content():
    assert "{% block content %}" in _read(ADMIN)


# --- CSRF ---


def test_public_layout_sans_csrf():
    assert "csrf_token" not in _read(PUBLIC)


def test_admin_layout_avec_csrf():
    assert "csrf_token" in _read(ADMIN)


# --- Scripts standard ---


def test_public_layout_charge_app_js():
    assert '<script src="/static/js/app.js" defer></script>' in _read(PUBLIC)


def test_admin_layout_charge_app_js():
    assert '<script src="/static/js/app.js" defer></script>' in _read(ADMIN)


def test_public_layout_expose_scripts_block():
    assert "{% block scripts %}{% endblock %}" in _read(PUBLIC)


def test_admin_layout_expose_scripts_block():
    assert "{% block scripts %}{% endblock %}" in _read(ADMIN)


# --- Tailwind ---


def test_public_layout_charge_tailwind():
    assert '<link rel="stylesheet" href="/static/tailwind.css">' in _read(PUBLIC)


def test_admin_layout_charge_tailwind():
    assert '<link rel="stylesheet" href="/static/tailwind.css">' in _read(ADMIN)
