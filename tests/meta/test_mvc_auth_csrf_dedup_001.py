"""Garde-fou MVC-AUTH-CSRF-DEDUP-001.

Vérifie que la vérification CSRF n'est pas dupliquée entre les contrôleurs
MVC et CsrfMiddleware :

- _csrf_valid et import hmac absents de auth_controller.py ;
- la vérification manuelle csrf_token != absente de mfa_challenge_controller.py ;
- CsrfMiddleware reste câblé dans application.py ;
- aucune route login/logout ne désactive csrf=False.

Avant ce ticket, auth_controller.py refaisait hmac.compare_digest alors que
CsrfMiddleware.check() l'exécutait déjà à chaque POST /login et /logout.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

_AUTH_CTRL   = PROJECT_ROOT / "mvc" / "controllers" / "auth_controller.py"
_MFA_CTRL    = PROJECT_ROOT / "mvc" / "controllers" / "mfa_challenge_controller.py"
_APP         = PROJECT_ROOT / "core" / "app" / "application.py"
_ROUTES      = PROJECT_ROOT / "mvc" / "routes.py"


class TestCsrfValidRemovedFromAuthController:
    """_csrf_valid et son import hmac ont été supprimés du contrôleur auth."""

    def test_file_exists(self):
        assert _AUTH_CTRL.exists()

    def test_csrf_valid_function_absent(self):
        text = _AUTH_CTRL.read_text(encoding="utf-8")
        assert "_csrf_valid" not in text, (
            "auth_controller.py définit encore _csrf_valid — "
            "la vérification CSRF doit être déléguée à CsrfMiddleware."
        )

    def test_hmac_import_absent(self):
        text = _AUTH_CTRL.read_text(encoding="utf-8")
        assert "import hmac" not in text, (
            "auth_controller.py importe encore hmac — "
            "inutile depuis la suppression de _csrf_valid."
        )


class TestManualCsrfCheckRemovedFromMfaController:
    """La comparaison manuelle != csrf_token a été retirée de mfa_challenge_controller."""

    def test_file_exists(self):
        assert _MFA_CTRL.exists()

    def test_no_inline_csrf_inequality_check(self):
        text = _MFA_CTRL.read_text(encoding="utf-8")
        pattern = re.compile(r"csrf_token\s*!=\s*session|session.*csrf_token.*!=", re.IGNORECASE)
        assert not pattern.search(text), (
            "mfa_challenge_controller.py contient encore une vérification "
            "manuelle csrf_token != session — doublon avec CsrfMiddleware."
        )


class TestCsrfMiddlewareStillWired:
    """CsrfMiddleware reste opérationnel dans core/app/application.py."""

    def test_csrf_middleware_imported(self):
        text = _APP.read_text(encoding="utf-8")
        assert "CsrfMiddleware" in text, (
            "core/app/application.py n'importe plus CsrfMiddleware — "
            "la protection CSRF globale serait perdue."
        )

    def test_csrf_middleware_instantiated(self):
        text = _APP.read_text(encoding="utf-8")
        assert "CsrfMiddleware()" in text, (
            "core/app/application.py n'instancie plus CsrfMiddleware — "
            "la protection CSRF globale serait perdue."
        )


class TestLoginLogoutRoutesKeepCsrf:
    """Les routes POST /login et /logout ne désactivent pas csrf=False."""

    def test_routes_file_exists(self):
        assert _ROUTES.exists()

    def test_login_route_does_not_disable_csrf(self):
        text = _ROUTES.read_text(encoding="utf-8")
        assert not re.search(r"/login.*csrf\s*=\s*False", text), (
            "La route /login désactive csrf=False — CsrfMiddleware ne s'appliquera plus."
        )

    def test_logout_route_does_not_disable_csrf(self):
        text = _ROUTES.read_text(encoding="utf-8")
        assert not re.search(r"/logout.*csrf\s*=\s*False", text), (
            "La route /logout désactive csrf=False — CsrfMiddleware ne s'appliquera plus."
        )
