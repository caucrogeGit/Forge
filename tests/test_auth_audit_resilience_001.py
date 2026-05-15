"""Tests AUTH-AUDIT-RESILIENCE-001 — safe_log_auth_event et observabilite des echecs.

Verifie que :
- safe_log_auth_event encapsule log_auth_event sans propager d'exception ;
- les echecs emettent un warning Python loggable avec traceback ;
- le compteur d'echecs est incremente et reinitalisable ;
- aucun fichier de core/auth/ (hors audit.py) ne contient le pattern
  try: log_auth_event(...) except: pass ;
- l'API publique est coherente.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from core.auth.audit import (
    get_audit_failure_count,
    reset_audit_failure_count,
    safe_log_auth_event,
)


# ---------------------------------------------------------------------------
# Classe 1 — Succes normal
# ---------------------------------------------------------------------------


class TestSafeLogAuthEventSuccess:
    def test_returns_true_on_success(self):
        with patch("core.auth.audit.log_auth_event", return_value=None) as mock:
            result = safe_log_auth_event("login.success", user_id=1)
            assert result is True
            mock.assert_called_once_with("login.success", user_id=1)

    def test_failure_count_unchanged_on_success(self):
        with patch("core.auth.audit.log_auth_event", return_value=None):
            assert get_audit_failure_count() == 0
            safe_log_auth_event("login.success", user_id=1)
            assert get_audit_failure_count() == 0

    def test_passes_all_args_and_kwargs(self):
        with patch("core.auth.audit.log_auth_event") as mock:
            safe_log_auth_event(
                "login.failed",
                user_id=42,
                ip_address="1.2.3.4",
                metadata={"reason": "bad_password"},
            )
            mock.assert_called_once_with(
                "login.failed",
                user_id=42,
                ip_address="1.2.3.4",
                metadata={"reason": "bad_password"},
            )


# ---------------------------------------------------------------------------
# Classe 2 — Echec attrapé
# ---------------------------------------------------------------------------


class TestSafeLogAuthEventFailure:
    def test_returns_false_on_exception(self):
        with patch("core.auth.audit.log_auth_event", side_effect=RuntimeError("DB down")):
            result = safe_log_auth_event("login.success", user_id=1)
            assert result is False

    def test_does_not_propagate_exception(self):
        with patch("core.auth.audit.log_auth_event", side_effect=Exception("boom")):
            try:
                safe_log_auth_event("login.success", user_id=1)
            except Exception:
                pytest.fail("safe_log_auth_event ne doit jamais propager d'exception")

    def test_failure_count_incremented_once(self):
        with patch("core.auth.audit.log_auth_event", side_effect=Exception):
            assert get_audit_failure_count() == 0
            safe_log_auth_event("login.success", user_id=1)
            assert get_audit_failure_count() == 1

    def test_failure_count_cumulative(self):
        with patch("core.auth.audit.log_auth_event", side_effect=Exception):
            safe_log_auth_event("login.success", user_id=1)
            safe_log_auth_event("login.success", user_id=2)
            assert get_audit_failure_count() == 2

    def test_emits_warning_on_failure(self, caplog):
        with patch("core.auth.audit.log_auth_event", side_effect=RuntimeError("DB down")):
            with caplog.at_level(logging.WARNING, logger="forge.auth.audit"):
                safe_log_auth_event("mfa.rate_limited", user_id=42)
        assert any(
            "Audit event lost" in record.message and record.levelno == logging.WARNING
            for record in caplog.records
        )

    def test_warning_includes_traceback(self, caplog):
        with patch("core.auth.audit.log_auth_event", side_effect=RuntimeError("DB down")):
            with caplog.at_level(logging.WARNING, logger="forge.auth.audit"):
                safe_log_auth_event("mfa.rate_limited", user_id=42)
        assert any(record.exc_info is not None for record in caplog.records)

    def test_real_validation_error_is_caught(self):
        """Sans mock : event_type vide lève InvalidAuthAuditEventError, captée par safe_."""
        result = safe_log_auth_event("")
        assert result is False
        assert get_audit_failure_count() == 1

    def test_reset_restores_count_to_zero(self):
        with patch("core.auth.audit.log_auth_event", side_effect=Exception):
            safe_log_auth_event("login.success", user_id=1)
            safe_log_auth_event("login.success", user_id=2)
        assert get_audit_failure_count() == 2
        reset_audit_failure_count()
        assert get_audit_failure_count() == 0


# ---------------------------------------------------------------------------
# Classe 3 — Garde-fou : pas de try/except silencieux dans core/auth/
# ---------------------------------------------------------------------------


_TRY_LOG_SILENT = re.compile(
    r"try\s*:\s*\n\s+log_auth_event\b.+?\n.*?except.*?:\s*\n\s+pass",
    re.DOTALL,
)


class TestNoSilentTryExceptInCoreAuth:
    @pytest.mark.parametrize("py_file", [
        p for p in Path("core/auth").rglob("*.py") if p.name != "audit.py"
    ])
    def test_no_silent_try_except_around_log_auth_event(self, py_file):
        content = py_file.read_text(encoding="utf-8")
        matches = _TRY_LOG_SILENT.findall(content)
        assert not matches, (
            f"{py_file} contient encore try: log_auth_event(...) except: pass — "
            "utiliser safe_log_auth_event() à la place"
        )


# ---------------------------------------------------------------------------
# Classe 4 — API publique coherente
# ---------------------------------------------------------------------------


class TestApiPublique:
    def test_safe_log_auth_event_exportable_depuis_core_auth(self):
        from core.auth import safe_log_auth_event as sla
        assert callable(sla)

    def test_log_auth_event_toujours_disponible(self):
        from core.auth.audit import log_auth_event as raw
        assert callable(raw)

    def test_get_audit_failure_count_retourne_entier(self):
        from core.auth.audit import get_audit_failure_count as gafc
        assert callable(gafc)
        assert isinstance(gafc(), int)
        assert gafc() >= 0

    def test_reset_audit_failure_count_disponible(self):
        from core.auth.audit import reset_audit_failure_count as rafc
        assert callable(rafc)

    def test_get_audit_failure_count_exportable_depuis_core_auth(self):
        from core.auth import get_audit_failure_count
        assert callable(get_audit_failure_count)
