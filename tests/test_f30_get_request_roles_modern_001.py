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
    import forge_mvc_rbac.contract as mod
    from pathlib import Path

    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "import get_user" not in src, "get_request_roles ne doit plus importer le get_user déprécié"
