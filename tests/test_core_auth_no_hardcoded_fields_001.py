"""Tests comportementaux CORE-AUTH-NO-HARDCODED-FIELDS-001.

Vérifie que :
- authenticate_session() accepte des dicts génériques (id, login, email) sans UtilisateurId
- authenticate_session() accepte encore les dicts legacy (UtilisateurId, Login)
- login_user() + regenerate() crée une session authentifiée sans champs FR
- les ponts legacy/canonique restent fonctionnels après la migration
- le core ne requiert aucun champ métier français pour authentifier
"""
from __future__ import annotations

import warnings

import pytest

from core.sessions.memory_store import MemorySessionStore
from core.sessions.manager import set_session_store
from core.security.session import SESSION_COOKIE_NAME
from core.auth.session import AUTH_USER_ID_SESSION_KEY, login_user
from core.auth.user import AuthUser

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def isolated_store():
    store = MemorySessionStore()
    set_session_store(store)
    yield store
    set_session_store(None)


class _FakeRequest:
    def __init__(self, session_id: str) -> None:
        self.headers = {"Cookie": f"{SESSION_COOKIE_NAME}={session_id}"}
        self.session = None  # force la résolution via le cookie


# ---------------------------------------------------------------------------
# authenticate_session() — généricité via _normalize_legacy_user
# ---------------------------------------------------------------------------


def test_authenticate_session_accepts_legacy_dict(isolated_store):
    """authenticate_session() fonctionne avec un dict UtilisateurId/Login legacy."""
    from core.security.session import authenticate_session

    sid = isolated_store.create()
    legacy_user = {
        "UtilisateurId": 42,
        "Login": "alice",
        "PasswordHash": "$argon2id$test",
        "Prenom": "Alice",
        "Nom": "Martin",
        "Email": "alice@example.com",
        "Actif": True,
        "roles": ["admin"],
    }
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        nouveau_id = authenticate_session(sid, legacy_user)

    assert nouveau_id is not None
    session = isolated_store.get(nouveau_id)
    assert session is not None
    assert session["user"]["id"] == 42
    assert session["user"]["login"] == "alice"
    assert session["user"]["email"] == "alice@example.com"
    assert session["user"]["roles"] == ["admin"]


def test_authenticate_session_accepts_generic_dict(isolated_store):
    """authenticate_session() fonctionne avec un dict générique EN (id, login, email)."""
    from core.security.session import authenticate_session

    sid = isolated_store.create()
    generic_user = {
        "id": 7,
        "login": "bob",
        "email": "bob@example.com",
        "password_hash": "$argon2id$test",
        "roles": ["viewer"],
    }
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        nouveau_id = authenticate_session(sid, generic_user)

    assert nouveau_id is not None
    session = isolated_store.get(nouveau_id)
    assert session is not None
    assert session["user"]["id"] == 7
    assert session["user"]["login"] == "bob"
    assert session["user"]["email"] == "bob@example.com"


def test_authenticate_session_generic_priority_over_legacy(isolated_store):
    """Les clés EN génériques prennent la priorité sur les clés FR legacy."""
    from core.security.session import authenticate_session

    sid = isolated_store.create()
    mixed_user = {
        "id": 10,             # EN — prioritaire
        "UtilisateurId": 99,  # FR — ignoré si id présent
        "login": "carol",
        "Login": "CAROL_LEGACY",
        "email": "carol@example.com",
        "roles": [],
    }
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        nouveau_id = authenticate_session(sid, mixed_user)

    session = isolated_store.get(nouveau_id)
    assert session["user"]["id"] == 10
    assert session["user"]["login"] == "carol"


def test_authenticate_session_preserves_roles(isolated_store):
    """authenticate_session() préserve la liste des rôles."""
    from core.security.session import authenticate_session

    sid = isolated_store.create()
    user = {"id": 5, "login": "dave", "email": "dave@example.com", "roles": ["editor", "viewer"]}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        nouveau_id = authenticate_session(sid, user)

    session = isolated_store.get(nouveau_id)
    assert set(session["user"]["roles"]) == {"editor", "viewer"}


