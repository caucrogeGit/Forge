"""Garde-fou documentaire STARTER-AUTH-MODERNIZE-001.

Vérifie que :
- les starters n'importent plus create_session depuis core.security.session ;
- le middleware AuthMiddleware utilise l'is_authenticated canonique (core.auth.session) ;
- le auth_controller runtime n'appelle plus create_session() ;
- l'import create_session n'apparaît plus dans les fichiers migrés.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

_STARTERS_ROOT = PROJECT_ROOT / "forge_cli" / "starters" / "data"
_MIDDLEWARE = PROJECT_ROOT / "core" / "security" / "middleware.py"
_AUTH_CONTROLLER_RUNTIME = PROJECT_ROOT / "mvc" / "controllers" / "auth_controller.py"

_AUTH_MFA_CONTROLLER = (
    _STARTERS_ROOT / "auth-mfa" / "files" / "mvc" / "controllers" / "auth_controller.py"
)
_SUIVI_CONTROLLER = (
    _STARTERS_ROOT
    / "suivi-comportement-eleves"
    / "files"
    / "mvc"
    / "controllers"
    / "auth_controller.py"
)
_UTILISATEURS_CONTROLLER = (
    _STARTERS_ROOT
    / "utilisateurs-auth"
    / "files"
    / "mvc"
    / "controllers"
    / "auth_controller.py"
)


def _read(path: Path) -> str:
    if not path.exists():
        pytest.skip(f"{path.relative_to(PROJECT_ROOT)} introuvable")
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# middleware.py — migration canonical is_authenticated
# ---------------------------------------------------------------------------


def test_middleware_imports_canonical_is_authenticated():
    src = _read(_MIDDLEWARE)
    assert "from core.auth.session import is_authenticated" in src, (
        "middleware.py doit importer is_authenticated depuis core.auth.session"
    )


def test_middleware_does_not_import_legacy_is_authenticated():
    src = _read(_MIDDLEWARE)
    assert "from core.security.session import is_authenticated" not in src, (
        "middleware.py ne doit plus importer is_authenticated depuis core.security.session"
    )


def test_middleware_does_not_call_create_session():
    src = _read(_MIDDLEWARE)
    assert "create_session()" not in src, (
        "middleware.py ne doit pas appeler create_session()"
    )


# ---------------------------------------------------------------------------
# mvc/controllers/auth_controller.py (runtime) — migration create_session
# ---------------------------------------------------------------------------


def test_runtime_auth_controller_does_not_import_create_session():
    src = _read(_AUTH_CONTROLLER_RUNTIME)
    assert "create_session" not in src, (
        "mvc/controllers/auth_controller.py ne doit plus importer ou appeler create_session"
    )


def test_runtime_auth_controller_uses_session_store_create():
    src = _read(_AUTH_CONTROLLER_RUNTIME)
    assert "_get_session_store" in src and ".create()" in src, (
        "mvc/controllers/auth_controller.py doit utiliser _get_session_store().create()"
    )


# ---------------------------------------------------------------------------
# starter utilisateurs-auth — migration create_session
# ---------------------------------------------------------------------------


def test_starter_utilisateurs_does_not_import_create_session():
    src = _read(_UTILISATEURS_CONTROLLER)
    assert "create_session" not in src, (
        "starter utilisateurs-auth ne doit plus importer create_session"
    )


def test_starter_utilisateurs_uses_session_store_create():
    src = _read(_UTILISATEURS_CONTROLLER)
    assert "_get_session_store" in src or "get_session_store" in src, (
        "starter utilisateurs-auth doit utiliser get_session_store().create()"
    )


# ---------------------------------------------------------------------------
# starter suivi-comportement-eleves — migration create_session
# ---------------------------------------------------------------------------


def test_starter_suivi_does_not_import_create_session():
    src = _read(_SUIVI_CONTROLLER)
    assert "create_session" not in src, (
        "starter suivi-comportement-eleves ne doit plus importer create_session"
    )


def test_starter_suivi_uses_session_store_create():
    src = _read(_SUIVI_CONTROLLER)
    assert "_get_session_store" in src or "get_session_store" in src, (
        "starter suivi-comportement-eleves doit utiliser get_session_store().create()"
    )


# ---------------------------------------------------------------------------
# starter auth-mfa — migration create_session
# ---------------------------------------------------------------------------


def test_starter_auth_mfa_does_not_import_create_session():
    src = _read(_AUTH_MFA_CONTROLLER)
    assert "create_session" not in src, (
        "starter auth-mfa ne doit plus importer create_session"
    )


def test_starter_auth_mfa_uses_session_store_create():
    src = _read(_AUTH_MFA_CONTROLLER)
    assert "_get_session_store" in src or "get_session_store" in src, (
        "starter auth-mfa doit utiliser get_session_store().create()"
    )


# ---------------------------------------------------------------------------
# Vérifications transversales — aucun starter ne réintroduit create_session
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "controller_path",
    [
        _AUTH_MFA_CONTROLLER,
        _SUIVI_CONTROLLER,
        _UTILISATEURS_CONTROLLER,
        _AUTH_CONTROLLER_RUNTIME,
    ],
    ids=["auth-mfa", "suivi-comportement-eleves", "utilisateurs-auth", "runtime"],
)
def test_no_create_session_call_in_migrated_controllers(controller_path):
    src = _read(controller_path)
    assert "create_session()" not in src, (
        f"{controller_path.name} ne doit pas appeler create_session()"
    )


@pytest.mark.parametrize(
    "controller_path",
    [
        _AUTH_MFA_CONTROLLER,
        _SUIVI_CONTROLLER,
        _UTILISATEURS_CONTROLLER,
    ],
    ids=["auth-mfa", "suivi-comportement-eleves", "utilisateurs-auth"],
)
def test_starters_import_session_store(controller_path):
    src = _read(controller_path)
    assert "get_session_store" in src, (
        f"{controller_path.name} doit importer get_session_store depuis core.sessions.manager"
    )
