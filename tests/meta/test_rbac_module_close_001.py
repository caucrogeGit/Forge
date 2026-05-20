"""Tests meta — RBAC-MODULE-CLOSE-001 : clôture du bloc RBAC module opt-in.

Vérifie que le rapport de clôture est présent, cohérent et reflète
l'état final du bloc RBAC applicatif opt-in.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

RAPPORT = Path("docs/history/audits/rbac-module-package-audit-002.md")


def _text() -> str:
    return RAPPORT.read_text(encoding="utf-8")


# ── Existence ──────────────────────────────────────────────────────────────────


def test_rapport_existe():
    assert RAPPORT.exists()


# ── Ticket de clôture ─────────────────────────────────────────────────────────


def test_rapport_mentionne_close_001():
    assert "RBAC-MODULE-CLOSE-001" in _text()


# ── Tickets du bloc ───────────────────────────────────────────────────────────


def test_rapport_mentionne_module_001():
    assert "RBAC-MODULE-001" in _text()


def test_rapport_mentionne_module_002():
    assert "RBAC-MODULE-002" in _text()


def test_rapport_mentionne_module_003():
    assert "RBAC-MODULE-003" in _text()


def test_rapport_mentionne_module_004():
    assert "RBAC-MODULE-004" in _text()


def test_rapport_mentionne_module_005():
    assert "RBAC-MODULE-005" in _text()


def test_rapport_mentionne_module_006():
    assert "RBAC-MODULE-006" in _text()


def test_rapport_mentionne_module_007():
    assert "RBAC-MODULE-007" in _text()


# ── Éléments clés ─────────────────────────────────────────────────────────────


def test_rapport_mentionne_mvc_security_rbac_json():
    assert "mvc/security/rbac.json" in _text()


def test_rapport_mentionne_rbac_validate():
    assert "rbac:validate" in _text()


def test_rapport_mentionne_rbac_audit():
    assert "rbac:audit" in _text()


# ── API publique exportée ─────────────────────────────────────────────────────


def test_rapport_mentionne_load_rbac_contract():
    assert "load_rbac_contract" in _text()


def test_rapport_mentionne_has_contract_permission():
    assert "has_contract_permission" in _text()


def test_rapport_mentionne_require_contract_permission_for_request():
    assert "require_contract_permission_for_request" in _text()


def test_rapport_mentionne_contract_permission_required():
    assert "contract_permission_required" in _text()


# ── Neutralité de make:crud ───────────────────────────────────────────────────


def test_rapport_dit_make_crud_neutre():
    text = _text()
    assert "make:crud" in text
    assert "neutre" in text.lower() or "ne lit pas" in text.lower()


# ── Routes non protégées automatiquement ─────────────────────────────────────


def test_rapport_dit_routes_non_protegees_automatiquement():
    text = _text()
    assert "opt-in" in text.lower() or "NON" in text


# ── Absence de publication ────────────────────────────────────────────────────


def test_rapport_ne_dit_pas_pypi_publie():
    text = _text()
    assert "PyPI publié" not in text
    assert "publié sur PyPI" not in text


def test_rapport_ne_dit_pas_tag_cree():
    text = _text()
    assert "tag créé" not in text.lower() or "NON" in text
