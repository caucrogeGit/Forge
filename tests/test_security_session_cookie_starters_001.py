"""Tests — SECURITY-SESSION-COOKIE-STARTERS-001.

Vérifie que les contrôleurs Auth et MFA n'écrivent plus le cookie de session
de façon inline et qu'ils délèguent à `core.security.cookies` :

  - `mvc/controllers/auth_controller.py` importe et utilise
    `set_session_cookie` et `clear_session_cookie` ;
  - `mvc/controllers/mfa_challenge_controller.py` importe et utilise
    `set_session_cookie` ;
  - aucun de ces fichiers ne contient plus de construction inline
    `Set-Cookie` ni de référence à `SESSION_COOKIE_NAME`.

Verrouille aussi côté comportement le contrat équivalent : un cookie posé
ou effacé via les helpers porte bien tous les attributs (`Path=/`,
`HttpOnly`, `SameSite=Strict`, `Secure`, et `Max-Age=0` pour la
suppression).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from core.http.response import Response
from core.security.cookies import clear_session_cookie, set_session_cookie
from core.security.session import SESSION_COOKIE_NAME


PROJECT_ROOT = Path(__file__).parent.parent
AUTH_CTRL = PROJECT_ROOT / "tests" / "fixtures" / "app" / "mvc" / "controllers" / "auth_controller.py"
MFA_CTRL = PROJECT_ROOT / "tests" / "fixtures" / "app" / "mvc" / "controllers" / "mfa_challenge_controller.py"


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ── Structurel : plus d'écriture inline ─────────────────────────────────────


class TestNoInlineSetCookieInControllers:
    @pytest.mark.parametrize("controller", [AUTH_CTRL, MFA_CTRL])
    def test_no_raw_set_cookie_assignment(self, controller: Path):
        source = _source(controller)
        assert 'headers["Set-Cookie"]' not in source, (
            f"{controller.name} pose encore directement headers[\"Set-Cookie\"]. "
            "Utiliser set_session_cookie() / clear_session_cookie() à la place."
        )

    @pytest.mark.parametrize("controller", [AUTH_CTRL, MFA_CTRL])
    def test_no_reference_to_session_cookie_name(self, controller: Path):
        source = _source(controller)
        assert "SESSION_COOKIE_NAME" not in source, (
            f"{controller.name} référence encore SESSION_COOKIE_NAME. "
            "Les helpers gèrent le nom du cookie ; l'import devrait avoir disparu."
        )

    def test_auth_controller_imports_helpers(self):
        source = _source(AUTH_CTRL)
        assert "from core.security.cookies import" in source
        assert "set_session_cookie" in source
        assert "clear_session_cookie" in source

    def test_auth_controller_uses_set_and_clear(self):
        source = _source(AUTH_CTRL)
        # set_session_cookie attendu pour login_form, login (branche MFA), login (branche succès).
        assert source.count("set_session_cookie(") >= 3
        # clear_session_cookie attendu pour logout.
        assert source.count("clear_session_cookie(") == 1

    def test_mfa_controller_imports_helper(self):
        source = _source(MFA_CTRL)
        assert "from core.security.cookies import set_session_cookie" in source

    def test_mfa_controller_uses_set(self):
        source = _source(MFA_CTRL)
        assert source.count("set_session_cookie(") >= 1


# ── Comportement : contrat équivalent à l'ancienne écriture inline ─────────


class TestHelpersReproduceLegacyCookie:
    """Le helper doit produire exactement le même contrat que l'inline antérieur."""

    def _attrs(self, set_cookie: str) -> dict[str, str | None]:
        out: dict[str, str | None] = {}
        for i, part in enumerate(p.strip() for p in set_cookie.split(";") if p.strip()):
            if "=" in part:
                k, v = part.split("=", 1)
                out[k if i == 0 else k.lower()] = v
            else:
                out[part.lower()] = None
        return out

    def test_set_matches_legacy_login_cookie(self):
        response = Response(200, b"")
        set_session_cookie(response, "abc123")
        attrs = self._attrs(response.headers["Set-Cookie"])
        assert attrs[SESSION_COOKIE_NAME] == "abc123"
        assert attrs["path"] == "/"
        assert "httponly" in attrs
        assert attrs["samesite"] == "Strict"
        assert "secure" in attrs

    def test_clear_matches_legacy_logout_cookie(self):
        response = Response(200, b"")
        clear_session_cookie(response)
        cookie = response.headers["Set-Cookie"]
        attrs = self._attrs(cookie)
        assert attrs[SESSION_COOKIE_NAME] == ""
        assert "Max-Age=0" in cookie
        assert attrs["path"] == "/"
        assert "httponly" in attrs
        assert attrs["samesite"] == "Strict"
        assert "secure" in attrs


# ADR-044 : l'app de dogfooding est devenue une fixture de test ; les
# contrôleurs ne sont plus un paquet `mvc` importable au niveau racine.
# L'usage des helpers de cookie reste vérifié par inspection de source ci-dessus.
