"""Garde-fou AUTH-AUDIT-VOCAB-PERIMETER-001.

Vérifie que la documentation officialise la règle de périmètre du vocabulaire
d'audit auth MFA/RBAC dans le core :

- ADR-011 existe et documente la règle.
- core/auth/audit.py contient les constantes MFA/RBAC (elles y sont assumées).
- La documentation mentionne que la logique MFA/RBAC complète reste opt-in.
- La documentation mentionne que le core ne doit pas importer forge_mvc_mfa,
  forge_mvc_rbac, ni pyotp.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
ADR_011 = PROJECT_ROOT / "docs" / "adr" / "011-auth-audit-vocab-perimeter.md"
AUDIT_PY = PROJECT_ROOT / "core" / "auth" / "audit.py"


# ---------------------------------------------------------------------------
# ADR-011 — existence et contenu
# ---------------------------------------------------------------------------

class TestAdr011Exists:

    def _src(self) -> str:
        assert ADR_011.exists(), "ADR-011 doit exister (AUTH-AUDIT-VOCAB-PERIMETER-001)"
        return ADR_011.read_text(encoding="utf-8")

    def test_adr_011_exists(self):
        assert ADR_011.exists(), (
            "docs/adr/011-auth-audit-vocab-perimeter.md doit exister"
        )

    def test_adr_mentions_vocab_assumed_in_core(self):
        src = self._src()
        assert "assumé" in src or "assumés" in src or "assume" in src.lower(), (
            "ADR-011 doit indiquer que le vocabulaire MFA/RBAC est assumé dans le core"
        )

    def test_adr_mentions_mfa_opt_in(self):
        src = self._src()
        assert "forge-mvc-mfa" in src, (
            "ADR-011 doit mentionner forge-mvc-mfa comme module responsable de la logique MFA"
        )

    def test_adr_mentions_rbac_opt_in(self):
        src = self._src()
        assert "forge-mvc-rbac" in src, (
            "ADR-011 doit mentionner forge-mvc-rbac comme module responsable de la logique RBAC"
        )

    def test_adr_mentions_pyotp_forbidden(self):
        src = self._src()
        assert "pyotp" in src, (
            "ADR-011 doit mentionner pyotp comme import interdit dans le core"
        )

    def test_adr_mentions_import_boundary(self):
        src = self._src()
        assert "interdit" in src or "inviolable" in src, (
            "ADR-011 doit mentionner la frontière d'import inviolable"
        )

    def test_adr_mentions_adr_004(self):
        src = self._src()
        assert "ADR-004" in src, (
            "ADR-011 doit référencer ADR-004 (décision complémentaire sur core/auth/audit.py)"
        )

    def test_adr_mentions_adr_008(self):
        src = self._src()
        assert "ADR-008" in src, (
            "ADR-011 doit référencer ADR-008 (architecture audit auth)"
        )

    def test_adr_mentions_require_role_is_core_primitive(self):
        src = self._src()
        assert "require_role" in src, (
            "ADR-011 doit documenter que require_role est une primitive core légère"
        )


# ---------------------------------------------------------------------------
# core/auth/audit.py — constantes MFA et RBAC assumées
# ---------------------------------------------------------------------------

class TestAuditConstantsAssumedInCore:

    def _src(self) -> str:
        assert AUDIT_PY.exists(), "core/auth/audit.py doit exister"
        return AUDIT_PY.read_text(encoding="utf-8")

    def test_mfa_required_event_present(self):
        assert "mfa.challenge.required" in self._src(), (
            "AUTH_EVENT_MFA_REQUIRED doit être défini dans core/auth/audit.py"
        )

    def test_mfa_challenge_failed_event_present(self):
        assert "mfa.challenge.failed" in self._src(), (
            "AUTH_EVENT_MFA_CHALLENGE_FAILED doit être défini dans core/auth/audit.py"
        )

    def test_mfa_revalidation_event_present(self):
        assert "mfa.revalidation.failed" in self._src(), (
            "AUTH_EVENT_MFA_REVALIDATION_FAILED doit être défini dans core/auth/audit.py"
        )

    def test_user_role_added_event_present(self):
        assert "user_role.added" in self._src(), (
            "AUTH_EVENT_USER_ROLE_ADDED doit être défini dans core/auth/audit.py"
        )

    def test_user_role_removed_event_present(self):
        assert "user_role.removed" in self._src(), (
            "AUTH_EVENT_USER_ROLE_REMOVED doit être défini dans core/auth/audit.py"
        )

    def test_audit_py_does_not_import_forge_mvc_mfa(self):
        src = self._src()
        assert "forge_mvc_mfa" not in src, (
            "core/auth/audit.py ne doit pas importer forge_mvc_mfa"
        )

    def test_audit_py_does_not_import_forge_mvc_rbac(self):
        src = self._src()
        assert "forge_mvc_rbac" not in src, (
            "core/auth/audit.py ne doit pas importer forge_mvc_rbac"
        )

    def test_audit_py_does_not_import_pyotp(self):
        src = self._src()
        assert "pyotp" not in src, (
            "core/auth/audit.py ne doit pas importer pyotp"
        )
