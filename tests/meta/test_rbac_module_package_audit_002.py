"""Tests meta — RBAC-MODULE-002 : audit et verrouillage du package RBAC existant.

Vérifie que le rapport d'audit est présent et cohérent :
- il existe ;
- il mentionne packages/forge-mvc-rbac et forge_mvc_rbac ;
- il mentionne has_permission, require_permission, PermissionDenied ;
- il mentionne les erreurs 403 ;
- il dit que make:crud core reste neutre ;
- il dit que mvc/security/rbac.json n'est pas encore chargé ;
- il propose RBAC-MODULE-003 ;
- il ne dit pas que PyPI a été publié dans ce ticket ;
- il ne dit pas que le runtime est déjà branché.
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


# ── Références au package ──────────────────────────────────────────────────────


def test_rapport_mentionne_packages_forge_mvc_rbac():
    assert "packages/forge-mvc-rbac" in _text()


def test_rapport_mentionne_forge_mvc_rbac():
    assert "forge_mvc_rbac" in _text()


# ── API RBAC ───────────────────────────────────────────────────────────────────


def test_rapport_mentionne_has_permission():
    assert "has_permission" in _text()


def test_rapport_mentionne_require_permission():
    assert "require_permission" in _text()


def test_rapport_mentionne_permission_denied():
    assert "PermissionDenied" in _text()


def test_rapport_mentionne_erreur_403():
    assert "403" in _text()


# ── Neutralité du core ────────────────────────────────────────────────────────


def test_rapport_dit_make_crud_reste_neutre():
    text = _text()
    assert "make:crud" in text
    assert "neutre" in text.lower() or "reste neutre" in text.lower()


# ── Chaînon manquant ──────────────────────────────────────────────────────────


def test_rapport_dit_rbac_json_non_charge():
    text = _text()
    assert "mvc/security/rbac.json" in text
    assert (
        "non chargé" in text
        or "ne charge pas" in text.lower()
        or "n'est pas encore chargé" in text.lower()
        or "ne lit pas" in text.lower()
    )


# ── Ticket suivant ────────────────────────────────────────────────────────────


def test_rapport_propose_rbac_module_003():
    assert "RBAC-MODULE-003" in _text()


# ── Garde-fous négatifs ───────────────────────────────────────────────────────


def test_rapport_ne_dit_pas_publie_sur_pypi():
    text = _text()
    assert "publié sur PyPI" not in text
    assert "pypi publish" not in text.lower()


def test_rapport_ne_dit_pas_runtime_branché():
    text = _text()
    assert "runtime branché" not in text or "non branché" in text.lower() or "non branché" in text
