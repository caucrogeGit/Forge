"""
Garde-fous documentaires pour FIELD-FIX-001.
Vérifie que la documentation canonique des entités est cohérente avec le schéma.
"""

import pytest
from pathlib import Path

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_DOC = PROJECT_ROOT / "docs/entities/json-canonique.md"
FIELD_TEST_REPORT = PROJECT_ROOT / "docs/history/field-tests/field-test-app-001.md"


# --- existence ---

def test_canonical_doc_exists():
    assert CANONICAL_DOC.exists(), f"Doc introuvable : {CANONICAL_DOC}"


def test_field_test_report_exists():
    assert FIELD_TEST_REPORT.exists()


# --- clé racine "name" ---

def test_canonical_doc_mentions_schema_version():
    assert 'schema_version' in CANONICAL_DOC.read_text()


def test_canonical_doc_mentions_name_key():
    assert '"name"' in CANONICAL_DOC.read_text()


def test_canonical_doc_mentions_name_as_entity_key():
    content = CANONICAL_DOC.read_text()
    # La doc doit montrer "name" comme clé de l'entité (PascalCase), pas "entity"
    assert '"name": "Article"' in content or '"name": "Contact"' in content


# --- structure mvc/entities ---

def test_canonical_doc_mentions_entity_subdirectory():
    content = CANONICAL_DOC.read_text()
    assert 'mvc/entities/article/article.json' in content


def test_canonical_doc_mentions_relations_json_location():
    content = CANONICAL_DOC.read_text()
    assert 'mvc/entities/relations.json' in content


def test_canonical_doc_explains_relations_json_at_root():
    content = CANONICAL_DOC.read_text()
    # relations.json est à la racine de mvc/entities/, pas dans un sous-dossier
    assert 'relations.json' in content
    assert 'racine' in content or 'root' in content.lower() or 'entities/' in content


def test_canonical_doc_mentions_build_model():
    assert 'build:model' in CANONICAL_DOC.read_text()


def test_canonical_doc_mentions_entity_validate():
    assert 'entity:validate' in CANONICAL_DOC.read_text()


def test_canonical_doc_explains_subdirectory_structure():
    content = CANONICAL_DOC.read_text()
    # Doit expliquer que chaque entité vit dans son sous-dossier
    assert 'sous-dossier' in content or 'sous-dossiers' in content


def test_canonical_doc_explains_lowercase_directory():
    content = CANONICAL_DOC.read_text()
    # Les noms de dossiers doivent être en minuscule
    assert 'minuscule' in content or 'snake_case' in content


def test_canonical_doc_mentions_double_underscore_prefix():
    content = CANONICAL_DOC.read_text()
    # Convention __ pour les dossiers non-entités
    assert '__' in content


# --- build:model comportement ---

def test_canonical_doc_explains_build_model_scans_subdirs():
    content = CANONICAL_DOC.read_text()
    assert 'build:model' in content
    assert 'sous-dossier' in content or 'sous-dossiers' in content


def test_canonical_doc_warns_root_json_not_recognized():
    content = CANONICAL_DOC.read_text()
    # Doit prévenir qu'un JSON à la racine de mvc/entities/ n'est pas reconnu
    assert 'pas' in content and ('reconnu' in content or 'reconnu' in content)


# --- rapport terrain ---

def test_field_test_report_mentions_field_fix_001():
    assert 'FIELD-FIX-001' in FIELD_TEST_REPORT.read_text()


def test_field_test_report_f001_treated():
    content = FIELD_TEST_REPORT.read_text()
    assert 'F-001' in content
    assert 'FIELD-FIX-001' in content


def test_field_test_report_f002_treated():
    content = FIELD_TEST_REPORT.read_text()
    assert 'F-002' in content
    assert 'FIELD-FIX-001' in content


def test_field_test_report_f003_open():
    content = FIELD_TEST_REPORT.read_text()
    assert 'F-003' in content
    # F-003 reste ouvert — doit mentionner FIELD-AUDIT-M2M-GUARD-001
    assert 'FIELD-AUDIT-M2M-GUARD-001' in content


# --- absence de publication ---

def test_canonical_doc_no_pypi_mention():
    content = CANONICAL_DOC.read_text()
    assert 'PyPI' not in content
    assert 'pypi' not in content.lower()


def test_canonical_doc_no_tag_creation_mention():
    content = CANONICAL_DOC.read_text()
    assert 'git tag' not in content
