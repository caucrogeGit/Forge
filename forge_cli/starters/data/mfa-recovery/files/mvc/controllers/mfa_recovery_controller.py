"""Starter Codes de récupération — palier 3 du niveau intermédiaire (welcome-mfa).

Ticket : STARTER-MFA-RECOVERY-001.

Quand l'appareil TOTP est perdu, les **codes de récupération** sauvent l'accès.
``create_recovery_codes`` génère un lot (montré **une seule fois**, stocké **haché**) ;
``verify_recovery_code`` confronte un code à son hash ; ``consume_recovery_code`` le
marque utilisé (usage **unique**).

  ``index``   — `GET  /mfa-recovery` : génère un lot, l'affiche une fois, garde les
                enregistrements (hachés) en session.
  ``consume`` — `POST /mfa-recovery` : consomme un code saisi.

Démo **en session**, **aucune clé de chiffrement requise** (les codes sont hachés,
pas chiffrés). Aucune base de données.
"""
import dataclasses

from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController
from core.security.session import get_session, get_session_id
from core.sessions.manager import get_session_store

from forge_mvc_mfa import (
    AuthMfaRecoveryCode,
    consume_recovery_code,
    create_recovery_codes,
    verify_recovery_code,
)

_DEMO_USER_ID = 1
_SESSION_KEY = "mfa_recovery_records"
_COOKIE = "session_id={sid}; Path=/; HttpOnly; SameSite=Strict; Secure"


def _ensure_session(request):
    store = get_session_store()
    sid = get_session_id(request)
    session = get_session(sid) if sid else None
    if not session:
        sid = store.create()
        session = get_session(sid)
    return store, sid, session


def _render(request, sid, context):
    response = BaseController.render("mfa_recovery/index.html", context=context, request=request)
    response.headers["Set-Cookie"] = _COOKIE.format(sid=sid)
    return response


class MfaRecoveryController(BaseController):
    """Starter pédagogique : générer et consommer des codes de récupération."""

    @staticmethod
    def index(request: Request) -> Response:
        store, sid, session = _ensure_session(request)
        setup = create_recovery_codes(_DEMO_USER_ID)
        store.set(sid, {**session, _SESSION_KEY: [dataclasses.asdict(r) for r in setup.code_records]})
        return _render(request, sid, {
            "csrf_token": BaseController.csrf_token(request),
            "codes": list(setup.raw_codes),
        })

    @staticmethod
    def consume(request: Request) -> Response:
        store, sid, session = _ensure_session(request)
        context = {"csrf_token": BaseController.csrf_token(request)}
        records = (session or {}).get(_SESSION_KEY) or []
        code = (request.form("code") or "").strip()
        for data in records:
            record = AuthMfaRecoveryCode(**data)
            if verify_recovery_code(code, record.code_hash):
                consumed = consume_recovery_code(code, record)
                context["consumed"] = consumed is not None
                break
        else:
            context["consumed"] = False
        return _render(request, sid, context)
