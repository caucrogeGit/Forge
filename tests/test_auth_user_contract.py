"""Tests AUTH-USER-001 — contrat utilisateur minimal Forge."""

import inspect

import pytest

from core.auth import (
    AuthError,
    AuthUser,
    InvalidAuthUserError,
    is_valid_auth_user,
    normalize_auth_user,
    validate_auth_user_contract,
)


# ---------------------------------------------------------------------------
# Création valide
# ---------------------------------------------------------------------------


def test_create_valid_auth_user():
    user = AuthUser(id=1, email="alice@example.com", password_hash="hash_abc")
    assert user.id == 1
    assert user.email == "alice@example.com"
    assert user.password_hash == "hash_abc"
    assert user.is_active is True
    assert user.created_at is None
    assert user.updated_at is None


def test_auth_user_with_all_fields():
    user = AuthUser(
        id=42,
        email="bob@example.com",
        password_hash="hash_xyz",
        is_active=False,
        created_at="2024-01-01",
        updated_at="2024-06-01",
    )
    assert user.id == 42
    assert user.is_active is False
    assert user.created_at == "2024-01-01"
    assert user.updated_at == "2024-06-01"


def test_auth_user_is_immutable():
    user = AuthUser(id=1, email="a@b.com", password_hash="h")
    with pytest.raises(AttributeError):
        user.email = "c@d.com"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Champs obligatoires (TypeError car positional via dataclass)
# ---------------------------------------------------------------------------


def test_email_is_required():
    with pytest.raises(TypeError):
        AuthUser(id=1, password_hash="h")  # type: ignore[call-arg]


def test_id_is_required():
    with pytest.raises(TypeError):
        AuthUser(email="a@b.com", password_hash="h")  # type: ignore[call-arg]


def test_password_hash_is_required():
    with pytest.raises(TypeError):
        AuthUser(id=1, email="a@b.com")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# is_active
# ---------------------------------------------------------------------------


def test_is_active_defaults_to_true():
    user = AuthUser(id=1, email="a@b.com", password_hash="h")
    assert user.is_active is True


def test_is_active_can_be_false():
    user = AuthUser(id=1, email="a@b.com", password_hash="h", is_active=False)
    assert user.is_active is False


def test_is_active_is_bool():
    user = AuthUser(id=1, email="a@b.com", password_hash="h")
    assert isinstance(user.is_active, bool)


def test_validate_rejects_non_bool_is_active():
    with pytest.raises(InvalidAuthUserError, match="is_active"):
        validate_auth_user_contract({"id": 1, "email": "a@b.com", "password_hash": "h", "is_active": 1})


# ---------------------------------------------------------------------------
# created_at / updated_at optionnels
# ---------------------------------------------------------------------------


def test_created_at_is_optional():
    user = AuthUser(id=1, email="a@b.com", password_hash="h")
    assert user.created_at is None


def test_updated_at_is_optional():
    user = AuthUser(id=1, email="a@b.com", password_hash="h")
    assert user.updated_at is None


def test_created_at_and_updated_at_accept_any_value():
    user = AuthUser(id=1, email="a@b.com", password_hash="h", created_at="2024-01-01", updated_at="2024-06-01")
    assert user.created_at == "2024-01-01"
    assert user.updated_at == "2024-06-01"


# ---------------------------------------------------------------------------
# normalize_auth_user
# ---------------------------------------------------------------------------


def test_normalize_auth_user_valid():
    data = {"id": 1, "email": " alice@example.com ", "password_hash": "hash_abc"}
    user = normalize_auth_user(data)
    assert isinstance(user, AuthUser)
    assert user.id == 1
    assert user.email == "alice@example.com"


def test_normalize_trims_email():
    data = {"id": 1, "email": "  bob@example.com  ", "password_hash": "h"}
    user = normalize_auth_user(data)
    assert user.email == "bob@example.com"


def test_normalize_rejects_is_active_from_int():
    data = {"id": 1, "email": "a@b.com", "password_hash": "h", "is_active": 1}
    with pytest.raises(InvalidAuthUserError, match="is_active"):
        normalize_auth_user(data)


def test_normalize_passes_created_at_and_updated_at():
    data = {
        "id": 1,
        "email": "a@b.com",
        "password_hash": "h",
        "created_at": "2024-01-15",
        "updated_at": "2024-03-20",
    }
    user = normalize_auth_user(data)
    assert user.created_at == "2024-01-15"
    assert user.updated_at == "2024-03-20"


