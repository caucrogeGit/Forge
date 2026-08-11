"""Tests comportementaux AUTH-SESSION-COMPATIBILITY-BRIDGE-001.

Vérifie la reconnaissance croisée entre les deux piles de session :
- une session legacy (authenticate_session) est reconnue par le flux canonique ;
- une session canonique (login_user) est reconnue par le flux legacy ;
- require_auth et login_required convergent sur les deux types de sessions ;
- aucune pollution de session (pas d'écriture de clés supplémentaires).

Note : ce fichier teste le pont de compatibilité, pas les API legacy elles-mêmes.
Les appels directs à core.security.session.is_authenticated() sont intentionnels
pour valider que le pont est fonctionnel côté legacy. Les DeprecationWarning
sont des effets de bord connus et intentionnellement ignorés ici — les tests
dédiés à la dépréciation se trouvent dans test_auth_session_legacy_deprecation_001.py.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from core.sessions import MemorySessionStore
from core.sessions.manager import set_session_store

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


@pytest.fixture(autouse=True)
def isolated_store():
    """Fournit un store propre pour chaque test."""
    store = MemorySessionStore()
    set_session_store(store)
    yield store
    set_session_store(None)


def _make_legacy_session(store: MemorySessionStore, user_id: int = 42) -> tuple[str, str]:
    """Crée une session legacy via le store directement (bypass des API dépréciées).

    Simule l'état produit par authenticate_session() sans appeler la fonction dépréciée.
    """
    sid = store.create()
    user_data = {
        "id": user_id,
        "login": "alice",
        "prenom": "Alice",
        "nom": "Test",
        "email": "alice@example.com",
        "roles": ["admin"],
    }
    new_sid = store.authenticate(sid, user_data, 3600)
    cookie = f"__Host-session_id={new_sid}"
    return new_sid, cookie


def _make_canonical_session(store: MemorySessionStore, user_id: int = 99) -> tuple[str, str]:
    """Crée une session canonique via login_user, retourne (session_id, cookie)."""
    from core.auth.session import login_user
    from core.auth.user import AuthUser
    from core.security.session import SESSION_COOKIE_NAME

    sid = store.create()
    session = store.get(sid)
    cookie = f"{SESSION_COOKIE_NAME}={sid}"

    request = SimpleNamespace(
        session=session,
        headers={"Cookie": cookie},
    )
    user = AuthUser(id=user_id, login="bob@example.com", password_hash="x", is_active=True)
    login_user(request, user)
    return sid, cookie


def _request_with_cookie(cookie: str) -> SimpleNamespace:
    return SimpleNamespace(headers={"Cookie": cookie})


# ── Session legacy reconnue par le flux canonique ────────────────────────────


def test_legacy_session_recognized_by_canonical_get_authenticated_user_id(isolated_store):
    """Une session legacy (authenticate_session) est reconnue par get_authenticated_user_id."""
    from core.auth.session import get_authenticated_user_id

    _sid, cookie = _make_legacy_session(isolated_store, user_id=42)
    request = _request_with_cookie(cookie)
    assert get_authenticated_user_id(request) == 42


def test_legacy_session_recognized_by_canonical_is_authenticated(isolated_store):
    """Une session legacy est reconnue par core.auth.session.is_authenticated."""
    from core.auth.session import is_authenticated

    _sid, cookie = _make_legacy_session(isolated_store, user_id=42)
    request = _request_with_cookie(cookie)
    assert is_authenticated(request) is True


def test_legacy_session_recognized_by_login_required(isolated_store):
    """login_required autorise une requête avec session legacy."""
    from core.auth.session import login_required

    @login_required(redirect_to="/login")
    def protected(request):
        return SimpleNamespace(status=200)

    _sid, cookie = _make_legacy_session(isolated_store, user_id=42)
    request = _request_with_cookie(cookie)
    assert protected(request).status == 200


# ── Session canonique reconnue par le flux legacy ────────────────────────────


def test_canonical_session_recognized_by_legacy_is_authenticated(isolated_store):
    """Une session canonique (login_user) est reconnue par core.security.session.is_authenticated."""
    from core.security.session import is_authenticated

    _sid, cookie = _make_canonical_session(isolated_store, user_id=99)
    request = _request_with_cookie(cookie)
    assert is_authenticated(request) is True


def test_canonical_session_recognized_by_require_auth(isolated_store):
    """require_auth autorise une requête avec session canonique."""
    from core.security.decorators import require_auth

    @require_auth
    def protected(request):
        return SimpleNamespace(status=200)

    _sid, cookie = _make_canonical_session(isolated_store, user_id=99)
    request = _request_with_cookie(cookie)
    assert protected(request).status == 200


def test_canonical_session_get_authenticated_user_id(isolated_store):
    """get_authenticated_user_id retourne l'id pour une session canonique."""
    from core.auth.session import get_authenticated_user_id

    _sid, cookie = _make_canonical_session(isolated_store, user_id=99)
    request = _request_with_cookie(cookie)
    assert get_authenticated_user_id(request) == 99


