"""Garde-fou SESSION-KEYS-DOCSTRING-001.

Vérifie que core/sessions/keys.py mentionne correctement la version
d'introduction de la migration FR→EN des clés de session.

Origine : audit F12 — docstring disait 'avant Forge 3.1' alors que
la migration a été livrée en G1 (Forge 3.0.1).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
KEYS_FILE = PROJECT_ROOT / "core" / "sessions" / "keys.py"


class TestDocstringMentionsCorrectVersion:

    def test_no_avant_forge_3_1(self):
        text = KEYS_FILE.read_text(encoding="utf-8")
        assert "avant Forge 3.1" not in text, (
            "core/sessions/keys.py mentionne 'avant Forge 3.1' alors que "
            "la migration a été livrée en G1 (Forge 3.0.1). Corriger en "
            "'avant Forge 3.0.1'."
        )

    def test_mentions_forge_3_0_1(self):
        text = KEYS_FILE.read_text(encoding="utf-8")
        assert "Forge 3.0.1" in text, (
            "core/sessions/keys.py doit mentionner Forge 3.0.1 comme "
            "version d'introduction de la migration FR→EN."
        )

    def test_mentions_forge_4_0_retrait(self):
        text = KEYS_FILE.read_text(encoding="utf-8")
        assert "Forge 4.0" in text, (
            "core/sessions/keys.py doit mentionner Forge 4.0 comme version "
            "de retrait des clés legacy françaises (next major)."
        )


class TestApiStable:

    def test_session_get_importable(self):
        from core.sessions.keys import session_get
        assert callable(session_get)

    def test_session_constants_unchanged(self):
        from core.sessions.keys import (
            SESSION_KEY_AUTHENTICATED,
            SESSION_KEY_EXPIRES_AT,
            SESSION_KEY_USER,
        )
        assert SESSION_KEY_AUTHENTICATED == "authenticated"
        assert SESSION_KEY_USER == "user"
        assert SESSION_KEY_EXPIRES_AT == "expires_at"

    def test_legacy_fr_fallback_still_works(self):
        from core.sessions.keys import SESSION_KEY_AUTHENTICATED, session_get
        old_session = {"authentifie": True, "utilisateur": "alice"}
        assert session_get(old_session, SESSION_KEY_AUTHENTICATED) is True
