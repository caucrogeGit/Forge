"""Tests meta — RBAC-CONTRACT-002 : documentation du contrat RBAC séparé.

Vérifie que la page de documentation RBAC est présente et cohérente avec la
décision de séparation entre schéma d'entité et contrat RBAC.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

DOC = Path("docs/security/rbac-contract.md")


def _text() -> str:
    return DOC.read_text(encoding="utf-8")


# ── Existence ──────────────────────────────────────────────────────────────────


def test_doc_rbac_contract_existe():
    assert DOC.exists()


# ── Contenu ───────────────────────────────────────────────────────────────────


def test_doc_mentionne_emplacement():
    assert "mvc/security/rbac.json" in _text()


def test_doc_mentionne_roles():
    text = _text()
    assert "roles" in text.lower()


def test_doc_mentionne_permissions():
    assert "permissions" in _text().lower()


def test_doc_mentionne_schema_version():
    assert 'schema_version' in _text() and '"1.0"' in _text()


def test_doc_dit_rbac_separe_de_entity_schema():
    text = _text()
    assert "entity.schema.json" in text
    assert "séparé" in text.lower() or "séparément" in text.lower() or "séparation" in text.lower()


def test_doc_dit_runtime_non_branche():
    text = _text()
    assert "pas encore branché" in text or "non branché" in text or "pas encore" in text
