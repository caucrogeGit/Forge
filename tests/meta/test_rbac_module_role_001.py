"""Tests meta — RBAC-MODULE-001 : décision sur le rôle du module RBAC opt-in.

Vérifie que le rapport de décision est présent et cohérent :
- il existe ;
- il référence le ticket RBAC-MODULE-001 ;
- il mentionne mvc/security/rbac.json ;
- il mentionne rbac:validate ;
- il mentionne has_permission et require_permission ;
- il mentionne les erreurs 403 ;
- il confirme que make:crud core reste neutre ;
- il confirme que entity.schema.json n'est pas modifié ;
- il mentionne module opt-in ;
- il propose RBAC-MODULE-002 et RBAC-MODULE-CLOSE-001 ;
- il ne prétend pas que le module est déjà implémenté (runtime branché) ;
- il ne mentionne pas de publication PyPI.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

RAPPORT = Path("docs/history/audits/rbac-module-role-decision-001.md")


def _text() -> str:
    return RAPPORT.read_text(encoding="utf-8")


# ── Existence ──────────────────────────────────────────────────────────────────


def test_rapport_existe():
    assert RAPPORT.exists()


# ── Références ticket et contrat ──────────────────────────────────────────────


def test_rapport_mentionne_ticket_rbac_module_001():
    assert "RBAC-MODULE-001" in _text()


def test_rapport_mentionne_rbac_json():
    assert "mvc/security/rbac.json" in _text()


def test_rapport_mentionne_rbac_validate():
    assert "rbac:validate" in _text()


# ── Services du module ────────────────────────────────────────────────────────


def test_rapport_mentionne_has_permission():
    assert "has_permission" in _text()


def test_rapport_mentionne_require_permission():
    assert "require_permission" in _text()


def test_rapport_mentionne_erreur_403():
    text = _text()
    assert "403" in text or "PermissionDenied" in text


# ── Neutralité du core ────────────────────────────────────────────────────────


def test_rapport_dit_make_crud_reste_neutre():
    text = _text()
    assert "make:crud" in text
    assert "neutre" in text.lower() or "reste neutre" in text.lower() or "ne génère pas" in text.lower()


def test_rapport_dit_entity_schema_non_modifie():
    text = _text()
    assert "entity.schema.json" in text
    assert "non modifié" in text.lower() or "n'est pas modifié" in text.lower() or "pas de propriété" in text.lower() or "Non modifié" in text


# ── Module opt-in ─────────────────────────────────────────────────────────────


def test_rapport_mentionne_module_optin():
    text = _text()
    assert "opt-in" in text or "opt_in" in text


# ── Tickets futurs ────────────────────────────────────────────────────────────


def test_rapport_propose_rbac_module_002():
    assert "RBAC-MODULE-002" in _text()


def test_rapport_propose_rbac_module_close_001():
    assert "RBAC-MODULE-CLOSE-001" in _text()


# ── Garde-fous négatifs ───────────────────────────────────────────────────────


def test_rapport_ne_dit_pas_module_deja_implemente():
    text = _text()
    assert "runtime branché maintenant" not in text or "NON" in text
    assert "implémenté dans ce ticket" not in text
    assert "module créé dans ce ticket" not in text


def test_rapport_ne_mentionne_pas_publication_pypi():
    text = _text()
    assert "publié sur PyPI" not in text
    assert "pypi publish" not in text.lower()
    assert "pip publish" not in text.lower()
