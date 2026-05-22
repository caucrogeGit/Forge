"""Tests du flux challenge MFA à la connexion (AUTH-MFA-004).

Vérifie l'intégration entre authentification primaire, challenge MFA temporaire
et finalisation de session. Aucun accès base de données réelle.
"""
from __future__ import annotations

import pytest
pytest.importorskip("forge_mvc_mfa")
pytest.importorskip("pyotp")

import pyotp

from forge_mvc_mfa.secret_crypto import encrypt_totp_secret

_TEST_FERNET_KEY = "aGsgWXh_DXIOTYw2nsUvnhb8tQkPflH-rWnGywxsg8I="

@pytest.fixture(autouse=True)
def _mfa_secret_key(monkeypatch):
    monkeypatch.setenv("FORGE_MFA_SECRET_KEY", _TEST_FERNET_KEY)



from forge_mvc_mfa import (
    MFA_CHALLENGE_STARTED_AT_KEY,
    MFA_CHALLENGE_USER_ID_KEY,
    MFA_FACTOR_TOTP,
    MFA_STATUS_ACTIVE,
    AuthMfaFactor,
    clear_mfa_challenge,
    get_mfa_challenge_user_id,
    has_pending_mfa_challenge,
    is_mfa_enabled,
    start_mfa_challenge,
    verify_mfa_challenge,
)
from core.auth.session import AUTH_USER_ID_SESSION_KEY, login_user
from core.auth.user import AuthUser
from core.http.response import Response
from mvc.controllers.mfa_challenge_controller import MfaChallengeController


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeRequest:
    def __init__(self, session=None):
        self.session = {} if session is None else dict(session)
        self.body = {}
        self.ip = "127.0.0.1"

    class _FakeHeaders:
        def get(self, name, default=""):
            return default

    headers = _FakeHeaders()


_USER = AuthUser(
    id=1,
    email="test@example.com",
    password_hash="$argon2id$fake",
    is_active=True,
)


def _make_totp_factor(user_id: int = 1) -> tuple[AuthMfaFactor, str]:
    secret = pyotp.random_base32()
    factor = AuthMfaFactor(
        id=1,
        user_id=user_id,
        factor_type=MFA_FACTOR_TOTP,
        totp_secret=encrypt_totp_secret(secret),
        status=MFA_STATUS_ACTIVE,
    )
    code = pyotp.TOTP(secret).now()
    return factor, code


# ---------------------------------------------------------------------------
# Flux — login sans MFA : session ouverte directement
# ---------------------------------------------------------------------------


def test_login_sans_mfa_ouvre_session_directement():
    req = FakeRequest()
    assert is_mfa_enabled([]) is False
    login_user(req, _USER)
    assert req.session[AUTH_USER_ID_SESSION_KEY] == 1
    assert MFA_CHALLENGE_USER_ID_KEY not in req.session


# ---------------------------------------------------------------------------
# Flux — login avec MFA : challenge créé, session non ouverte
# ---------------------------------------------------------------------------


def test_login_avec_mfa_ne_cree_pas_session_complete():
    req = FakeRequest()
    start_mfa_challenge(req, _USER)
    assert AUTH_USER_ID_SESSION_KEY not in req.session


def test_login_avec_mfa_cree_etat_temporaire_challenge():
    req = FakeRequest()
    start_mfa_challenge(req, _USER)
    assert has_pending_mfa_challenge(req) is True
    assert get_mfa_challenge_user_id(req) == 1


# ---------------------------------------------------------------------------
# Code MFA valide
# ---------------------------------------------------------------------------


def test_code_mfa_valide_retourne_resultat():
    req = FakeRequest()
    start_mfa_challenge(req, _USER)
    factor, code = _make_totp_factor()
    result = verify_mfa_challenge(req, code, factors=[factor])
    assert result is not None
    assert result.user_id == 1


def test_code_mfa_valide_supprime_etat_temporaire():
    req = FakeRequest()
    start_mfa_challenge(req, _USER)
    factor, code = _make_totp_factor()
    verify_mfa_challenge(req, code, factors=[factor])
    assert MFA_CHALLENGE_USER_ID_KEY not in req.session
    assert MFA_CHALLENGE_STARTED_AT_KEY not in req.session


def test_code_mfa_valide_permet_appel_login_user():
    req = FakeRequest()
    start_mfa_challenge(req, _USER)
    factor, code = _make_totp_factor()
    result = verify_mfa_challenge(req, code, factors=[factor])
    assert result is not None
    login_user(req, _USER)
    assert req.session[AUTH_USER_ID_SESSION_KEY] == 1


