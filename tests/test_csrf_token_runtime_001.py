"""Garde-fou runtime de `BaseController.csrf_token` (WELCOME-FORGE-CSRF-SESSION-001).

La sémantique enseignée par le parcours welcome-forge n'était gardée qu'au
niveau « le snippet compile ». Ici on l'éprouve au runtime, sur le vrai
`BaseController.csrf_token` :

- sans session active, le jeton CSRF est la chaîne vide ;
- après bootstrap d'une session (qui pose un `csrf_token`), il vaut ce jeton.
"""
from __future__ import annotations

from core.mvc.controller import BaseController
from core.security.session import SESSION_COOKIE_NAME
from core.sessions.manager import get_session_store


class _FakeRequest:
    """Requête minimale : `csrf_token` ne lit que l'en-tête `Cookie`."""

    def __init__(self, cookie: str = ""):
        self.headers = {"Cookie": cookie} if cookie else {}


def test_csrf_token_vide_sans_session():
    assert BaseController.csrf_token(_FakeRequest()) == ""


def test_csrf_token_present_apres_bootstrap_session():
    store = get_session_store()
    session_id = store.create()  # crée une session, pose un csrf_token
    token = store.get(session_id)["csrf_token"]
    assert token  # non vide

    request = _FakeRequest(f"{SESSION_COOKIE_NAME}={session_id}")
    assert BaseController.csrf_token(request) == token
