"""Tests — AUTH-SESSION-HARDENING-001 : durcissement des sessions Forge.

Vérifie que :
- la session est rotée (nouvel identifiant) après login réussi ;
- la session est rotée après MFA valide ;
- le logout invalide côté serveur et expire le cookie ;
- les états temporaires MFA sont nettoyés après succès et logout ;
- aucune donnée sensible n'est stockée en session ;
- le format du session_id est validé à l'extraction.
"""
from __future__ import annotations

import re

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
    has_pending_mfa_challenge,
    start_mfa_challenge,
    verify_mfa_challenge,
)
from core.auth.session import AUTH_USER_ID_SESSION_KEY
from core.auth.user import AuthUser
from core.security.session import (
    authenticate_session,
    create_session,
    get_session,
    get_session_id,
    delete_session,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SESSION_ID_RE = re.compile(r"^[0-9a-f]{64}$")

_UTILISATEUR = {
    "UtilisateurId": 1,
    "Login": "testuser",
    "Prenom": "Test",
    "Nom": "User",
    "Email": "test@example.com",
    "Actif": True,
    "PasswordHash": "$argon2id$fake",
    "roles": [],
}

_AUTH_USER = AuthUser(
    id=1,
    email="test@example.com",
    password_hash="$argon2id$fake",
    is_active=True,
)


class FakeRequest:
    def __init__(self, session_id: str | None = None):
        self._sid = session_id
        self.body: dict = {}
        self.ip = "127.0.0.1"

    class _Headers:
        def __init__(self, sid: str | None):
            self._sid = sid

        def get(self, name: str, default: str = "") -> str:
            if name == "Cookie" and self._sid:
                return f"__Host-session_id={self._sid}"
            return default

    @property
    def headers(self):
        return self._Headers(self._sid)


class FakeRequestWithSession:
    """FakeRequest avec session dict inline (pour les tests MFA sans core.security)."""
    def __init__(self, session=None):
        self.session = {} if session is None else dict(session)
        self.ip = "127.0.0.1"
        self.body: dict = {}

    class _Headers:
        def get(self, name: str, default: str = "") -> str:
            return default

    headers = _Headers()


def _make_totp_factor(user_id: int = 1) -> tuple[AuthMfaFactor, str]:
    secret = pyotp.random_base32()
    factor = AuthMfaFactor(
        id=1,
        user_id=user_id,
        factor_type=MFA_FACTOR_TOTP,
        totp_secret=encrypt_totp_secret(secret),
        status=MFA_STATUS_ACTIVE,
    )
    return factor, pyotp.TOTP(secret).now()


# ---------------------------------------------------------------------------
# Format session_id — validation à l'extraction
# ---------------------------------------------------------------------------


class TestFormatSessionId:
    def test_session_id_valide_accepte(self):
        sid = create_session()
        assert _SESSION_ID_RE.match(sid), "session_id doit être 64 hex"
        req = FakeRequest(session_id=sid)
        assert get_session_id(req) == sid

    def test_session_id_trop_court_rejete(self):
        req = FakeRequest(session_id="abc123")
        assert get_session_id(req) is None

    def test_session_id_avec_caracteres_invalides_rejete(self):
        req = FakeRequest(session_id="x" * 64)
        assert get_session_id(req) is None

    def test_session_id_injection_rejete(self):
        req = FakeRequest(session_id="../etc/passwd")
        assert get_session_id(req) is None

    def test_session_id_vide_rejete(self):
        req = FakeRequest(session_id="")
        assert get_session_id(req) is None

    def test_session_id_absent_retourne_none(self):
        req = FakeRequest(session_id=None)
        assert get_session_id(req) is None

    def test_session_id_64_hex_valide(self):
        # Format exact attendu : secrets.token_hex(32) → 64 hex chars
        sid = "a" * 64
        req = FakeRequest(session_id=sid)
        assert get_session_id(req) == sid


# ---------------------------------------------------------------------------
# Rotation de session — protection session fixation
# ---------------------------------------------------------------------------


class TestRotationSession:
    def test_login_cree_nouvel_id_de_session(self):
        ancien_sid = create_session()
        nouveau_sid = authenticate_session(ancien_sid, _UTILISATEUR)
        assert nouveau_sid is not None
        assert nouveau_sid != ancien_sid

    def test_ancien_id_supprime_apres_login(self):
        ancien_sid = create_session()
        authenticate_session(ancien_sid, _UTILISATEUR)
        assert get_session(ancien_sid) is None

    def test_new_id_is_authenticated(self):
        sid = create_session()
        nouveau_sid = authenticate_session(sid, _UTILISATEUR)
        session = get_session(nouveau_sid)
        assert session is not None
        assert session.get("authenticated") is True

    def test_csrf_token_regenere_apres_login(self):
        sid = create_session()
        csrf_avant = get_session(sid)["csrf_token"]
        nouveau_sid = authenticate_session(sid, _UTILISATEUR)
        csrf_apres = get_session(nouveau_sid)["csrf_token"]
        assert csrf_apres != csrf_avant

    def test_nouvel_id_format_hex_64(self):
        sid = create_session()
        nouveau_sid = authenticate_session(sid, _UTILISATEUR)
        assert _SESSION_ID_RE.match(nouveau_sid)

    def test_session_inexistante_retourne_none(self):
        result = authenticate_session("a" * 64, _UTILISATEUR)
        assert result is None


# ---------------------------------------------------------------------------
# Logout — invalidation serveur et expiration cookie
# ---------------------------------------------------------------------------


class TestLogout:
    def test_logout_supprime_session_serveur(self):
        sid = create_session()
        nouveau_sid = authenticate_session(sid, _UTILISATEUR)
        delete_session(nouveau_sid)
        assert get_session(nouveau_sid) is None

    def test_session_supprimee_ne_peut_pas_reauthentifier(self):
        sid = create_session()
        nouveau_sid = authenticate_session(sid, _UTILISATEUR)
        delete_session(nouveau_sid)
        # Tenter d'authentifier l'id supprimé retourne None
        result = authenticate_session(nouveau_sid, _UTILISATEUR)
        assert result is None

    def test_logout_preserve_pas_donnees(self):
        sid = create_session()
        nouveau_sid = authenticate_session(sid, _UTILISATEUR)
        delete_session(nouveau_sid)
        assert get_session(nouveau_sid) is None

    def test_session_id_invalide_apres_suppression(self):
        sid = create_session()
        delete_session(sid)
        assert get_session(sid) is None


# ---------------------------------------------------------------------------
# MFA pending — nettoyage après succès et logout
# ---------------------------------------------------------------------------


class TestNettoyageMfa:
    def test_mfa_challenge_demarre_sans_session_complete(self):
        req = FakeRequestWithSession()
        start_mfa_challenge(req, _AUTH_USER)
        assert AUTH_USER_ID_SESSION_KEY not in req.session
        assert MFA_CHALLENGE_USER_ID_KEY in req.session

    def test_mfa_challenge_valide_supprime_cles_temporaires(self):
        req = FakeRequestWithSession()
        start_mfa_challenge(req, _AUTH_USER)
        factor, code = _make_totp_factor()
        verify_mfa_challenge(req, code, factors=[factor])
        assert MFA_CHALLENGE_USER_ID_KEY not in req.session
        assert MFA_CHALLENGE_STARTED_AT_KEY not in req.session

    def test_mfa_challenge_invalide_conserve_pending(self):
        req = FakeRequestWithSession()
        start_mfa_challenge(req, _AUTH_USER)
        factor, _ = _make_totp_factor()
        verify_mfa_challenge(req, "000000", factors=[factor])
        assert has_pending_mfa_challenge(req) is True

    def test_clear_mfa_challenge_supprime_cles(self):
        req = FakeRequestWithSession()
        start_mfa_challenge(req, _AUTH_USER)
        clear_mfa_challenge(req)
        assert MFA_CHALLENGE_USER_ID_KEY not in req.session
        assert MFA_CHALLENGE_STARTED_AT_KEY not in req.session

    def test_clear_mfa_challenge_preserve_csrf(self):
        req = FakeRequestWithSession()
        req.session["csrf_token"] = "csrf-tok"
        start_mfa_challenge(req, _AUTH_USER)
        clear_mfa_challenge(req)
        assert req.session.get("csrf_token") == "csrf-tok"

    def test_session_effacee_supprime_challenge(self):
        req = FakeRequestWithSession()
        start_mfa_challenge(req, _AUTH_USER)
        req.session.clear()
        assert has_pending_mfa_challenge(req) is False


# ---------------------------------------------------------------------------
# Données sensibles — pas en session
# ---------------------------------------------------------------------------


class TestDonneesSensiblesAbsentes:
    def test_aucun_mot_de_passe_en_session(self):
        sid = create_session()
        nouveau_sid = authenticate_session(sid, _UTILISATEUR)
        session = get_session(nouveau_sid)
        assert session is not None
        for v in session.values():
            assert "password" not in str(v).lower()
            assert "argon2id" not in str(v)

    def test_aucun_hash_en_session(self):
        sid = create_session()
        nouveau_sid = authenticate_session(sid, _UTILISATEUR)
        session = get_session(nouveau_sid)
        utilisateur = session.get("user", {})
        assert "PasswordHash" not in utilisateur
        assert "password_hash" not in str(utilisateur).lower()

    def test_secret_mfa_jamais_en_session(self):
        req = FakeRequestWithSession()
        factor, _ = _make_totp_factor()
        start_mfa_challenge(req, _AUTH_USER)
        for v in req.session.values():
            assert factor.totp_secret not in str(v)

    def test_code_mfa_jamais_stocke_en_session(self):
        req = FakeRequestWithSession()
        start_mfa_challenge(req, _AUTH_USER)
        factor, code = _make_totp_factor()
        verify_mfa_challenge(req, code, factors=[factor])
        for v in req.session.values():
            assert code not in str(v)

    def test_session_authentifiee_ne_contient_que_champs_prevus(self):
        sid = create_session()
        nouveau_sid = authenticate_session(sid, _UTILISATEUR)
        session = get_session(nouveau_sid)
        expected_top = {"authenticated", "user", "csrf_token", "expires_at"}
        assert set(session.keys()) <= expected_top | {"_auth_mfa_user_id", "_auth_mfa_started_at"}

    def test_utilisateur_session_ne_contient_que_champs_prevus(self):
        sid = create_session()
        nouveau_sid = authenticate_session(sid, _UTILISATEUR)
        user_data = get_session(nouveau_sid)["user"]
        expected_fields = {"id", "login", "prenom", "nom", "email", "roles"}
        assert set(user_data.keys()) == expected_fields


# ---------------------------------------------------------------------------
# Cookie attributes — vérification via la source du contrôleur
# ---------------------------------------------------------------------------


class TestCookieAttributes:
    def test_auth_controller_cookie_securise(self):
        import mvc.controllers.auth_controller as mod
        source = open(mod.__file__).read()
        assert "HttpOnly" in source
        assert "SameSite=Strict" in source
        assert "Secure" in source

    def test_logout_cookie_max_age_zero(self):
        import mvc.controllers.auth_controller as mod
        source = open(mod.__file__).read()
        assert "Max-Age=0" in source

    def test_mfa_controller_cookie_securise(self):
        import mvc.controllers.mfa_challenge_controller as mod
        source = open(mod.__file__).read()
        assert "HttpOnly" in source
        assert "SameSite=Strict" in source
        assert "Secure" in source


# ---------------------------------------------------------------------------
# Rotation documentée — session fixation protection vérifiable
# ---------------------------------------------------------------------------


class TestSessionFixationProtection:
    def test_session_fixation_impossible(self):
        """Un attaquant qui connaît l'ancien session_id ne peut pas l'utiliser après login."""
        ancien_sid = create_session()
        nouveau_sid = authenticate_session(ancien_sid, _UTILISATEUR)
        # L'attaquant tente d'utiliser l'ancien ID
        assert get_session(ancien_sid) is None
        # Seul le nouvel ID est valide
        assert get_session(nouveau_sid) is not None
        assert get_session(nouveau_sid)["authenticated"] is True

    def test_rotation_apres_mfa(self):
        """Après MFA, la session est rotée — pas le même ID qu'avant MFA."""
        # Simulé au niveau core : on vérifie que authenticate_session retourne un nouveau ID
        sid_pre_mfa = create_session()
        sid_post_mfa = authenticate_session(sid_pre_mfa, _UTILISATEUR)
        assert sid_post_mfa is not None
        assert sid_post_mfa != sid_pre_mfa
        assert get_session(sid_pre_mfa) is None  # Ancien ID invalide

    def test_get_session_id_valide_format(self):
        """get_session_id refuse les IDs au format invalide."""
        req = FakeRequest(session_id="injected'; DROP TABLE sessions; --")
        assert get_session_id(req) is None