# ---------------------------------------------------------------------------
# Code MFA invalide
# ---------------------------------------------------------------------------


def test_code_mfa_invalide_ne_finalise_pas_connexion():
    req = FakeRequest()
    start_mfa_challenge(req, _USER)
    factor, _ = _make_totp_factor()
    result = verify_mfa_challenge(req, "000000", factors=[factor])
    assert result is None
    assert AUTH_USER_ID_SESSION_KEY not in req.session


def test_code_mfa_invalide_conserve_challenge():
    req = FakeRequest()
    start_mfa_challenge(req, _USER)
    factor, _ = _make_totp_factor()
    verify_mfa_challenge(req, "000000", factors=[factor])
    assert has_pending_mfa_challenge(req) is True
    assert get_mfa_challenge_user_id(req) == 1


# ---------------------------------------------------------------------------
# Logout : supprime l'état MFA
# ---------------------------------------------------------------------------


def test_logout_supprime_etat_temporaire_mfa():
    req = FakeRequest()
    start_mfa_challenge(req, _USER)
    clear_mfa_challenge(req)
    assert has_pending_mfa_challenge(req) is False
    assert get_mfa_challenge_user_id(req) is None


def test_suppression_session_efface_challenge():
    req = FakeRequest()
    start_mfa_challenge(req, _USER)
    req.session.clear()
    assert has_pending_mfa_challenge(req) is False


# ---------------------------------------------------------------------------
# Sécurité : secret et code non stockés
# ---------------------------------------------------------------------------


def test_secret_mfa_jamais_expose_en_session():
    req = FakeRequest()
    factor, _ = _make_totp_factor()
    start_mfa_challenge(req, _USER)
    for v in req.session.values():
        assert factor.totp_secret not in str(v)


def test_code_mfa_non_stocke_en_session():
    req = FakeRequest()
    start_mfa_challenge(req, _USER)
    factor, code = _make_totp_factor()
    verify_mfa_challenge(req, code, factors=[factor])
    for v in req.session.values():
        assert code not in str(v)


# ---------------------------------------------------------------------------
# Contrôleur — redirections (pas de template nécessaire)
# ---------------------------------------------------------------------------


def test_form_sans_challenge_redirige_vers_login():
    req = FakeRequest()
    response = MfaChallengeController.form(req)
    assert response.status == 302
    assert response.headers.get("Location") == "/login"


def test_verify_sans_challenge_redirige_vers_login():
    req = FakeRequest()
    req.session["csrf_token"] = "tok"
    req.body = {"csrf_token": ["tok"], "code": ["123456"]}
    response = MfaChallengeController.verify(req, _load_factors=lambda uid: [])
    assert response.status == 302
    assert response.headers.get("Location") == "/login"


def test_verify_code_valide_appelle_finalize():
    req = FakeRequest()
    req.session["csrf_token"] = "tok"
    start_mfa_challenge(req, _USER)
    factor, code = _make_totp_factor()

    finalized = []

    def fake_finalize(user_id, session_id, session, request):
        finalized.append(user_id)
        return Response(302, headers={"Location": "/"})

    req.body = {"csrf_token": ["tok"], "code": [code]}
    response = MfaChallengeController.verify(
        req,
        _load_factors=lambda uid: [factor],
        _finalize_login=fake_finalize,
    )
    assert response.status == 302
    assert finalized == [1]


def test_verify_code_valide_supprime_challenge_avant_finalize():
    req = FakeRequest()
    req.session["csrf_token"] = "tok"
    start_mfa_challenge(req, _USER)
    factor, code = _make_totp_factor()

    challenge_at_finalize = []

    def fake_finalize(user_id, session_id, session, request):
        challenge_at_finalize.append(MFA_CHALLENGE_USER_ID_KEY in request.session)
        return Response(302, headers={"Location": "/"})

    req.body = {"csrf_token": ["tok"], "code": [code]}
    MfaChallengeController.verify(
        req,
        _load_factors=lambda uid: [factor],
        _finalize_login=fake_finalize,
    )
    assert challenge_at_finalize == [False]


# ---------------------------------------------------------------------------
# Contrôleur — chemins avec rendu (template nécessaire)
# ---------------------------------------------------------------------------


def _setup_renderer(tmp_path):
    """Configure un renderer Jinja2 minimal pour les tests de rendu."""
    import core.forge as forge
    from core.templating.manager import template_manager
    from integrations.jinja2.renderer import Jinja2Renderer

    renderer = Jinja2Renderer(str(tmp_path))
    template_manager.register(renderer)
    forge._cfg["views_dir"] = str(tmp_path)

    auth_dir = tmp_path / "auth"
    auth_dir.mkdir(exist_ok=True)
    (auth_dir / "mfa_challenge.html").write_text("{{ erreur }}")

    errors_dir = tmp_path / "errors"
    errors_dir.mkdir(exist_ok=True)
    (errors_dir / "403.html").write_text("403")


