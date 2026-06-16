"""Garde-fou META-TESTS-ROOT-MIGRATION-001.

Vérifie que les tests méta les plus évidents ne régressent pas vers tests/
après avoir été déplacés dans tests/meta/.

Règles vérifiées :
- Aucun fichier tests/*.py ne commence par test_doc_ (garde-fous documentaires).
- Aucun fichier tests/*.py ne commence par test_roadmap_ (garde-fous roadmap).
- Aucun fichier tests/*.py ne commence par test_changelog_ (garde-fous changelog).
- Aucun fichier tests/*.py ne commence par test_adr_ (garde-fous ADR).
- Aucun fichier tests/*.py ne commence par test_lts_policy (politiques de documentation).
- Aucun fichier tests/*.py ne commence par test_license_metadata (métadonnées paquet).
- Aucun fichier tests/*.py ne commence par test_migration_guide (guides de migration).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

TESTS_ROOT = Path(__file__).resolve().parents[1]


def _root_test_files() -> list[str]:
    return [f.name for f in TESTS_ROOT.glob("test_*.py")]


class TestNoMetaFilesAtRoot:
    """Les préfixes évidents de tests méta ne doivent plus être à la racine de tests/."""

    def test_no_test_doc_at_root(self):
        offenders = [f for f in _root_test_files() if f.startswith("test_doc_")]
        assert not offenders, (
            f"Fichiers test_doc_* détectés à la racine de tests/ — "
            f"ils doivent vivre dans tests/meta/ : {offenders}"
        )

    def test_no_test_roadmap_at_root(self):
        offenders = [f for f in _root_test_files() if f.startswith("test_roadmap_")]
        assert not offenders, (
            f"Fichiers test_roadmap_* détectés à la racine de tests/ — "
            f"ils doivent vivre dans tests/meta/ : {offenders}"
        )

    def test_no_test_changelog_at_root(self):
        offenders = [f for f in _root_test_files() if f.startswith("test_changelog_")]
        assert not offenders, (
            f"Fichiers test_changelog_* détectés à la racine de tests/ — "
            f"ils doivent vivre dans tests/meta/ : {offenders}"
        )

    def test_no_test_adr_at_root(self):
        offenders = [f for f in _root_test_files() if f.startswith("test_adr_")]
        assert not offenders, (
            f"Fichiers test_adr_* détectés à la racine de tests/ — "
            f"ils doivent vivre dans tests/meta/ : {offenders}"
        )

    def test_no_test_lts_policy_at_root(self):
        assert "test_lts_policy.py" not in _root_test_files(), (
            "test_lts_policy.py détecté à la racine de tests/ — "
            "ce fichier doit vivre dans tests/meta/."
        )

    def test_no_test_license_metadata_at_root(self):
        assert "test_license_metadata.py" not in _root_test_files(), (
            "test_license_metadata.py détecté à la racine de tests/ — "
            "ce fichier doit vivre dans tests/meta/."
        )

    def test_no_test_migration_guide_at_root(self):
        assert "test_migration_guide.py" not in _root_test_files(), (
            "test_migration_guide.py détecté à la racine de tests/ — "
            "ce fichier doit vivre dans tests/meta/."
        )


class TestMovedFilesInMeta:
    """Les fichiers déplacés par META-TESTS-ROOT-MIGRATION-001 sont bien dans tests/meta/."""

    _META_DIR = TESTS_ROOT / "meta"
    _EXPECTED = [
        "test_doc_bonjour_forge.py",
        "test_doc_app_complete.py",
        "test_doc_contribute.py",
        "test_doc_deploy_advanced.py",
        "test_doc_module_author.py",
        "test_docs_config.py",
        "test_doc_structure.py",
        "test_roadmap_unified.py",
        "test_license_metadata.py",
        "test_lts_policy.py",
        "test_package_metadata.py",
        "test_packaging.py",
        "test_migration_guide.py",
        "test_deploy_prod_security_doc.py",
        "test_tpl_doc.py",
        "test_landing_post_2_2_refresh.py",
        "test_app_stability_contract.py",
        "test_api_doc.py",
    ]

    @pytest.mark.parametrize("filename", _EXPECTED)
    def test_file_in_meta(self, filename):
        assert (self._META_DIR / filename).exists(), (
            f"{filename} introuvable dans tests/meta/ — "
            "il a été déplacé par META-TESTS-ROOT-MIGRATION-001 et ne doit pas régresser."
        )
