"""Tests MFA-EXTRACT-001 — extraction de la brique MFA dans forge-mvc-mfa.

Vérifie que :
- forge_mvc_mfa expose l'API publique MFA complète
- core.auth ne réexporte plus les noms MFA dans son __all__
- Les shims core.auth.mfa / .recovery / .totp_replay ont été supprimés
  (ticket EXTRACTION-CLEANUP-SHIMS-001)
- Les fichiers SQL sont au bon emplacement
- Le pyproject.toml de forge-mvc-mfa est cohérent
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
pytest.importorskip("forge_mvc_mfa")

pytestmark = pytest.mark.meta

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MFA_PKG = _REPO_ROOT / "packages" / "forge-mvc-mfa"


# ---------------------------------------------------------------------------
# TestMfaModuleAvailable — forge_mvc_mfa importable avec API complète
# ---------------------------------------------------------------------------


class TestMfaModuleAvailable:
    def test_package_importable(self):
        import forge_mvc_mfa  # noqa: F401

    def test_version_attribute(self):
        import forge_mvc_mfa
        assert forge_mvc_mfa.__version__ == "1.0.0b1"

    def test_auth_mfa_factor_importable(self):
        from forge_mvc_mfa import AuthMfaFactor
        assert AuthMfaFactor is not None

    def test_totp_constants_importable(self):
        from forge_mvc_mfa import MFA_FACTOR_TOTP, MFA_FACTOR_RECOVERY
        assert MFA_FACTOR_TOTP == "totp"
        assert MFA_FACTOR_RECOVERY == "recovery"

    def test_status_constants_importable(self):
        from forge_mvc_mfa import MFA_STATUS_ACTIVE, MFA_STATUS_PENDING, MFA_STATUS_DISABLED
        assert MFA_STATUS_ACTIVE == "active"
        assert MFA_STATUS_PENDING == "pending"
        assert MFA_STATUS_DISABLED == "disabled"

    def test_session_key_constants_importable(self):
        from forge_mvc_mfa import (
            MFA_CHALLENGE_USER_ID_KEY,
            MFA_CHALLENGE_STARTED_AT_KEY,
            MFA_REVALIDATION_USER_ID_KEY,
            MFA_REVALIDATION_AT_KEY,
        )
        assert MFA_CHALLENGE_USER_ID_KEY
        assert MFA_CHALLENGE_STARTED_AT_KEY
        assert MFA_REVALIDATION_USER_ID_KEY
        assert MFA_REVALIDATION_AT_KEY

    def test_mfa_functions_importable(self):
        from forge_mvc_mfa import (
            is_mfa_enabled,
            is_mfa_factor_active,
            is_valid_mfa_factor,
            normalize_mfa_factor,
            validate_mfa_factor_contract,
            create_totp_factor,
            generate_totp_secret,
            confirm_totp_factor,
            verify_totp_code,
            totp_provisioning_uri,
            start_mfa_challenge,
            has_pending_mfa_challenge,
            get_mfa_challenge_user_id,
            verify_mfa_challenge,
            clear_mfa_challenge,
            mark_mfa_revalidated,
            has_recent_mfa_revalidation,
            get_mfa_revalidated_user_id,
            verify_mfa_revalidation,
            clear_mfa_revalidation,
            require_recent_mfa,
        )
        for fn in (
            is_mfa_enabled, is_mfa_factor_active, is_valid_mfa_factor,
            normalize_mfa_factor, validate_mfa_factor_contract,
            create_totp_factor, generate_totp_secret, confirm_totp_factor,
            verify_totp_code, totp_provisioning_uri,
            start_mfa_challenge, has_pending_mfa_challenge, get_mfa_challenge_user_id,
            verify_mfa_challenge, clear_mfa_challenge,
            mark_mfa_revalidated, has_recent_mfa_revalidation, get_mfa_revalidated_user_id,
            verify_mfa_revalidation, clear_mfa_revalidation, require_recent_mfa,
        ):
            assert callable(fn), f"{fn} n'est pas callable"

    def test_recovery_types_importable(self):
        from forge_mvc_mfa import AuthMfaRecoveryCode, RecoveryCodesSetup
        assert AuthMfaRecoveryCode is not None
        assert RecoveryCodesSetup is not None

    def test_recovery_functions_importable(self):
        from forge_mvc_mfa import (
            generate_recovery_code,
            create_recovery_codes,
            consume_recovery_code,
            normalize_recovery_code_record,
        )
        for fn in (generate_recovery_code, create_recovery_codes, consume_recovery_code, normalize_recovery_code_record):
            assert callable(fn)

    def test_totp_replay_functions_importable(self):
        from forge_mvc_mfa import is_replay, purge_all_totp_replay
        assert callable(is_replay)
        assert callable(purge_all_totp_replay)

    def test_result_types_importable(self):
        from forge_mvc_mfa import MfaChallengeResult, MfaRevalidationResult, TotpSetup
        assert MfaChallengeResult is not None
        assert MfaRevalidationResult is not None
        assert TotpSetup is not None

    def test_all_list_is_defined(self):
        import forge_mvc_mfa
        assert hasattr(forge_mvc_mfa, "__all__")
        assert len(forge_mvc_mfa.__all__) > 0


# ---------------------------------------------------------------------------
# TestMfaRemovedFromCoreAuthApi — core.auth ne réexporte plus les noms MFA
# ---------------------------------------------------------------------------


_MFA_NAMES_REMOVED = [
    "AuthMfaFactor",
    "MfaChallengeResult",
    "MfaRevalidationResult",
    "TotpSetup",
    "MFA_FACTOR_TOTP",
    "MFA_FACTOR_RECOVERY",
    "MFA_STATUS_ACTIVE",
    "MFA_STATUS_PENDING",
    "MFA_STATUS_DISABLED",
    "MFA_CHALLENGE_USER_ID_KEY",
    "MFA_CHALLENGE_STARTED_AT_KEY",
    "MFA_REVALIDATION_USER_ID_KEY",
    "MFA_REVALIDATION_AT_KEY",
    "is_mfa_enabled",
    "is_mfa_factor_active",
    "is_valid_mfa_factor",
    "normalize_mfa_factor",
    "validate_mfa_factor_contract",
    "create_totp_factor",
    "confirm_totp_factor",
    "verify_mfa_challenge",
    "start_mfa_challenge",
    "mark_mfa_revalidated",
]

_EXCEPTIONS_KEPT = [
    "InvalidMfaFactorError",
    "InvalidMfaRecoveryCodeError",
]


class TestMfaRemovedFromCoreAuthApi:
    def test_core_auth_all_excludes_mfa_names(self):
        import core.auth as auth
        for name in _MFA_NAMES_REMOVED:
            assert name not in auth.__all__, f"{name} encore dans core.auth.__all__"

    def test_core_auth_does_not_expose_mfa_names_as_attrs(self):
        import core.auth as auth
        for name in _MFA_NAMES_REMOVED:
            assert not hasattr(auth, name), f"{name} encore accessible sur core.auth"

    def test_exceptions_still_in_core_auth(self):
        import core.auth as auth
        for name in _EXCEPTIONS_KEPT:
            assert name in auth.__all__, f"{name} manquant de core.auth.__all__"
            assert hasattr(auth, name), f"{name} inaccessible sur core.auth"

    def test_recovery_names_not_in_core_auth_all(self):
        import core.auth as auth
        recovery_names = ["AuthMfaRecoveryCode", "RecoveryCodesSetup", "generate_recovery_codes"]
        for name in recovery_names:
            assert name not in auth.__all__, f"{name} encore dans core.auth.__all__"

    def test_totp_replay_not_in_core_auth_all(self):
        import core.auth as auth
        assert "is_replay" not in auth.__all__
        assert "purge_all_totp_replay" not in auth.__all__


# ---------------------------------------------------------------------------
# TestShimsRemoved — shims supprimés (EXTRACTION-CLEANUP-SHIMS-001)
# ---------------------------------------------------------------------------


class TestShimsRemoved:
    """Les shims créés à MFA-EXTRACT-001 ont été retirés (EXTRACTION-CLEANUP-SHIMS-001)."""

    def test_core_auth_mfa_file_does_not_exist(self):
        assert not Path("core/auth/mfa.py").exists(), (
            "core/auth/mfa.py (shim) doit être supprimé (EXTRACTION-CLEANUP-SHIMS-001)"
        )

    def test_core_auth_recovery_file_does_not_exist(self):
        assert not Path("core/auth/recovery.py").exists(), (
            "core/auth/recovery.py (shim) doit être supprimé (EXTRACTION-CLEANUP-SHIMS-001)"
        )

    def test_core_auth_totp_replay_file_does_not_exist(self):
        assert not Path("core/auth/totp_replay.py").exists(), (
            "core/auth/totp_replay.py (shim) doit être supprimé (EXTRACTION-CLEANUP-SHIMS-001)"
        )

    def test_import_from_core_auth_mfa_fails(self):
        import sys
        sys.modules.pop("core.auth.mfa", None)
        with pytest.raises((ImportError, ModuleNotFoundError)):
            importlib.import_module("core.auth.mfa")

    def test_import_from_core_auth_recovery_fails(self):
        import sys
        sys.modules.pop("core.auth.recovery", None)
        with pytest.raises((ImportError, ModuleNotFoundError)):
            importlib.import_module("core.auth.recovery")

    def test_import_from_core_auth_totp_replay_fails(self):
        import sys
        sys.modules.pop("core.auth.totp_replay", None)
        with pytest.raises((ImportError, ModuleNotFoundError)):
            importlib.import_module("core.auth.totp_replay")


# ---------------------------------------------------------------------------
# TestNoShimImportsRemain — aucun fichier n'importe encore depuis les shims
# ---------------------------------------------------------------------------


_FORBIDDEN_SHIM_IMPORTS = [
    "from core.auth.mfa",
    "from core.auth.recovery",
    "from core.auth.totp_replay",
    "import core.auth.mfa",
    "import core.auth.recovery",
    "import core.auth.totp_replay",
]


class TestNoShimImportsRemain:
    """Aucun fichier (hors ce garde-fou) n'importe depuis les anciens shims."""

    @pytest.mark.parametrize("forbidden", _FORBIDDEN_SHIM_IMPORTS)
    def test_no_imports_from_shims(self, forbidden):
        roots = [
            Path("core"), Path("mvc"), Path("forge_cli"),
            Path("tests"), Path("integrations"),
        ]
        offenders = []
        for root in roots:
            if not root.exists():
                continue
            for py_file in root.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                if py_file.name == "test_mfa_extract_001.py":
                    continue
                content = py_file.read_text(encoding="utf-8")
                if forbidden in content:
                    offenders.append(str(py_file))
        assert not offenders, (
            f"Import résiduel depuis shim '{forbidden}' dans : {offenders}"
        )


