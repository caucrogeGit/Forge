"""Garde-fou SESSIONS-STORE-CONTRACT-DOC-001.

Vérifie que docs/reference/sessions.md documente le contrat des stores de session :
forge.configure(session_store=...), les trois backends, le défaut MemorySessionStore,
la limite thread-safety, et le renvoi de la double pile auth/session à la Phase 4.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
SESSIONS_DOC = PROJECT_ROOT / "docs" / "reference" / "sessions.md"


def _text() -> str:
    if not SESSIONS_DOC.exists():
        pytest.skip("docs/reference/sessions.md n'existe pas")
    return SESSIONS_DOC.read_text(encoding="utf-8")


class TestSessionsDocMentionsConfigureApi:
    """La doc mentionne forge.configure(session_store=...)."""

    def test_configure_session_store_mentioned(self):
        assert "forge.configure(session_store" in _text(), (
            "docs/reference/sessions.md doit mentionner forge.configure(session_store=...)"
        )


class TestSessionsDocMentionsProtocol:
    """La doc mentionne SessionStore (le protocole)."""

    def test_session_store_protocol_mentioned(self):
        assert "SessionStore" in _text(), (
            "docs/reference/sessions.md doit mentionner SessionStore"
        )


class TestSessionsDocMentionsBackends:
    """La doc mentionne les trois backends disponibles."""

    def test_memory_store_mentioned(self):
        assert "MemorySessionStore" in _text(), (
            "docs/reference/sessions.md doit mentionner MemorySessionStore"
        )

    def test_file_store_mentioned(self):
        assert "FileSessionStore" in _text(), (
            "docs/reference/sessions.md doit mentionner FileSessionStore"
        )

    def test_mariadb_store_mentioned(self):
        assert "MariaDbSessionStore" in _text(), (
            "docs/reference/sessions.md doit mentionner MariaDbSessionStore"
        )


class TestSessionsDocMentionsDefault:
    """La doc précise que MemorySessionStore est le comportement par défaut."""

    def test_memory_is_default(self):
        text = _text()
        assert "défaut" in text and "MemorySessionStore" in text, (
            "docs/reference/sessions.md doit préciser que MemorySessionStore "
            "est le comportement par défaut"
        )


class TestSessionsDocMentionsLimits:
    """La doc mentionne les limites reportées aux tickets suivants."""

    def test_thread_safety_deferred(self):
        assert "SESSIONS-MEMORY-THREADSAFE-DOC-001" in _text(), (
            "docs/reference/sessions.md doit indiquer que la thread-safety mémoire "
            "est traitée dans SESSIONS-MEMORY-THREADSAFE-DOC-001"
        )

    def test_auth_session_dedup_deferred(self):
        text = _text()
        assert "double pile" in text or "AUTH-SESSION-DEDUP-001" in text, (
            "docs/reference/sessions.md doit mentionner la double pile auth/session "
            "renvoyée à la Phase 4"
        )
