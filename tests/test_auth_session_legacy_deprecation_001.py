"""Tests de dépréciation AUTH-SESSION-LEGACY-DEPRECATION-001.

Vérifie que :
- chaque fonction legacy dépréciée émet un DeprecationWarning à l'appel ;
- les fonctions dépréciées continuent à fonctionner malgré l'avertissement ;
- les fonctions infrastructure (get_session_id, get_session, set_flash…) n'émettent aucun warning ;
- le pont 4.2b reste fonctionnel ;
- aucun import circulaire n'est introduit.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from core.sessions import MemorySessionStore
from core.sessions.manager import set_session_store


@pytest.fixture(autouse=True)
def isolated_store():
    """Store propre pour chaque test."""
    store = MemorySessionStore()
    set_session_store(store)
    yield store
    set_session_store(None)


def _raw_legacy_session(store: MemorySessionStore, user_id: int = 7) -> tuple[str, str]:
    """Crée une session legacy via le store directement — sans API dépréciée."""
    sid = store.create()
    user_data = {"id": user_id, "login": "test", "prenom": "", "nom": "", "email": "", "roles": []}
    new_sid = store.authenticate(sid, user_data, 3600)
    return new_sid, f"__Host-session_id={new_sid}"


# ── create_session ────────────────────────────────────────────────────────────


def test_create_session_emits_deprecation_warning(isolated_store):
    """create_session() émet un DeprecationWarning à l'appel."""
    from core.security.session import create_session

    with pytest.warns(DeprecationWarning, match="create_session"):
        sid = create_session()
    assert sid is not None and len(sid) == 64


def test_create_session_still_works_despite_warning(isolated_store):
    """create_session() retourne un identifiant de session valide malgré le warning."""
    from core.security.session import create_session

    with pytest.warns(DeprecationWarning):
        sid = create_session()
    assert isolated_store.get(sid) is not None


# ── authenticate_session ──────────────────────────────────────────────────────


def test_authenticate_session_emits_deprecation_warning(isolated_store):
    """authenticate_session() émet un DeprecationWarning à l'appel."""
    from core.security.session import authenticate_session

    sid = isolated_store.create()
    with pytest.warns(DeprecationWarning, match="authenticate_session"):
        new_sid = authenticate_session(sid, {
            "UtilisateurId": 1,
            "Login": "alice",
            "Prenom": "Alice",
            "Nom": "Test",
            "Email": "alice@example.com",
            "roles": [],
        })
    assert new_sid is not None


def test_authenticate_session_still_authenticates(isolated_store):
    """authenticate_session() authentifie correctement la session malgré le warning."""
    from core.security.session import authenticate_session
    from core.sessions.keys import SESSION_KEY_AUTHENTICATED, session_get

    sid = isolated_store.create()
    with pytest.warns(DeprecationWarning):
        new_sid = authenticate_session(sid, {
            "UtilisateurId": 42,
            "Login": "alice",
            "Prenom": "Alice",
            "Nom": "Test",
            "Email": "alice@example.com",
            "roles": ["admin"],
        })
    session = isolated_store.get(new_sid)
    assert session is not None
    assert session_get(session, SESSION_KEY_AUTHENTICATED) is True
    assert session["user"]["id"] == 42


# ── is_authenticated ──────────────────────────────────────────────────────────


def test_is_authenticated_emits_deprecation_warning(isolated_store):
    """is_authenticated() émet un DeprecationWarning à l'appel."""
    from core.security.session import is_authenticated

    request = SimpleNamespace(headers={})
    with pytest.warns(DeprecationWarning, match="is_authenticated"):
        result = is_authenticated(request)
    assert result is False


def test_is_authenticated_still_works_for_legacy_session(isolated_store):
    """is_authenticated() reconnaît une session legacy malgré le warning."""
    from core.security.session import is_authenticated

    _sid, cookie = _raw_legacy_session(isolated_store, user_id=7)
    request = SimpleNamespace(headers={"Cookie": cookie})
    with pytest.warns(DeprecationWarning):
        result = is_authenticated(request)
    assert result is True


