"""Tests meta — RBAC-MODULE-007 : documentation usage applicatif RBAC.

Vérifie que la documentation RBAC opt-in est complète et ne contient pas
d'affirmations erronées (PyPI publié, routes automatiquement protégées, etc.).
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


_USAGE_DOC = Path(__file__).parents[2] / "docs" / "security" / "rbac-usage.md"
_CONTRACT_DOC = Path(__file__).parents[2] / "docs" / "security" / "rbac-contract.md"
_AUDIT_DOC = (
    Path(__file__).parents[2]
    / "docs" / "history" / "audits" / "rbac-module-package-audit-002.md"
)
_MKDOCS = Path(__file__).parents[2] / "mkdocs.yml"


def _usage() -> str:
    return _USAGE_DOC.read_text(encoding="utf-8")


def _contract() -> str:
    return _CONTRACT_DOC.read_text(encoding="utf-8")


def _audit() -> str:
    return _AUDIT_DOC.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Page usage existe et est dans mkdocs.yml
# ---------------------------------------------------------------------------


def test_usage_doc_exists():
    assert _USAGE_DOC.exists(), f"Page manquante : {_USAGE_DOC}"


def test_usage_doc_in_mkdocs():
    mkdocs = _MKDOCS.read_text(encoding="utf-8")
    assert "security/rbac-usage.md" in mkdocs


# ---------------------------------------------------------------------------
# Contenu minimal — références clés
# ---------------------------------------------------------------------------


def test_usage_mentions_rbac_contract_path():
    assert "mvc/security/rbac.json" in _usage()


def test_usage_mentions_rbac_validate():
    assert "rbac:validate" in _usage()


def test_usage_mentions_rbac_audit():
    assert "rbac:audit" in _usage()


def test_usage_mentions_load_rbac_contract():
    assert "load_rbac_contract" in _usage()


def test_usage_mentions_has_contract_permission():
    assert "has_contract_permission" in _usage()


def test_usage_mentions_require_contract_permission():
    assert "require_contract_permission" in _usage()


def test_usage_mentions_require_contract_permission_for_request():
    assert "require_contract_permission_for_request" in _usage()


def test_usage_mentions_contract_permission_required():
    assert "contract_permission_required" in _usage()


# ---------------------------------------------------------------------------
# Exemple de contrat JSON présent
# ---------------------------------------------------------------------------


def test_usage_contains_rbac_json_example():
    text = _usage()
    assert '"schema_version"' in text
    assert '"roles"' in text


# ---------------------------------------------------------------------------
# Limites documentées correctement
# ---------------------------------------------------------------------------


def test_usage_says_make_crud_no_guards():
    text = _usage()
    assert "make:crud" in text
    assert "ne génère pas" in text


def test_usage_says_rbac_is_opt_in():
    text = _usage()
    assert "opt-in" in text


def test_usage_says_routes_not_auto_protected():
    text = _usage()
    assert "pas protégées automatiquement" in text or "not protected automatically" in text.lower()


def test_usage_mentions_403():
    text = _usage()
    assert "Response(403)" in text or "403" in text


def test_usage_says_rbac_audit_read_only():
    text = _usage()
    assert "lecture seule" in text or "read-only" in text.lower()


# ---------------------------------------------------------------------------
# Audit package mentionne RBAC-MODULE-007
# ---------------------------------------------------------------------------


def test_audit_doc_mentions_rbac_module_007():
    assert "RBAC-MODULE-007" in _audit()


# ---------------------------------------------------------------------------
# Pas de mention de publication PyPI dans la doc usage
# ---------------------------------------------------------------------------


def test_usage_does_not_claim_pypi_published():
    text = _usage()
    assert "publié sur PyPI" not in text
    assert "released on PyPI" not in text.lower()
