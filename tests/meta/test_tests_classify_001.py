"""Tests TESTS-CLASSIFY-001 : structure tests/ apres reorganisation.

Verifie que :
- tests/meta/ et tests/release/ existent avec leur __init__.py ;
- les fichiers garde-fous sont bien dans tests/meta/ et non a plat ;
- les fichiers release sont bien dans tests/release/ et non a plat ;
- ce test lui-meme tourne (validation que pytest decouvre tests/meta/).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

TESTS_DIR = Path(__file__).resolve().parent.parent  # tests/meta/ → tests/


# ── Existence des sous-dossiers ────────────────────────────────────────────────

class TestMetaDirExists:

    def test_meta_dir_exists(self):
        assert (TESTS_DIR / "meta").is_dir()

    def test_meta_dir_has_init(self):
        assert (TESTS_DIR / "meta" / "__init__.py").exists()


class TestReleaseDirExists:

    def test_release_dir_exists(self):
        assert (TESTS_DIR / "release").is_dir()

    def test_release_dir_has_init(self):
        assert (TESTS_DIR / "release" / "__init__.py").exists()


# ── Contenu de tests/meta/ ────────────────────────────────────────────────────

_EXPECTED_IN_META = [
    "test_lang_migration_001.py",
    "test_oidc_remove_001.py",
    "test_cli_auth_init_oidc_sql_001.py",
    "test_session_limits_status_001.py",
    "test_pbkdf2_remove_001.py",
    "test_cmd_remove_001.py",
    "test_mfa_extract_001.py",
    "test_workflow_extract_001.py",
    "test_stats_extract_001.py",
    "test_rbac_extract_001.py",
    "test_modules_explicit_routes_001.py",
    "test_auth_audit_architecture_001.py",
    "test_claude_md_001.py",
    "test_charter_v2_adoption_001.py",
    "test_consolidation_001.py",
    "test_consolidation_cli_001.py",
    "test_consolidation_doc_001.py",
    "test_consolidation_modules_001.py",
    "test_consolidation_starter_001.py",
    "test_consolidation_roadmap_001.py",
    "test_deprecation_policy.py",
    "test_phase_11_auth_close.py",
    "test_phase_12_security_ux_close.py",
    "test_phase_13_crud_close.py",
    "test_stats_generic_events_001.py",
    "test_starters_auth_audit_001.py",
    "test_auth_legacy_boundary_001.py",
    "test_auth_mfa_secret_naming_001.py",
    "test_security_md_001.py",
    "test_security_audit_001.py",
    "test_docs_consolidate_roadmaps_001.py",
    "test_docs_reference_split_001.py",
    "test_docs_charter_dedup_001.py",
    "test_docs_internal_conventions_001.py",
    "test_getting_started_3_0_001.py",
    "test_docs_landing_page_3_0_001.py",
    "test_pre_release_fix_rbac_import_001.py",
    "test_pre_release_fix_pyproject_python_001.py",
    "test_pre_release_fix_landing_links_001.py",
    "test_pre_release_fix_venv_stale_001.py",
    "test_pre_release_fix_landing_css_sync_001.py",
    "test_app_default_no_mfa_001.py",
    "test_python_312_consistency_001.py",
    "test_roadmap_3_0_consistency_001.py",
    "test_docs_positioning_v3_001.py",
    "test_docs_relations_v3_001.py",
    "test_docs_install_tags_v3_001.py",
    "test_contributing_main_branch_001.py",
    "test_landing_license_wording_001.py",
    "test_docs_reference_modules_001.py",
    "test_docs_auth_consolidate_001.py",
    "test_docs_entity_relations_consistency_001.py",
    "test_docs_stats_readme_001.py",
    "test_security_md_refresh_001.py",
    "test_mvc_auth_csrf_dedup_001.py",
    "test_hashing_ratelimit_move_001.py",
    "test_docs_audits_history_001.py",
    "test_adr_forge_3_revision_001.py",
    "test_docs_api_reference_modules_001.py",
    "test_docs_no_phantom_modules_001.py",
    "test_docs_no_orphan_pages_001.py",
    "test_tests_meta_isolate_001.py",
    "test_sessions_lang_align_001.py",
    "test_starter_auth_mfa_profile_001.py",
    "test_docs_v1_v2_terminology_001.py",
    "test_docs_getting_started_consolidate_001.py",
    "test_docs_release_section_audit_001.py",
    "test_auth_extra_extract_decision_001.py",
    "test_packaging_forge_module_001.py",
    "test_docs_cli_commands_reference_001.py",
    "test_docs_installation_windows_001.py",
    "test_landing_search_bar_001.py",
    "test_landing_positionnement_remove_001.py",
    "test_docs_release_local_starters_001.py",
    "test_pytest_reproducible_001.py",
    "test_packaging_src_layout_001.py",
    "test_mfa_secret_hash_remove_001.py",
    "test_mfa_production_decision_001.py",
    "test_oidc_exceptions_cleanup_001.py",
    "test_core_rbac_plugin_mechanism_001.py",
    "test_wheel_content_001.py",
    "test_docs_no_stale_versions_001.py",
    "test_stability_contract_3_x_001.py",
    "test_claude_md_3_0_2_001.py",
    "test_session_keys_docstring_001.py",
    "test_adr_historical_warnings_001.py",
    "test_changelog_3_0_1_3_0_2_001.py",
    "test_roadmap_3_0_1_3_0_2_001.py",
    "test_starter_6_doc_001.py",
    "test_forge_help_coverage_001.py",
    "test_forge_help_safe_flag_001.py",
    "test_mfa_security_clarify_001.py",
    "test_package_lock_sync_001.py",
    "test_docs_forge_2x_sweep_001.py",
    "test_release_validation_git_001.py",
    "test_docs_version_variable_001.py",
    "test_docs_python_examples_executable_001.py",
    "test_pytest_core_only_contract_001.py",
    "test_cli_help_coverage_001.py",
    "test_pypi_classifiers_001.py",
    "test_packages_optin_no_pypi_001.py",
    "test_release_current_version_001.py",
    "test_install_contract_001.py",
    "test_pytest_core_only_contract_clarified_001.py",
    "test_landing_articles_clickable_001.py",
    "test_meta_tests_root_migration_001.py",
    "test_meta_tests_rotation_policy_001.py",
    "test_tests_behavior_first_001.py",
    "test_public_api_duplicates_scan_001.py",
    "test_starter_lang_normalize_001.py",
    "test_starter_conventions_doc_001.py",
    "test_base_controller_surface_audit_001.py",
    "test_base_controller_api_doc_001.py",
    "test_media_core_boundary_audit_001.py",
    "test_media_extract_package_scaffold_001.py",
    "test_media_repository_move_001.py",
    "test_media_crud_integration_optin_001.py",
]


@pytest.mark.parametrize("expected_file", _EXPECTED_IN_META)
class TestMetaDirContainsExpectedFiles:

    def test_meta_file_exists(self, expected_file):
        assert (TESTS_DIR / "meta" / expected_file).exists(), (
            f"{expected_file} attendu dans tests/meta/"
        )


# ── Pas a plat dans tests/ ─────────────────────────────────────────────────────

_FORBIDDEN_AT_TOP = [
    "test_lang_migration_001.py",
    "test_oidc_remove_001.py",
    "test_cli_auth_init_oidc_sql_001.py",
    "test_session_limits_status_001.py",
    "test_pbkdf2_remove_001.py",
    "test_mfa_extract_001.py",
    "test_workflow_extract_001.py",
    "test_stats_extract_001.py",
    "test_rbac_extract_001.py",
    "test_modules_explicit_routes_001.py",
    "test_auth_audit_architecture_001.py",
    "test_claude_md_001.py",
    "test_release_compat.py",
    "test_release_policy.py",
    "test_release_checklist_001.py",
    "test_sessions_lang_align_001.py",
    "test_pytest_reproducible_001.py",
    "test_packaging_src_layout_001.py",
    "test_mfa_secret_hash_remove_001.py",
    "test_mfa_production_decision_001.py",
    "test_oidc_exceptions_cleanup_001.py",
    "test_stability_contract_3_x_001.py",
    "test_claude_md_3_0_2_001.py",
    "test_session_keys_docstring_001.py",
    "test_adr_historical_warnings_001.py",
    "test_changelog_3_0_1_3_0_2_001.py",
    "test_roadmap_3_0_1_3_0_2_001.py",
    "test_starter_6_doc_001.py",
    "test_forge_help_coverage_001.py",
    "test_forge_help_safe_flag_001.py",
    "test_mfa_security_clarify_001.py",
    "test_package_lock_sync_001.py",
    "test_docs_forge_2x_sweep_001.py",
    "test_release_validation_git_001.py",
    "test_landing_positionnement_remove_001.py",
    "test_docs_phantom_modules_001.py",
]


@pytest.mark.parametrize("forbidden_at_top", _FORBIDDEN_AT_TOP)
class TestNoMetaFilesAtTopLevel:

    def test_not_at_top_level(self, forbidden_at_top):
        assert not (TESTS_DIR / forbidden_at_top).exists(), (
            f"{forbidden_at_top} devrait etre dans tests/meta/ ou tests/release/, "
            f"pas a plat dans tests/"
        )


# ── Contenu de tests/release/ ─────────────────────────────────────────────────

_EXPECTED_IN_RELEASE = [
    "test_release_compat.py",
    "test_release_policy.py",
    "test_release_checklist_001.py",
    "test_packaging_multi_dist_001.py",
    "test_publication_2_0_build_001.py",
    "test_publication_2_0_version_001.py",
    "test_quality_ruff_001.py",
]


@pytest.mark.parametrize("expected_file", _EXPECTED_IN_RELEASE)
class TestReleaseDirContainsExpectedFiles:

    def test_release_file_exists(self, expected_file):
        assert (TESTS_DIR / "release" / expected_file).exists(), (
            f"{expected_file} attendu dans tests/release/"
        )


# ── Validation indirecte de la decouverte recursive ───────────────────────────

class TestPytestDiscoversMetaDir:
    """Si ce test s'execute, pytest decouvre bien tests/meta/ recursivement."""

    def test_this_test_runs(self):
        assert True