def test_is_authenticated_still_works_for_canonical_session(isolated_store):
    """is_authenticated() reconnaît une session canonique via le pont (4.2b) malgré le warning."""
    from core.auth.session import login_user
    from core.auth.user import AuthUser
    from core.security.session import is_authenticated

    sid = isolated_store.create()
    session = isolated_store.get(sid)
    cookie = f"__Host-session_id={sid}"
    request = SimpleNamespace(session=session, headers={"Cookie": cookie})
    user = AuthUser(id=55, login="x@example.com", password_hash="h", is_active=True)
    login_user(request, user)

    request2 = SimpleNamespace(headers={"Cookie": cookie})
    with pytest.warns(DeprecationWarning):
        result = is_authenticated(request2)
    assert result is True


# ── get_user ──────────────────────────────────────────────────────────────────


def test_get_user_emits_deprecation_warning(isolated_store):
    """get_user() émet un DeprecationWarning à l'appel."""
    from core.security.session import get_user

    request = SimpleNamespace(headers={})
    with pytest.warns(DeprecationWarning, match="get_user"):
        result = get_user(request)
    assert result is None


def test_get_user_still_returns_user_for_legacy_session(isolated_store):
    """get_user() retourne le dict utilisateur legacy malgré le warning."""
    from core.security.session import get_user

    _sid, cookie = _raw_legacy_session(isolated_store, user_id=7)
    request = SimpleNamespace(headers={"Cookie": cookie})
    with pytest.warns(DeprecationWarning):
        user = get_user(request)
    assert user is not None
    assert user["id"] == 7


# ── Fonctions infrastructure : aucun warning ──────────────────────────────────


def test_get_session_id_no_deprecation_warning(isolated_store):
    """get_session_id() n'émet aucun DeprecationWarning."""
    from core.security.session import get_session_id

    request = SimpleNamespace(headers={})
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        result = get_session_id(request)
    assert result is None


def test_get_session_no_deprecation_warning(isolated_store):
    """get_session() n'émet aucun DeprecationWarning."""
    from core.security.session import get_session

    sid = isolated_store.create()
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        result = get_session(sid)
    assert result is not None


def test_delete_session_no_deprecation_warning(isolated_store):
    """delete_session() n'émet aucun DeprecationWarning."""
    from core.security.session import delete_session

    sid = isolated_store.create()
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        delete_session(sid)
    assert isolated_store.get(sid) is None


def test_set_flash_no_deprecation_warning(isolated_store):
    """set_flash() n'émet aucun DeprecationWarning."""
    from core.security.session import set_flash

    sid = isolated_store.create()
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        set_flash(sid, "Bonjour", "success")


def test_get_flash_no_deprecation_warning(isolated_store):
    """get_flash() n'émet aucun DeprecationWarning."""
    from core.security.session import get_flash

    sid = isolated_store.create()
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        result = get_flash(sid)
    assert result is None


def test_user_has_role_no_deprecation_warning(isolated_store):
    """user_has_role() n'émet aucun DeprecationWarning."""
    from core.security.session import user_has_role

    _sid, cookie = _raw_legacy_session(isolated_store, user_id=7)
    request = SimpleNamespace(headers={"Cookie": cookie})
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        result = user_has_role(request, "admin")
    assert result is False  # le store crée avec roles=[] dans _raw_legacy_session


# ── Import sans warning ───────────────────────────────────────────────────────


def test_import_core_security_session_no_deprecation_warning():
    """L'import de core.security.session n'émet aucun DeprecationWarning."""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        import core.security.session  # noqa: F401


# ── Pont 4.2b toujours fonctionnel ───────────────────────────────────────────


def test_bridge_legacy_to_canonical_still_works(isolated_store):
    """Le pont 4.2b est intact : get_authenticated_user_id reconnaît une session legacy."""
    from core.auth.session import get_authenticated_user_id

    _sid, cookie = _raw_legacy_session(isolated_store, user_id=42)
    request = SimpleNamespace(headers={"Cookie": cookie})
    assert get_authenticated_user_id(request) == 42


def test_bridge_canonical_to_legacy_still_works(isolated_store):
    """Le pont 4.2b est intact : is_authenticated legacy reconnaît une session canonique."""
    from core.auth.session import login_user
    from core.auth.user import AuthUser
    from core.security.session import is_authenticated

    sid = isolated_store.create()
    session = isolated_store.get(sid)
    cookie = f"__Host-session_id={sid}"
    request = SimpleNamespace(session=session, headers={"Cookie": cookie})
    user = AuthUser(id=88, login="y@example.com", password_hash="h", is_active=True)
    login_user(request, user)

    request2 = SimpleNamespace(headers={"Cookie": cookie})
    with pytest.warns(DeprecationWarning):
        result = is_authenticated(request2)
    assert result is True
