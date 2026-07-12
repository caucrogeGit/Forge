"""F30 : get_request_roles ne passe plus par core.security.session.get_user (déprécié).

- `request.roles` reste le point d'injection canonique (auth moderne, ADR-010).
- Le repli sur la session legacy est lu directement, sans le get_user déprécié,
  donc SANS DeprecationWarning.
"""
from __future__ import annotations

import warnings

import pytest

pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac.contract import get_request_roles


class _ReqRoles:
    def __init__(self, roles: object) -> None:
        self.roles = roles


class _ReqNoRoles:
    roles = None


def test_injected_roles_are_returned() -> None:
    assert get_request_roles(_ReqRoles(["admin", "editor"])) == ["admin", "editor"]


def test_injected_roles_filtered_to_strings() -> None:
    assert get_request_roles(_ReqRoles(["admin", 1, None, "editor"])) == ["admin", "editor"]


def test_injected_non_list_is_empty() -> None:
    assert get_request_roles(_ReqRoles("admin")) == []


def test_no_roles_and_no_session_is_empty() -> None:
    assert get_request_roles(_ReqNoRoles()) == []


def test_no_deprecation_warning_emitted() -> None:
    # Le fix F30 retire l'appel au get_user déprécié : aucun DeprecationWarning.
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        assert get_request_roles(_ReqNoRoles()) == []


def test_source_no_longer_imports_deprecated_get_user() -> None:
    import re
    from pathlib import Path

    import forge_mvc_rbac.contract as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    # `\b...\b` : le mot exact `get_user`, pas `get_user_role_slugs`.
    assert not re.search(r"\bimport get_user\b", src), (
        "get_request_roles ne doit plus importer le get_user déprécié"
    )


class TestModernAuthResolution:
    """A (RBAC contrat autonome) : rôles résolus en base sous l'auth moderne,
    sans injection request.roles préalable (marche sur route publique)."""

    def test_resolves_roles_from_db_when_authenticated(self, monkeypatch) -> None:
        import core.auth.session as auth
        import forge_mvc_rbac.resolver as resolver

        monkeypatch.setattr(auth, "get_authenticated_user_id", lambda req: 7)
        monkeypatch.setattr(resolver, "get_user_role_slugs", lambda uid, **k: ("admin", "editor"))
        assert get_request_roles(_ReqNoRoles()) == ["admin", "editor"]

    def test_injected_roles_take_priority_over_db(self, monkeypatch) -> None:
        import core.auth.session as auth
        import forge_mvc_rbac.resolver as resolver

        monkeypatch.setattr(auth, "get_authenticated_user_id", lambda req: 7)
        monkeypatch.setattr(resolver, "get_user_role_slugs", lambda uid, **k: ("admin",))
        assert get_request_roles(_ReqRoles(["cached"])) == ["cached"]

    def test_not_authenticated_is_empty(self, monkeypatch) -> None:
        import core.auth.session as auth

        monkeypatch.setattr(auth, "get_authenticated_user_id", lambda req: None)
        assert get_request_roles(_ReqNoRoles()) == []

    def test_missing_role_tables_is_empty(self, monkeypatch) -> None:
        import core.auth.session as auth
        import forge_mvc_rbac.resolver as resolver

        monkeypatch.setattr(auth, "get_authenticated_user_id", lambda req: 7)

        def _missing(uid, **k):
            raise RuntimeError("Table 'app.user_roles' doesn't exist")

        monkeypatch.setattr(resolver, "get_user_role_slugs", _missing)
        # L'exception est absorbée : on retombe sur la session legacy (vide ici).
        assert get_request_roles(_ReqNoRoles()) == []
