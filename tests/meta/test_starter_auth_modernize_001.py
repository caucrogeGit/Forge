"""Garde-fou documentaire STARTER-AUTH-MODERNIZE-001.

Vérifie que :
- les starters n'importent plus create_session depuis core.security.session ;
- le middleware AuthMiddleware utilise l'is_authenticated canonique (core.auth.session) ;
- le auth_controller runtime n'appelle plus create_session() ;
- l'import create_session n'apparaît plus dans les fichiers migrés.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

_STARTERS_ROOT = PROJECT_ROOT / "cli" / "starters" / "data"
_MIDDLEWARE = PROJECT_ROOT / "core" / "security" / "middleware.py"
_AUTH_CONTROLLER_RUNTIME = PROJECT_ROOT / "mvc" / "controllers" / "auth_controller.py"

_AUTH_MFA_CONTROLLER = (
    _STARTERS_ROOT / "welcome-optin-mfa" / "files" / "mvc" / "controllers" / "auth_controller.py"
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
    / "users-core-auth"
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


# Import canonique de is_authenticated depuis core.auth.session, forme simple
# `from core.auth.session import is_authenticated` ou groupée/aliasée
# `from core.auth.session import (\n    ... is_authenticated as _is_authenticated, ...)`.
_CANONICAL_IMPORT = re.compile(
    r"from core\.auth\.session import \([^)]*\bis_authenticated\b", re.DOTALL
)


def test_middleware_imports_canonical_is_authenticated():
    src = _read(_MIDDLEWARE)
    assert (
        "from core.auth.session import is_authenticated" in src
        or _CANONICAL_IMPORT.search(src) is not None
    ), "middleware.py doit importer is_authenticated depuis core.auth.session"


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
# Le générateur `make:auth` — migration create_session
# ---------------------------------------------------------------------------
#
# Ces contrôles visaient trois starters de `cli/starters/data/` et le
# contrôleur runtime `mvc/controllers/auth_controller.py`. Les quatre chemins
# ont disparu, les starters avec l'ADR-035, le dossier `mvc/` avec l'ADR-044 :
# les quinze tests correspondants se **sautaient** en silence
# (`TESTS-DEAD-SKIPS-REVIVE-001`).
#
# Le contrôleur d'authentification est aujourd'hui **engendré** par
# `forge make:auth`. C'est donc la source du générateur qui porte la propriété,
# et c'est une cible qui ne peut pas disparaître sous le garde-fou : si elle
# disparaît, `_source_du_generateur` échoue au lieu de sauter.


def _source_du_generateur() -> str:
    """Source de `make:auth`, où vit le gabarit du contrôleur engendré.

    Lue par `__file__` plutôt que par un chemin en dur, conformément au
    pattern B.2 des conventions : un déplacement du module ne doit pas
    rendre le garde-fou muet.
    """
    from cli.security import make_auth

    return Path(make_auth.__file__).read_text(encoding="utf-8")


def test_le_generateur_n_emet_plus_create_session() -> None:
    """`create_session()` est l'API legacy que ce ticket avait retirée."""
    assert "create_session" not in _source_du_generateur(), (
        "make:auth engendre un contrôleur employant create_session, API legacy "
        "remplacée par get_session_store().create()"
    )


def test_le_generateur_emet_le_store_de_session() -> None:
    """La forme canonique est `get_session_store().create()`."""
    source = _source_du_generateur()

    assert "from core.sessions.manager import get_session_store" in source
    assert "get_session_store().create()" in source


def test_le_generateur_emet_l_is_authenticated_canonique() -> None:
    """Même règle que pour le middleware : `core.auth.session`, pas `core.security.session`."""
    source = _source_du_generateur()

    assert "from core.security.session import is_authenticated" not in source, (
        "make:auth engendre un import legacy de is_authenticated"
    )


def test_le_garde_fou_regarde_bien_quelque_chose() -> None:
    """Un garde-fou dont la cible a disparu doit échouer, jamais sauter.

    C'est la leçon de ce fichier : ses quinze contrôles ont dormi le temps de
    deux ADR parce qu'ils sautaient quand leur fichier était absent.
    """
    source = _source_du_generateur()

    assert len(source) > 2000
    assert "class AuthController" in source or "auth_controller" in source