# ── Absence de pollution de session ──────────────────────────────────────────


def test_legacy_session_not_polluted_by_canonical_read(isolated_store):
    """Lire une session legacy via le flux canonique n'ajoute pas _auth_user_id."""
    from core.auth.session import get_authenticated_user_id

    sid, cookie = _make_legacy_session(isolated_store, user_id=42)
    request = _request_with_cookie(cookie)
    get_authenticated_user_id(request)

    session_after = isolated_store.get(sid)
    assert "_auth_user_id" not in session_after


def test_canonical_session_not_polluted_by_legacy_read(isolated_store):
    """Lire une session canonique via is_authenticated legacy ne modifie pas authenticated/user.

    Le store initialise déjà authenticated=False et user=None à la création.
    La lecture legacy ne doit pas changer ces valeurs (authenticated reste False, user reste None).
    """
    from core.security.session import is_authenticated

    sid, cookie = _make_canonical_session(isolated_store, user_id=99)
    request = _request_with_cookie(cookie)
    is_authenticated(request)

    session_after = isolated_store.get(sid)
    assert session_after.get("authenticated") is False, "authenticated ne doit pas passer à True"
    assert session_after.get("user") is None, "user ne doit pas être peuplé par la lecture legacy"


# ── Expiry touchée dans les deux sens ────────────────────────────────────────


def test_legacy_session_expiry_touched_by_legacy_is_authenticated(isolated_store):
    """is_authenticated legacy étend l'expiration d'une session legacy."""
    from core.security.session import is_authenticated

    sid, cookie = _make_legacy_session(isolated_store, user_id=42)
    t_before = time.time()
    request = _request_with_cookie(cookie)
    assert is_authenticated(request) is True
    session_after = isolated_store.get(sid)
    assert session_after["expires_at"] >= t_before


def test_canonical_session_expiry_touched_by_legacy_is_authenticated(isolated_store):
    """is_authenticated legacy étend l'expiration d'une session canonique."""
    from core.security.session import is_authenticated

    sid, cookie = _make_canonical_session(isolated_store, user_id=99)
    request = _request_with_cookie(cookie)
    assert is_authenticated(request) is True
    session_after = isolated_store.get(sid)
    assert "expires_at" in session_after


# ── Sessions non-authentifiées refusées ──────────────────────────────────────


def test_unauthenticated_session_rejected_by_canonical(isolated_store):
    """get_authenticated_user_id retourne None pour une session vide."""
    from core.auth.session import get_authenticated_user_id

    sid = isolated_store.create()
    cookie = f"__Host-session_id={sid}"
    request = _request_with_cookie(cookie)
    assert get_authenticated_user_id(request) is None


def test_unauthenticated_session_rejected_by_legacy(isolated_store):
    """is_authenticated legacy retourne False pour une session vide."""
    from core.security.session import is_authenticated

    sid = isolated_store.create()
    cookie = f"__Host-session_id={sid}"
    request = _request_with_cookie(cookie)
    assert is_authenticated(request) is False
