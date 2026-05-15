"""Guard test G1 — SESSIONS-LANG-ALIGN-001.

Vérifie :
- Aucune clé de session française n'est écrite dans le code de production.
- session_get() résout les clés françaises legacy vers les clés anglaises.
"""
from __future__ import annotations

import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

pytestmark = pytest.mark.meta

_STORE_FILES = [
    PROJECT_ROOT / "core" / "sessions" / "memory_store.py",
    PROJECT_ROOT / "core" / "sessions" / "file_store.py",
    PROJECT_ROOT / "core" / "sessions" / "mariadb_store.py",
]


@pytest.mark.meta
class TestNoFrenchSessionKeysInProductionCode:

    @pytest.mark.parametrize("store_path", _STORE_FILES, ids=lambda p: p.name)
    def test_no_authentifie_write(self, store_path):
        content = store_path.read_text(encoding="utf-8")
        assert '"authentifie":' not in content, (
            f"{store_path.name} écrit encore la clé française 'authentifie'"
        )

    @pytest.mark.parametrize("store_path", _STORE_FILES, ids=lambda p: p.name)
    def test_no_utilisateur_write(self, store_path):
        content = store_path.read_text(encoding="utf-8")
        assert '"utilisateur":' not in content, (
            f"{store_path.name} écrit encore la clé française 'utilisateur'"
        )

    @pytest.mark.parametrize("store_path", _STORE_FILES, ids=lambda p: p.name)
    def test_no_expire_a_write(self, store_path):
        content = store_path.read_text(encoding="utf-8")
        assert '"expire_a":' not in content, (
            f"{store_path.name} écrit encore la clé française 'expire_a'"
        )

    def test_security_session_no_direct_french_reads(self):
        path = PROJECT_ROOT / "core" / "security" / "session.py"
        content = path.read_text(encoding="utf-8")
        assert 'session.get("authentifie"' not in content
        assert 'session.get("utilisateur"' not in content
        assert 'session["authentifie"]' not in content
        assert 'session["utilisateur"]' not in content


@pytest.mark.meta
class TestLegacySessionKeysStillReadable:

    def test_legacy_authenticated_key_resolved(self):
        from core.sessions.keys import SESSION_KEY_AUTHENTICATED, session_get
        assert session_get({"authentifie": True}, SESSION_KEY_AUTHENTICATED) is True

    def test_legacy_user_key_resolved(self):
        from core.sessions.keys import SESSION_KEY_USER, session_get
        user = {"id": 1, "login": "alice"}
        assert session_get({"utilisateur": user}, SESSION_KEY_USER) is user

    def test_new_key_takes_priority_over_legacy(self):
        from core.sessions.keys import SESSION_KEY_AUTHENTICATED, session_get
        session = {"authenticated": True, "authentifie": False}
        assert session_get(session, SESSION_KEY_AUTHENTICATED) is True

    def test_missing_key_returns_default(self):
        from core.sessions.keys import SESSION_KEY_AUTHENTICATED, session_get
        assert session_get({}, SESSION_KEY_AUTHENTICATED, False) is False
