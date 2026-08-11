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
    user = AuthUser(id=1, login="alice@example.com", password_hash="hash_abc")
    assert user.id == 1
    assert user.login == "alice@example.com"
    assert user.password_hash == "hash_abc"
    assert user.is_active is True
    assert user.created_at is None
    assert user.updated_at is None


def test_auth_user_with_all_fields():
    user = AuthUser(
        id=42,
        login="bob@example.com",
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
    user = AuthUser(id=1, login="a@b.com", password_hash="h")
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
        AuthUser(login="a@b.com", password_hash="h")  # type: ignore[call-arg]


def test_password_hash_is_required():
    with pytest.raises(TypeError):
        AuthUser(id=1, login="a@b.com")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# is_active
# ---------------------------------------------------------------------------


def test_is_active_defaults_to_true():
    user = AuthUser(id=1, login="a@b.com", password_hash="h")
    assert user.is_active is True


def test_is_active_can_be_false():
    user = AuthUser(id=1, login="a@b.com", password_hash="h", is_active=False)
    assert user.is_active is False


def test_is_active_is_bool():
    user = AuthUser(id=1, login="a@b.com", password_hash="h")
    assert isinstance(user.is_active, bool)


def test_validate_accepts_sql_boolean_is_active():
    # FORGE-10 : les backends SQL renvoient BOOLEAN / tinyint(1) en entier 0/1.
    validate_auth_user_contract({"id": 1, "login": "a@b.com", "password_hash": "h", "is_active": 1})
    validate_auth_user_contract({"id": 1, "login": "a@b.com", "password_hash": "h", "is_active": 0})


def test_validate_rejects_non_boolean_is_active():
    # Au-delà de bool et 0/1, tout est refusé (chaîne, float, entier hors 0/1, None).
    for bad in ("1", 2, 1.5, None):
        with pytest.raises(InvalidAuthUserError, match="is_active"):
            validate_auth_user_contract(
                {"id": 1, "login": "a@b.com", "password_hash": "h", "is_active": bad}
            )


# ---------------------------------------------------------------------------
# created_at / updated_at optionnels
# ---------------------------------------------------------------------------


def test_created_at_is_optional():
    user = AuthUser(id=1, login="a@b.com", password_hash="h")
    assert user.created_at is None


def test_updated_at_is_optional():
    user = AuthUser(id=1, login="a@b.com", password_hash="h")
    assert user.updated_at is None


def test_created_at_and_updated_at_accept_any_value():
    user = AuthUser(id=1, login="a@b.com", password_hash="h", created_at="2024-01-01", updated_at="2024-06-01")
    assert user.created_at == "2024-01-01"
    assert user.updated_at == "2024-06-01"


# ---------------------------------------------------------------------------
# normalize_auth_user
# ---------------------------------------------------------------------------


def test_normalize_auth_user_valid():
    data = {"id": 1, "login": " alice@example.com ", "password_hash": "hash_abc"}
    user = normalize_auth_user(data)
    assert isinstance(user, AuthUser)
    assert user.id == 1
    assert user.login == "alice@example.com"


def test_normalize_trims_email():
    data = {"id": 1, "login": "  bob@example.com  ", "password_hash": "h"}
    user = normalize_auth_user(data)
    assert user.login == "bob@example.com"


def test_normalize_coerces_int_is_active_to_bool():
    # FORGE-10 : 0/1 des backends SQL sont normalisés en bool strict.
    active = normalize_auth_user({"id": 1, "login": "a@b.com", "password_hash": "h", "is_active": 1})
    assert active.is_active is True
    inactive = normalize_auth_user({"id": 1, "login": "a@b.com", "password_hash": "h", "is_active": 0})
    assert inactive.is_active is False


def test_normalize_passes_created_at_and_updated_at():
    data = {
        "id": 1,
        "login": "a@b.com",
        "password_hash": "h",
        "created_at": "2024-01-15",
        "updated_at": "2024-03-20",
    }
    user = normalize_auth_user(data)
    assert user.created_at == "2024-01-15"
    assert user.updated_at == "2024-03-20"


def test_normalize_missing_id_raises():
    with pytest.raises(InvalidAuthUserError, match="id"):
        normalize_auth_user({"login": "a@b.com", "password_hash": "h"})


def test_normalize_missing_login_raises():
    with pytest.raises(InvalidAuthUserError, match="login"):
        normalize_auth_user({"id": 1, "password_hash": "h"})


def test_normalize_missing_password_hash_raises():
    with pytest.raises(InvalidAuthUserError, match="password_hash"):
        normalize_auth_user({"id": 1, "login": "a@b.com"})


def test_normalize_non_dict_raises():
    with pytest.raises(InvalidAuthUserError):
        normalize_auth_user("not a dict")


def test_normalize_invalid_id_zero_raises():
    with pytest.raises(InvalidAuthUserError, match="id"):
        normalize_auth_user({"id": 0, "login": "a@b.com", "password_hash": "h"})


def test_normalize_invalid_id_negative_raises():
    with pytest.raises(InvalidAuthUserError, match="id"):
        normalize_auth_user({"id": -1, "login": "a@b.com", "password_hash": "h"})


def test_normalize_empty_login_raises():
    with pytest.raises(InvalidAuthUserError, match="login"):
        normalize_auth_user({"id": 1, "login": "", "password_hash": "h"})


def test_normalize_whitespace_only_login_raises():
    with pytest.raises(InvalidAuthUserError, match="login"):
        normalize_auth_user({"id": 1, "login": "   ", "password_hash": "h"})


def test_normalize_missing_multiple_fields_raises():
    with pytest.raises(InvalidAuthUserError) as exc_info:
        normalize_auth_user({})
    message = str(exc_info.value)
    # `login` et non `email` : le champ obligatoire est l'IDENTITÉ, le contact
    # étant facultatif depuis l'ADR-089.
    assert "login" in message
    assert "id" in message
    assert "password_hash" in message


# ---------------------------------------------------------------------------
# is_valid_auth_user
# ---------------------------------------------------------------------------


def test_is_valid_auth_user_true():
    user = AuthUser(id=1, login="a@b.com", password_hash="h")
    assert is_valid_auth_user(user) is True


def test_validate_auth_user_contract_accepts_valid_user():
    user = AuthUser(id=1, login="a@b.com", password_hash="h")
    assert validate_auth_user_contract(user) is None


def test_validate_auth_user_contract_accepts_valid_dict():
    data = {"id": 1, "login": "a@b.com", "password_hash": "h"}
    assert validate_auth_user_contract(data) is None


def test_validate_auth_user_contract_rejects_invalid_dict():
    with pytest.raises(InvalidAuthUserError, match="password_hash"):
        validate_auth_user_contract({"id": 1, "login": "a@b.com"})


def test_is_valid_auth_user_false_for_dict():
    assert is_valid_auth_user({"id": 1, "login": "a@b.com"}) is False


def test_is_valid_auth_user_false_for_none():
    assert is_valid_auth_user(None) is False


def test_is_valid_auth_user_false_for_string():
    assert is_valid_auth_user("user@example.com") is False


# ---------------------------------------------------------------------------
# Isolation : pas de base de données
# ---------------------------------------------------------------------------


def test_no_database_access():
    # AuthUser peut être créé sans connexion DB ni configuration Forge.
    user = AuthUser(id=1, login="a@b.com", password_hash="h")
    assert user.id == 1


def test_no_session_created(monkeypatch):
    import core.security.session as session_module

    called = []
    monkeypatch.setattr(session_module, "create_session", lambda: called.append(True) or "fake_id")

    AuthUser(id=1, login="a@b.com", password_hash="h")
    normalize_auth_user({"id": 1, "login": "a@b.com", "password_hash": "h"})

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


# ---------------------------------------------------------------------------
# Le contact, facultatif et distinct de l'identité (ADR-089)
# ---------------------------------------------------------------------------


def test_un_compte_sans_contact_est_valide():
    """Un élève mineur n'a pas d'adresse, et son compte est légitime.

    C'est la propriété qui justifie la séparation : avant l'ADR-089, une seule
    colonne portait les deux, si bien qu'un compte sans adresse était
    impossible.
    """
    user = normalize_auth_user({"id": 1, "login": "2TNE1-01", "password_hash": "h"})

    assert user.login == "2TNE1-01"
    assert user.email is None


def test_le_contact_est_normalise_mais_pas_l_identite():
    """La casse appartient à l'identité, jamais au contact.

    Abaisser la casse d'un identifiant le déforme ; l'abaisser sur une adresse
    est la convention du courriel. Une seule colonne ne pouvait pas satisfaire
    les deux, et c'est de cette contradiction qu'est né le défaut de casse
    (`AUTH-CASE-ASYMMETRY-001`).
    """
    user = normalize_auth_user({
        "id": 1,
        "login": "2TNE1-01",
        "email": "  Prof.Durand@Ecole.FR ",
        "password_hash": "h",
    })

    assert user.login == "2TNE1-01"
    assert user.email == "prof.durand@ecole.fr"


def test_l_identite_n_a_aucune_contrainte_de_forme():
    """Rien n'exige une adresse, et c'est délibéré.

    Le cœur ne l'a jamais exigé ; c'est la CLI qui l'imposait, et cet écart est
    précisément ce que l'ADR-089 supprime.
    """
    for identite in ("2TNE1-01", "admin", "prof.durand@ecole.fr", "a"):
        user = normalize_auth_user({"id": 1, "login": identite, "password_hash": "h"})
        assert user.login == identite


def test_un_contact_vide_est_refuse():
    """Absent vaut `None` ; présent, il doit désigner quelqu'un.

    Une chaîne blanche n'est ni l'un ni l'autre, et la laisser passer
    produirait un compte que l'on croit joignable.
    """
    with pytest.raises(InvalidAuthUserError, match="email"):
        normalize_auth_user({
            "id": 1, "login": "admin", "email": "   ", "password_hash": "h",
        })