# ---------------------------------------------------------------------------
# TestSqlFilesMoved — SQL au bon emplacement
# ---------------------------------------------------------------------------


class TestSqlFilesMoved:
    def test_mfa_factors_sql_at_new_path(self):
        sql = _MFA_PKG / "sql" / "auth_mfa_factors.sql"
        assert sql.exists(), f"SQL manquant : {sql}"

    def test_mfa_recovery_codes_sql_at_new_path(self):
        sql = _MFA_PKG / "sql" / "auth_mfa_recovery_codes.sql"
        assert sql.exists(), f"SQL manquant : {sql}"

    def test_mfa_factors_sql_not_at_old_path(self):
        old = _REPO_ROOT / "mvc" / "models" / "sql" / "auth_mfa_factors.sql"
        assert not old.exists(), f"SQL encore à l'ancienne adresse : {old}"

    def test_mfa_recovery_codes_sql_not_at_old_path(self):
        old = _REPO_ROOT / "mvc" / "models" / "sql" / "auth_mfa_recovery_codes.sql"
        assert not old.exists(), f"SQL encore à l'ancienne adresse : {old}"

    def test_mfa_factors_sql_content(self):
        sql = (_MFA_PKG / "sql" / "auth_mfa_factors.sql").read_text(encoding="utf-8")
        assert "auth_mfa_factors" in sql
        assert "totp_secret" in sql

    def test_mfa_recovery_codes_sql_content(self):
        sql = (_MFA_PKG / "sql" / "auth_mfa_recovery_codes.sql").read_text(encoding="utf-8")
        assert "auth_mfa_recovery_codes" in sql


# ---------------------------------------------------------------------------
# TestPyprojectMetadata — pyproject.toml de forge-mvc-mfa
# ---------------------------------------------------------------------------


class TestPyprojectMetadata:
    def _toml(self):
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]
        with open(_MFA_PKG / "pyproject.toml", "rb") as fh:
            return tomllib.load(fh)

    def test_name(self):
        assert self._toml()["project"]["name"] == "forge-mvc-mfa"

    def test_version(self):
        assert self._toml()["project"]["version"] == "1.0.0b1"

    def test_requires_python(self):
        assert self._toml()["project"]["requires-python"] == ">=3.12"

    def test_pyotp_dependency(self):
        deps = self._toml()["project"]["dependencies"]
        assert any("pyotp" in d for d in deps), "pyotp manquant des dépendances"

    def test_find_packages_config(self):
        cfg = self._toml()["tool"]["setuptools"]["packages"]["find"]
        assert cfg["where"] == ["."]
        assert any("forge_mvc_mfa" in inc for inc in cfg.get("include", []))