def test_authenticate_session_returns_none_for_missing_session(isolated_store):
    """authenticate_session() retourne None si la session source est absente."""
    from core.security.session import authenticate_session

    user = {"id": 1, "login": "eve", "email": "eve@example.com", "roles": []}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        result = authenticate_session("a" * 64, user)

    assert result is None


# ---------------------------------------------------------------------------
# login_user() + regenerate() — flux canonique sans champs FR
# ---------------------------------------------------------------------------


def test_login_user_plus_regenerate_produces_new_session_id(isolated_store):
    """login_user() + regenerate() retourne un session_id différent du précédent."""
    sid = isolated_store.create()
    request = _FakeRequest(sid)
    auth_user = AuthUser(id=1, login="frank@example.com", password_hash="$argon2id$x", is_active=True)
    login_user(request, auth_user)
    nouveau_id = isolated_store.regenerate(sid)
    assert nouveau_id != sid


def test_login_user_plus_regenerate_authenticated_canonically(isolated_store):
    """Après login_user() + regenerate(), is_authenticated() canonique retourne True."""
    from core.auth.session import is_authenticated as canonical_is_authenticated

    sid = isolated_store.create()
    request = _FakeRequest(sid)
    auth_user = AuthUser(id=2, login="grace@example.com", password_hash="$argon2id$x", is_active=True)
    login_user(request, auth_user)
    nouveau_id = isolated_store.regenerate(sid)

    new_request = _FakeRequest(nouveau_id)
    assert canonical_is_authenticated(new_request) is True


def test_login_user_stores_only_auth_user_id_no_french_fields(isolated_store):
    """login_user() stocke uniquement _auth_user_id — pas de champ métier FR."""
    sid = isolated_store.create()
    request = _FakeRequest(sid)
    auth_user = AuthUser(id=99, login="henry@example.com", password_hash="$argon2id$x", is_active=True)
    login_user(request, auth_user)

    session = isolated_store.get(sid)
    assert session[AUTH_USER_ID_SESSION_KEY] == 99
    assert "UtilisateurId" not in session
    assert "Login" not in session
    assert "MotDePasse" not in session


def test_no_french_field_required_for_canonical_authentication(isolated_store):
    """Le flux canonique n'exige aucun champ métier FR pour authentifier une session."""
    sid = isolated_store.create()
    request = _FakeRequest(sid)
    auth_user = AuthUser(id=42, login="iris@example.com", password_hash="$argon2id$x", is_active=True)
    login_user(request, auth_user)

    session = isolated_store.get(sid)
    assert session.get(AUTH_USER_ID_SESSION_KEY) == 42


# ---------------------------------------------------------------------------
# Ponts legacy/canonique — non régressifs après ticket 4.5
# ---------------------------------------------------------------------------


def test_legacy_session_still_recognized_by_canonical_bridge(isolated_store):
    """Session créée par authenticate_session() reconnue par get_authenticated_user_id."""
    from core.security.session import authenticate_session
    from core.auth.session import get_authenticated_user_id

    sid = isolated_store.create()
    user = {"UtilisateurId": 77, "Login": "legacy_user", "roles": []}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        nouveau_id = authenticate_session(sid, user)

    request = _FakeRequest(nouveau_id)
    user_id = get_authenticated_user_id(request)
    assert user_id == 77


def test_canonical_session_recognized_by_legacy_bridge(isolated_store):
    """Session créée par login_user() reconnue par is_authenticated() legacy."""
    from core.security.session import is_authenticated as legacy_is_authenticated

    sid = isolated_store.create()
    request = _FakeRequest(sid)
    auth_user = AuthUser(id=33, login="jack@example.com", password_hash="$argon2id$x", is_active=True)
    login_user(request, auth_user)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        result = legacy_is_authenticated(request)
    assert result is True
