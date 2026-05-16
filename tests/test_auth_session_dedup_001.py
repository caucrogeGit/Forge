"""Tests comportementaux AUTH-SESSION-DEDUP-001.

Vérifie :
- les deux piles importent sans DeprecationWarning ;
- require_auth et login_required sont importables et fonctionnels ;
- les deux piles restent indépendantes (pas de régression) ;
- aucun DeprecationWarning n'est émis depuis core.security.session ou core.auth.session.
"""
from __future__ import annotations

import warnings
from types import SimpleNamespace

import pytest


# ── Imports sans DeprecationWarning ──────────────────────────────────────────


def test_import_core_auth_session_no_deprecation_warning():
    """Importer core.auth.session n'émet aucun DeprecationWarning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        import core.auth.session  # noqa: F401


def test_import_core_security_session_no_deprecation_warning():
    """Importer core.security.session n'émet aucun DeprecationWarning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        import core.security.session  # noqa: F401


def test_import_require_auth_no_deprecation_warning():
    """Importer require_auth depuis core.security.decorators n'émet aucun DeprecationWarning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        from core.security.decorators import require_auth  # noqa: F401


def test_import_login_required_no_deprecation_warning():
    """Importer login_required depuis core.auth.session n'émet aucun DeprecationWarning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        from core.auth.session import login_required  # noqa: F401


# ── require_auth : comportement ───────────────────────────────────────────────


def _unauthenticated_request() -> SimpleNamespace:
    """Requête sans cookie de session."""
    return SimpleNamespace(headers={}, body={}, ip="127.0.0.1")


def test_require_auth_redirects_unauthenticated():
    """require_auth redirige vers /login si la requête n'est pas authentifiée."""
    from core.security.decorators import require_auth

    @require_auth
    def protected(request):
        return SimpleNamespace(status=200)

    response = protected(_unauthenticated_request())
    assert response.status == 302
    assert response.headers["Location"] == "/login"


def test_require_auth_is_importable():
    """require_auth est importable depuis core.security.decorators."""
    from core.security.decorators import require_auth
    assert callable(require_auth)


# ── login_required : comportement ────────────────────────────────────────────


def test_login_required_returns_401_for_unauthenticated():
    """login_required retourne 401 si la requête n'est pas authentifiée (pas de redirect_to)."""
    from core.auth.session import login_required

    @login_required
    def protected(request):
        return SimpleNamespace(status=200)

    response = protected(_unauthenticated_request())
    assert response.status == 401


def test_login_required_redirects_with_redirect_to():
    """login_required(redirect_to='/login') redirige si non authentifié."""
    from core.auth.session import login_required

    @login_required(redirect_to="/login")
    def protected(request):
        return SimpleNamespace(status=200)

    response = protected(_unauthenticated_request())
    assert response.status == 302
    assert response.headers["Location"] == "/login"


def test_login_required_is_importable():
    """login_required est importable depuis core.auth.session."""
    from core.auth.session import login_required
    assert callable(login_required)


# ── Coexistence des deux piles ────────────────────────────────────────────────


def test_both_stacks_importable_simultaneously():
    """Les deux piles sont importables simultanément sans conflit."""
    import core.auth.session as _auth
    import core.security.session as _sec

    assert hasattr(_auth, "login_user")
    assert hasattr(_sec, "authenticate_session")


def test_require_auth_and_login_required_importable_simultaneously():
    """require_auth et login_required coexistent sans conflit d'importation."""
    from core.auth.session import login_required
    from core.security.decorators import require_auth

    assert callable(require_auth)
    assert callable(login_required)


# ── Mécanismes de session distincts ──────────────────────────────────────────


def test_is_authenticated_canonical_requires_auth_user_id():
    """core.auth.session.is_authenticated retourne False sans _auth_user_id dans la session."""
    from core.auth.session import is_authenticated

    # Session legacy (authenticated=True, user={...}) sans _auth_user_id
    request = SimpleNamespace(
        session={"authenticated": True, "user": {"id": 1}},
        headers={},
    )
    assert is_authenticated(request) is False


def test_is_authenticated_legacy_requires_legacy_keys():
    """core.security.session.is_authenticated retourne False sans SESSION_KEY_AUTHENTICATED."""
    from core.security.session import is_authenticated

    # Requête sans cookie de session
    request = SimpleNamespace(headers={})
    assert is_authenticated(request) is False


def test_session_store_not_broken_after_dedup():
    """forge.configure(session_store=...) fonctionne toujours après les modifications."""
    from core.sessions import MemorySessionStore
    import core.forge as forge
    from core.sessions.manager import set_session_store

    store = MemorySessionStore()
    forge.configure(session_store=store)
    try:
        from core.sessions.manager import get_session_store
        assert get_session_store() is store
    finally:
        set_session_store(None)
