"""Tests AUTH-AUDIT-001 — contrat generique d'audit Auth/User."""

from __future__ import annotations

import inspect
from datetime import datetime
from pathlib import Path

import pytest

from core.auth import (
    AUTH_EVENT_LOGIN_SUCCESS,
    AUTH_EVENT_USER_ROLE_ADDED,
    AuthAuditEvent,
    InvalidAuthAuditEventError,
    create_auth_audit_event,
    is_valid_auth_audit_event,
    normalize_auth_audit_event,
    sanitize_auth_audit_metadata,
)


def test_creation_auth_audit_event_valide():
    event = AuthAuditEvent(
        id=None,
        event_type=AUTH_EVENT_LOGIN_SUCCESS,
        user_id=1,
        actor_user_id=None,
    )

    assert event.event_type == "login.success"
    assert event.user_id == 1


def test_normalisation_depuis_dict():
    created_at = datetime(2026, 5, 6, 12, 0, 0)

    event = normalize_auth_audit_event({
        "id": 3,
        "event_type": " login.success ",
        "user_id": 1,
        "actor_user_id": 2,
        "ip_address": " 192.0.2.10 ",
        "user_agent": " Mozilla/5.0 ",
        "metadata": {"method": "password"},
        "created_at": created_at,
    })

    assert event == AuthAuditEvent(
        id=3,
        event_type=AUTH_EVENT_LOGIN_SUCCESS,
        user_id=1,
        actor_user_id=2,
        ip_address="192.0.2.10",
        user_agent="Mozilla/5.0",
        metadata={"method": "password"},
        created_at=created_at,
    )


def test_normalisation_depuis_auth_audit_event():
    original = AuthAuditEvent(
        id=None,
        event_type=AUTH_EVENT_USER_ROLE_ADDED,
        actor_user_id=1,
        metadata={"role_id": 2},
    )

    assert normalize_auth_audit_event(original) == original


def test_event_type_obligatoire():
    with pytest.raises(InvalidAuthAuditEventError):
        normalize_auth_audit_event({"id": None, "event_type": " "})


def test_user_id_optionnel():
    event = normalize_auth_audit_event({"id": None, "event_type": "logout"})

    assert event.user_id is None


@pytest.mark.parametrize("value", [0, -1, True, "1"])
def test_user_id_invalide_refuse(value):
    with pytest.raises(InvalidAuthAuditEventError):
        normalize_auth_audit_event({"id": None, "event_type": "logout", "user_id": value})


def test_actor_user_id_optionnel():
    event = normalize_auth_audit_event({"id": None, "event_type": "user.enabled", "user_id": 1})

    assert event.actor_user_id is None


@pytest.mark.parametrize("value", [0, -1, False, "1"])
def test_actor_user_id_invalide_refuse(value):
    with pytest.raises(InvalidAuthAuditEventError):
        normalize_auth_audit_event({
            "id": None,
            "event_type": "user.enabled",
            "actor_user_id": value,
        })


def test_ip_address_optionnel():
    event = normalize_auth_audit_event({"id": None, "event_type": "login.failed"})

    assert event.ip_address is None


def test_user_agent_optionnel():
    event = normalize_auth_audit_event({"id": None, "event_type": "login.failed"})

    assert event.user_agent is None


def test_metadata_optionnel():
    event = normalize_auth_audit_event({"id": None, "event_type": "login.failed"})

    assert event.metadata is None


def test_metadata_non_dict_refuse():
    with pytest.raises(InvalidAuthAuditEventError):
        normalize_auth_audit_event({
            "id": None,
            "event_type": "login.failed",
            "metadata": "bad",
        })


def test_created_at_optionnel():
    event = normalize_auth_audit_event({"id": None, "event_type": "login.failed"})

    assert event.created_at is None


def test_is_valid_auth_audit_event_retourne_true_sur_evenement_valide():
    assert is_valid_auth_audit_event(
        AuthAuditEvent(id=None, event_type=AUTH_EVENT_LOGIN_SUCCESS)
    ) is True


def test_is_valid_auth_audit_event_retourne_false_sur_evenement_invalide():
    assert is_valid_auth_audit_event({"id": None, "event_type": ""}) is False


def test_create_auth_audit_event_cree_un_evenement():
    event = create_auth_audit_event(
        event_type=AUTH_EVENT_LOGIN_SUCCESS,
        user_id=1,
        ip_address="192.0.2.10",
        user_agent="Mozilla/5.0",
        metadata={"method": "password"},
    )

    assert event == AuthAuditEvent(
        id=None,
        event_type=AUTH_EVENT_LOGIN_SUCCESS,
        user_id=1,
        actor_user_id=None,
        ip_address="192.0.2.10",
        user_agent="Mozilla/5.0",
        metadata={"method": "password"},
        created_at=None,
    )


def test_create_auth_audit_event_ne_modifie_pas_metadata_original():
    metadata = {"method": "password", "password": "secret"}

    event = create_auth_audit_event(AUTH_EVENT_LOGIN_SUCCESS, metadata=metadata)

    assert metadata == {"method": "password", "password": "secret"}
    assert event.metadata == {"method": "password"}


@pytest.mark.parametrize(
    "key",
    [
        "password",
        "password_hash",
        "token",
        "raw_token",
        "access_token",
        "refresh_token",
        "id_token",
        "secret",
        "secret_hash",
        "totp_secret",
        "recovery_code",
        "code_verifier",
    ],
)
def test_sanitize_auth_audit_metadata_retire_cles_sensibles(key):
    metadata = {key: "sensible", "method": "password"}

    assert sanitize_auth_audit_metadata(metadata) == {"method": "password"}


def test_sanitize_auth_audit_metadata_conserve_cles_non_sensibles():
    metadata = {"method": "password", "provider": "local"}

    assert sanitize_auth_audit_metadata(metadata) == metadata


def test_api_importable_depuis_core_auth():
    import core.auth as auth

    assert auth.AuthAuditEvent is AuthAuditEvent
    assert auth.AUTH_EVENT_LOGIN_SUCCESS == "login.success"
    assert auth.create_auth_audit_event is create_auth_audit_event


def test_module_necrit_pas_directement_en_base():
    import core.auth.audit as module

    source = inspect.getsource(module)
    for forbidden in ("core.database", "fetch_", "insert(", "execute(", "commit("):
        assert forbidden not in source


def test_login_user_non_modifie_par_audit():
    source = Path("core/auth/session.py").read_text(encoding="utf-8")

    assert "auth_audit" not in source
    assert "AuthAuditEvent" not in source


def test_mfa_non_modifie_par_audit():
    pytest.importorskip("forge_mvc_mfa")
    # core/auth/mfa.py (shim) supprimé (EXTRACTION-CLEANUP-SHIMS-001).
    # On vérifie que forge_mvc_mfa n'importe pas core.auth.audit.
    import forge_mvc_mfa.mfa as _mfa
    source = Path(_mfa.__file__).read_text(encoding="utf-8")

    assert "auth_audit" not in source
    assert "AuthAuditEvent" not in source


def test_aucune_interface_audit_creee():
    candidates = "\n".join(
        path.as_posix()
        for root in ("mvc/controllers", "mvc/views")
        for path in Path(root).rglob("*")
    )

    assert "audit" not in candidates.lower()
