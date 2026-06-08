"""Garde-fou SEC-AUTH-SESSION-FIXATION-001.

`login_user` ne régénère pas l'identifiant de session (il n'a pas accès à la
réponse HTTP). Pour fermer le vecteur de fixation de session, le contrat exige
que l'appelant régénère l'identifiant et réémette le cookie juste après. Ce
garde-fou verrouille deux choses :

1. la docstring de `login_user` documente explicitement cette exigence ;
2. le contrôleur de référence applique bien le flux
   `login_user` -> `regenerate` -> `set_session_cookie(nouvel_id)`.

Test documentaire : il lit du texte et du source, il n'exécute aucun service.
"""
from __future__ import annotations

import inspect
from pathlib import Path

from core.auth import session as session_mod

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUTH_CONTROLLER = PROJECT_ROOT / "mvc" / "controllers" / "auth_controller.py"


def test_login_user_docstring_documente_la_rotation():
    doc = (inspect.getdoc(session_mod.login_user) or "").lower()
    assert "fixation" in doc
    assert "regenerate_session" in doc or "régénér" in doc


def test_controleur_reference_rote_la_session_apres_login_user():
    src = AUTH_CONTROLLER.read_text(encoding="utf-8")
    assert "login_user(request" in src

    i_login = src.index("login_user(request")
    i_regen = src.index("regenerate(", i_login)
    i_cookie = src.index("set_session_cookie(", i_regen)
    assert i_login < i_regen < i_cookie, (
        "le flux de login canonique doit régénérer l'identifiant de session "
        "puis réémettre le cookie après login_user (anti-fixation)"
    )