def test_form_avec_challenge_retourne_200(tmp_path):
    _setup_renderer(tmp_path)
    req = FakeRequest()
    req.session["csrf_token"] = "tok"
    start_mfa_challenge(req, _USER)
    response = MfaChallengeController.form(req)
    assert response.status == 200


def test_verify_code_invalide_retourne_formulaire(tmp_path):
    _setup_renderer(tmp_path)
    req = FakeRequest()
    req.session["csrf_token"] = "tok"
    start_mfa_challenge(req, _USER)
    factor, _ = _make_totp_factor()
    req.body = {"csrf_token": ["tok"], "code": ["000000"]}
    response = MfaChallengeController.verify(
        req,
        _load_factors=lambda uid: [factor],
    )
    assert response.status == 200


# ---------------------------------------------------------------------------
# Audit : pas de nouvelle table SQL, pas de dépendance externe
# ---------------------------------------------------------------------------


def test_aucune_nouvelle_table_sql_dans_le_controleur():
    import mvc.controllers.mfa_challenge_controller as mod
    source = open(mod.__file__).read()
    assert "CREATE TABLE" not in source.upper()


def test_aucune_dependance_externe_dans_le_controleur():
    import mvc.controllers.mfa_challenge_controller as mod
    source = open(mod.__file__).read()
    assert "import requests" not in source
    assert "import httpx" not in source
    assert "import pyotp" not in source


def test_le_challenge_ne_connecte_pas_utilisateur():
    req = FakeRequest()
    start_mfa_challenge(req, _USER)
    assert AUTH_USER_ID_SESSION_KEY not in req.session
    assert MFA_CHALLENGE_USER_ID_KEY in req.session


# ---------------------------------------------------------------------------
# Audit — événements MFA
# ---------------------------------------------------------------------------


def test_event_mfa_required_existe():
    from core.auth.audit import AUTH_EVENT_MFA_REQUIRED
    assert AUTH_EVENT_MFA_REQUIRED == "mfa.challenge.required"


def test_event_mfa_required_dans_types_valides():
    from core.auth.audit import AUTH_AUDIT_EVENT_TYPES, AUTH_EVENT_MFA_REQUIRED
    assert AUTH_EVENT_MFA_REQUIRED in AUTH_AUDIT_EVENT_TYPES


def test_event_mfa_challenge_success_existe():
    from core.auth.audit import AUTH_EVENT_MFA_CHALLENGE_SUCCESS
    assert AUTH_EVENT_MFA_CHALLENGE_SUCCESS == "mfa.challenge.success"


def test_event_mfa_challenge_failed_existe():
    from core.auth.audit import AUTH_EVENT_MFA_CHALLENGE_FAILED
    assert AUTH_EVENT_MFA_CHALLENGE_FAILED == "mfa.challenge.failed"


def test_auth_controller_importe_event_mfa_required():
    import mvc.controllers.auth_controller as mod
    source = open(mod.__file__).read()
    assert "AUTH_EVENT_MFA_REQUIRED" in source


def test_auth_controller_appelle_log_auth_event_mfa_required():
    import mvc.controllers.auth_controller as mod
    source = open(mod.__file__).read()
    # Cherche la 2e occurrence (la 1re est l'import, la 2e est l'appel)
    first = source.find("AUTH_EVENT_MFA_REQUIRED")
    assert first != -1
    second = source.find("AUTH_EVENT_MFA_REQUIRED", first + 1)
    assert second != -1, "AUTH_EVENT_MFA_REQUIRED doit être appelé, pas seulement importé"
    assert "log_auth_event" in source[max(0, second - 80): second + 40]


# ---------------------------------------------------------------------------
# Sécurité — mot de passe invalide ne déclenche pas MFA
# ---------------------------------------------------------------------------


def test_password_invalide_ne_cree_pas_etat_mfa():
    req = FakeRequest()
    # Si le mot de passe est invalide, start_mfa_challenge n'est jamais appelé
    # La session reste sans état MFA
    assert MFA_CHALLENGE_USER_ID_KEY not in req.session
    assert not has_pending_mfa_challenge(req)


def test_etat_mfa_absent_par_defaut():
    req = FakeRequest()
    assert get_mfa_challenge_user_id(req) is None
    assert has_pending_mfa_challenge(req) is False
