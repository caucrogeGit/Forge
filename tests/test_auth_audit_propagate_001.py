"""Tests AUTH-AUDIT-PROPAGATE-001 — log_auth_event propage ses erreurs.

Verifie que :
- log_auth_event leve InvalidAuthAuditEventError sur event_type invalide ;
- log_auth_event propage les exceptions de la couche sous-jacente (logger) ;
- safe_log_auth_event observe maintenant les echecs sans mock artificiel ;
- aucun appel direct a log_auth_event ne subsiste dans core/auth/ hors audit.py.
"""
from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import patch

import pytest

from core.auth.audit import (
    AUTH_EVENT_LOGIN_SUCCESS,
    get_audit_failure_count,
    log_auth_event,
    safe_log_auth_event,
)
from core.auth.exceptions import InvalidAuthAuditEventError


# ---------------------------------------------------------------------------
# Classe 1 — Propagation dans log_auth_event
# ---------------------------------------------------------------------------


class TestLogAuthEventPropagation:

    def test_leve_sur_event_type_vide(self):
        """event_type vide → InvalidAuthAuditEventError propagee."""
        with pytest.raises(InvalidAuthAuditEventError):
            log_auth_event("")

    def test_leve_sur_event_type_whitespace(self):
        """event_type uniquement espaces → InvalidAuthAuditEventError propagee."""
        with pytest.raises(InvalidAuthAuditEventError):
            log_auth_event("   ")

    def test_leve_sur_event_type_none(self):
        """event_type None → InvalidAuthAuditEventError propagee."""
        with pytest.raises(InvalidAuthAuditEventError):
            log_auth_event(None)  # type: ignore[arg-type]

    def test_leve_sur_user_id_invalide(self):
        """user_id non entier positif → InvalidAuthAuditEventError propagee."""
        with pytest.raises(InvalidAuthAuditEventError):
            log_auth_event(AUTH_EVENT_LOGIN_SUCCESS, user_id=-1)

    def test_leve_sur_metadata_invalide(self):
        """metadata non dict → InvalidAuthAuditEventError propagee."""
        with pytest.raises(InvalidAuthAuditEventError):
            log_auth_event(AUTH_EVENT_LOGIN_SUCCESS, metadata="pas_un_dict")  # type: ignore[arg-type]

    def test_propage_exception_logger(self):
        """Une exception emise par le logger est propagee sans etre avalee."""
        with patch.object(
            __import__("logging").getLogger("forge.auth.audit"),
            "log",
            side_effect=OSError("logger indisponible"),
        ):
            with pytest.raises(OSError, match="logger indisponible"):
                log_auth_event(AUTH_EVENT_LOGIN_SUCCESS, user_id=1)

    def test_appel_nominal_ne_leve_pas(self):
        """Un appel nominal valide ne leve aucune exception."""
        log_auth_event(AUTH_EVENT_LOGIN_SUCCESS, user_id=1, ip_address="1.2.3.4")


# ---------------------------------------------------------------------------
# Classe 2 — safe_log_auth_event observe les vraies erreurs
# ---------------------------------------------------------------------------


class TestSafeLogAuthEventObserveVraiesErreurs:

    def test_capte_erreur_validation_sans_mock(self):
        """Avec event_type vide, log_auth_event leve, safe_ capte et retourne False."""
        result = safe_log_auth_event("")
        assert result is False

    def test_incremente_compteur_sur_erreur_reelle(self):
        """Le compteur s'incremente sur une vraie InvalidAuthAuditEventError."""
        safe_log_auth_event("")
        assert get_audit_failure_count() == 1

    def test_capte_erreur_logger_sans_mock_log_auth_event(self):
        """Quand le logger est indisponible, safe_ capte et retourne False."""
        with patch.object(
            __import__("logging").getLogger("forge.auth.audit"),
            "log",
            side_effect=OSError("logger indisponible"),
        ):
            result = safe_log_auth_event(AUTH_EVENT_LOGIN_SUCCESS, user_id=1)
        assert result is False
        assert get_audit_failure_count() == 1

    def test_succes_nominal_inchange(self):
        """Un appel valide retourne True — le chemin heureux est intact."""
        result = safe_log_auth_event(AUTH_EVENT_LOGIN_SUCCESS, user_id=1)
        assert result is True
        assert get_audit_failure_count() == 0


# ---------------------------------------------------------------------------
# Classe 3 — Garde-fou : aucun appel direct dans core/auth/ hors audit.py
# ---------------------------------------------------------------------------

_DIRECT_CALL = re.compile(r"(?<!safe_)log_auth_event\s*\(")
_IMPORT_LINE = re.compile(r"^\s*(from|import)\b.*log_auth_event", re.MULTILINE)


class TestNoDirectCallsInCoreAuth:

    @pytest.mark.parametrize("py_file", [
        p for p in Path("core/auth").rglob("*.py")
        if p.name != "audit.py" and "experimental" not in str(p)
    ])
    def test_no_direct_log_auth_event_call(self, py_file: Path):
        """Aucun fichier core/auth/ (hors audit.py/experimental) n'appelle
        log_auth_event directement — tous les appels passent par safe_log_auth_event."""
        content = py_file.read_text(encoding="utf-8")
        # Retire les lignes d'import (ce ne sont pas des appels)
        content_no_imports = _IMPORT_LINE.sub("", content)
        matches = _DIRECT_CALL.findall(content_no_imports)
        assert not matches, (
            f"{py_file} appelle encore log_auth_event directement "
            "(utiliser safe_log_auth_event)"
        )