def test_normalize_missing_id_raises():
    with pytest.raises(InvalidAuthUserError, match="id"):
        normalize_auth_user({"email": "a@b.com", "password_hash": "h"})


def test_normalize_missing_email_raises():
    with pytest.raises(InvalidAuthUserError, match="email"):
        normalize_auth_user({"id": 1, "password_hash": "h"})


def test_normalize_missing_password_hash_raises():
    with pytest.raises(InvalidAuthUserError, match="password_hash"):
        normalize_auth_user({"id": 1, "email": "a@b.com"})


def test_normalize_non_dict_raises():
    with pytest.raises(InvalidAuthUserError):
        normalize_auth_user("not a dict")


def test_normalize_invalid_id_zero_raises():
    with pytest.raises(InvalidAuthUserError, match="id"):
        normalize_auth_user({"id": 0, "email": "a@b.com", "password_hash": "h"})


def test_normalize_invalid_id_negative_raises():
    with pytest.raises(InvalidAuthUserError, match="id"):
        normalize_auth_user({"id": -1, "email": "a@b.com", "password_hash": "h"})


def test_normalize_empty_email_raises():
    with pytest.raises(InvalidAuthUserError, match="email"):
        normalize_auth_user({"id": 1, "email": "", "password_hash": "h"})


def test_normalize_whitespace_only_email_raises():
    with pytest.raises(InvalidAuthUserError, match="email"):
        normalize_auth_user({"id": 1, "email": "   ", "password_hash": "h"})


def test_normalize_missing_multiple_fields_raises():
    with pytest.raises(InvalidAuthUserError) as exc_info:
        normalize_auth_user({})
    message = str(exc_info.value)
    assert "email" in message
    assert "id" in message
    assert "password_hash" in message


# ---------------------------------------------------------------------------
# is_valid_auth_user
# ---------------------------------------------------------------------------


def test_is_valid_auth_user_true():
    user = AuthUser(id=1, email="a@b.com", password_hash="h")
    assert is_valid_auth_user(user) is True


def test_validate_auth_user_contract_accepts_valid_user():
    user = AuthUser(id=1, email="a@b.com", password_hash="h")
    assert validate_auth_user_contract(user) is None


def test_validate_auth_user_contract_accepts_valid_dict():
    data = {"id": 1, "email": "a@b.com", "password_hash": "h"}
    assert validate_auth_user_contract(data) is None


def test_validate_auth_user_contract_rejects_invalid_dict():
    with pytest.raises(InvalidAuthUserError, match="password_hash"):
        validate_auth_user_contract({"id": 1, "email": "a@b.com"})


def test_is_valid_auth_user_false_for_dict():
    assert is_valid_auth_user({"id": 1, "email": "a@b.com"}) is False


def test_is_valid_auth_user_false_for_none():
    assert is_valid_auth_user(None) is False


def test_is_valid_auth_user_false_for_string():
    assert is_valid_auth_user("user@example.com") is False


# ---------------------------------------------------------------------------
# Isolation : pas de base de données
# ---------------------------------------------------------------------------


def test_no_database_access():
    # AuthUser peut être créé sans connexion DB ni configuration Forge.
    user = AuthUser(id=1, email="a@b.com", password_hash="h")
    assert user.id == 1


def test_no_session_created(monkeypatch):
    import core.security.session as session_module

    called = []
    monkeypatch.setattr(session_module, "create_session", lambda: called.append(True) or "fake_id")

    AuthUser(id=1, email="a@b.com", password_hash="h")
    normalize_auth_user({"id": 1, "email": "a@b.com", "password_hash": "h"})

    assert len(called) == 0


def test_no_rbac_dependency():
    import core.auth.user as user_module

    source = inspect.getsource(user_module)
    assert "rbac" not in source.lower()
    assert "require_permission" not in source


# ---------------------------------------------------------------------------
# Import public
# ---------------------------------------------------------------------------


def test_public_import_from_core_auth():
    from core.auth import AuthUser as AU
    from core.auth import AuthError as AE
    from core.auth import InvalidAuthUserError as IAE
    from core.auth import is_valid_auth_user as ivu
    from core.auth import normalize_auth_user as nu
    from core.auth import validate_auth_user_contract as vauc

    assert AU is not None
    assert AE is not None
    assert IAE is not None
    assert callable(nu)
    assert callable(ivu)
    assert callable(vauc)


def test_invalid_auth_user_error_is_auth_error():
    assert issubclass(InvalidAuthUserError, AuthError)


def test_auth_error_is_value_error():
    assert issubclass(AuthError, ValueError)
