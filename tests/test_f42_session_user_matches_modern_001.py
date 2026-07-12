"""F42 : _session_user_matches accepte l'auth moderne (_auth_user_id).

Avant : ne lisait que la session legacy `authenticated`/`user`, donc échouait
sous l'auth moderne (ADR-010) qui ne pose que `_auth_user_id`. La revalidation
MFA rejetait alors une identité pourtant authentifiée.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_mfa")

from forge_mvc_mfa.mfa import _session_user_matches


class _Req:
    def __init__(self, session: dict) -> None:
        self.session = session


def test_modern_session_matches() -> None:
    # Auth moderne : la session ne porte que _auth_user_id.
    assert _session_user_matches(_Req({"_auth_user_id": 7}), 7) is True


def test_modern_session_mismatch() -> None:
    assert _session_user_matches(_Req({"_auth_user_id": 7}), 8) is False


def test_legacy_session_still_matches() -> None:
    # Rétro-compat : la session legacy authenticated + user.id fonctionne encore.
    assert _session_user_matches(_Req({"authenticated": True, "user": {"id": 7}}), 7) is True


def test_legacy_session_mismatch() -> None:
    assert _session_user_matches(_Req({"authenticated": True, "user": {"id": 7}}), 8) is False


def test_no_session_is_false() -> None:
    assert _session_user_matches(_Req({}), 7) is False
