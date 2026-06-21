"""Tests meta — RBAC-CONTRACT-CLOSE-001 : clôture du bloc contrat RBAC séparé.

Vérifie que la documentation de clôture est présente et cohérente :
- la documentation RBAC documente les tickets livrés ;
- elle confirme la séparation RBAC / entity.schema.json ;
- elle confirme que make:crud ne consomme pas rbac.json ;
- elle confirme qu'aucun guard n'est généré depuis le contrat séparé ;
- elle confirme que le runtime RBAC n'est pas branché ;
- aucune publication PyPI n'a été effectuée.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

DOC = Path("packages/forge-mvc-rbac/docs/contract.md")


def _text() -> str:
    return DOC.read_text(encoding="utf-8")


# ── Existence ──────────────────────────────────────────────────────────────────


def test_doc_rbac_contract_existe():
    assert DOC.exists()


# ── Tickets livrés mentionnés ─────────────────────────────────────────────────


def test_doc_mentionne_rbac_contract_001():
    assert "RBAC-CONTRACT-001" in _text()


def test_doc_mentionne_rbac_contract_002():
    assert "RBAC-CONTRACT-002" in _text()


def test_doc_mentionne_rbac_contract_003():
    assert "RBAC-CONTRACT-003" in _text()


# ── Emplacement et schéma ─────────────────────────────────────────────────────


def test_doc_mentionne_emplacement_rbac_json():
    assert "mvc/security/rbac.json" in _text()


def test_doc_mentionne_rbac_schema_json():
    assert "rbac.schema.json" in _text()


def test_doc_mentionne_rbac_validate():
    assert "rbac:validate" in _text()


# ── Séparations et décisions ──────────────────────────────────────────────────


def test_doc_dit_rbac_hors_entity_schema():
    text = _text()
    assert "entity.schema.json" in text
    assert "rbac" in text.lower()
    # La doc doit affirmer que rbac est absent du schéma d'entité
    assert "pas" in text.lower() or "hors" in text.lower() or "sépar" in text.lower()


def test_doc_dit_make_crud_ne_consomme_pas_rbac_json():
    text = _text()
    assert "make:crud" in text
    assert "mvc/security/rbac.json" in text
    # Formulation attendue : make:crud ne lit pas / ne consomme pas
    assert "ne consomme pas" in text or "ne lit pas" in text


def test_doc_dit_aucun_guard_rbac_genere():
    text = _text()
    assert "guard" in text.lower()
    assert "aucun" in text.lower()


def test_doc_dit_runtime_rbac_hors_perimetre():
    text = _text()
    assert "runtime" in text.lower()
    assert "hors" in text.lower() or "pas" in text.lower()


# ── Clôture ───────────────────────────────────────────────────────────────────


def test_doc_contient_section_cloture():
    assert "Clôture" in _text() or "cloture" in _text().lower()


def test_doc_statut_termine():
    text = _text()
    assert "terminé" in text.lower() or "terminé" in text


# ── Absence de publication ─────────────────────────────────────────────────────


def test_doc_ne_dit_pas_pypi_publie():
    text = _text()
    assert "PyPI publié" not in text
    assert "publié sur PyPI" not in text
    assert "forge-mvc publié" not in text
