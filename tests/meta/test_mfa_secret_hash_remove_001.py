"""Garde-fou MFA-SECRET-HASH-DEPRECATION-RESOLVE-001.

Vérifie que :
1. Le code MFA n'utilise plus la clé legacy 'secret_hash'
2. Aucun DeprecationWarning sur secret_hash n'est émis
3. La doc ne mentionne plus secret_hash comme API courante

Origine : Claude Code Majeur 1 — DeprecationWarning "Sera refuse en Forge 3.0"
était périmé en 3.0.1. Décision option A : retrait définitif car MFA est
Pre-Alpha et la dépréciation avait eu 4+ releases pour permettre la migration.
"""
from __future__ import annotations

from pathlib import Path

import pytest
pytest.importorskip("forge_mvc_mfa")

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
MFA_SRC = PROJECT_ROOT / "packages" / "forge-mvc-mfa" / "forge_mvc_mfa" / "mfa.py"


class TestSecretHashCodeRemoved:
    """Le code MFA n'utilise plus la clé legacy 'secret_hash'."""

    def test_mfa_py_no_active_secret_hash_reference(self):
        text = MFA_SRC.read_text(encoding="utf-8")
        active_lines = [
            (i, line) for i, line in enumerate(text.splitlines(), 1)
            if "secret_hash" in line and not line.strip().startswith("#")
        ]
        assert not active_lines, (
            "secret_hash encore référencé activement dans mfa.py :\n"
            + "\n".join(f"  ligne {i}: {line}" for i, line in active_lines)
        )

    def test_no_deprecation_warning_secret_hash_in_mfa(self):
        text = MFA_SRC.read_text(encoding="utf-8")
        assert not ("DeprecationWarning" in text and "secret_hash" in text), (
            "Un DeprecationWarning sur secret_hash subsiste dans mfa.py. "
            "Doit être retiré (T4 option A)."
        )

    def test_secret_hash_property_absent(self):
        text = MFA_SRC.read_text(encoding="utf-8")
        assert "def secret_hash" not in text, (
            "La property secret_hash est encore présente dans AuthMfaFactor. "
            "Doit être retirée (T4 option A)."
        )


class TestSecretHashNotImportable:
    """secret_hash n'existe plus comme attribut de AuthMfaFactor."""

    def test_authfactor_has_no_secret_hash_attribute(self):
        from forge_mvc_mfa import AuthMfaFactor, MFA_FACTOR_TOTP, MFA_STATUS_PENDING
        factor = AuthMfaFactor(
            id=None, user_id=1, factor_type=MFA_FACTOR_TOTP,
            totp_secret="TESTSECRET", status=MFA_STATUS_PENDING,
        )
        assert not hasattr(factor, "secret_hash"), (
            "AuthMfaFactor expose encore un attribut secret_hash. "
            "Doit être retiré (T4 option A)."
        )


class TestDocUpdated:
    """docs/auth.md ne mentionne plus secret_hash comme API courante."""

    def test_auth_md_no_active_secret_hash_alias(self):
        auth_md = PROJECT_ROOT / "docs" / "auth.md"
        if not auth_md.exists():
            pytest.skip("docs/auth.md absent")
        text = auth_md.read_text(encoding="utf-8")
        assert "alias deprecie" not in text or "secret_hash" not in text, (
            "docs/auth.md mentionne encore secret_hash comme alias déprécié actif. "
            "Cette mention doit être retirée (retrait effectué en 3.0.1)."
        )
