# Challenge de connexion

Objectif : le **second facteur** à la connexion : ouvrir un challenge après le mot
de passe, puis le valider.

**Ce que vous allez apprendre :** `start_mfa_challenge` ouvre un challenge
**temporaire en session** (sans connecter l'utilisateur) ; `verify_mfa_challenge`
confronte le code (TOTP ou récupération) au challenge, avec tentatives limitées.

Deuxième palier du **niveau intermédiaire** de la progression MFA.

!!! note "Module opt-in, clé requise"
    Ce starter suppose `forge-mvc-mfa` installé et `FORGE_MFA_SECRET_KEY` configurée.
    La démo travaille **en session** avec un utilisateur démo.

## Ce que ce starter montre

- `start_mfa_challenge(request, user)` → challenge ouvert en session ;
- `verify_mfa_challenge(request, code, factors)` → succès / échec ;
- un facteur démo gardé en session.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_mfa.start_mfa_challenge` | Ouvrir un challenge MFA temporaire en session. | [MFA](../../../reference/api.md) |
| `forge_mvc_mfa.verify_mfa_challenge` | Vérifier un code contre le challenge. | [MFA](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/mfa-challenge` : un secret démo s'affiche ; saisissez
un code pour valider le challenge.

## Le contrôleur

```python
# mvc/controllers/mfa_challenge_controller.py
import dataclasses

from core.auth.user import AuthUser
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController
from core.security.session import get_session, get_session_id
from core.sessions.manager import get_session_store

from forge_mvc_mfa import (
    MFA_STATUS_ACTIVE,
    AuthMfaFactor,
    create_totp_factor,
    start_mfa_challenge,
    verify_mfa_challenge,
)

_DEMO_USER = AuthUser(id=1, email="demo@forge.example", password_hash="(démo)", is_active=True)
_SESSION_KEY = "mfa_challenge_factor"
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
    response = BaseController.render("mfa_challenge/index.html", context=context, request=request)
    response.headers["Set-Cookie"] = _COOKIE.format(sid=sid)
    return response


class MfaChallengeController(BaseController):
    """Starter pédagogique : ouvrir et vérifier un challenge MFA de connexion."""

    @staticmethod
    def index(request: Request) -> Response:
        store, sid, session = _ensure_session(request)
        context = {"csrf_token": BaseController.csrf_token(request)}
        try:
            setup = create_totp_factor(_DEMO_USER.id, account_name=_DEMO_USER.email)
            factor_data = dataclasses.asdict(setup.factor)
            factor_data["status"] = MFA_STATUS_ACTIVE
            store.set(sid, {**session, _SESSION_KEY: factor_data})
            start_mfa_challenge(request, _DEMO_USER)
            context["secret"] = setup.secret
        except Exception as exc:
            context["error"] = f"Challenge indisponible (clé MFA / session ?) : {exc}"
        return _render(request, sid, context)

    @staticmethod
    def verify(request: Request) -> Response:
        store, sid, session = _ensure_session(request)
        context = {"csrf_token": BaseController.csrf_token(request)}
        data = (session or {}).get(_SESSION_KEY)
        code = (request.form("code") or "").strip()
        if not data:
            context["error"] = "Ouvrez d'abord le challenge (rechargez la page)."
            return _render(request, sid, context)
        try:
            result = verify_mfa_challenge(request, code, [AuthMfaFactor(**data)])
        except Exception as exc:
            context["error"] = f"Vérification impossible : {exc}"
            return _render(request, sid, context)
        if result is None:
            context["error"] = "Code invalide ou challenge expiré."
        else:
            context["verified"] = result.method
        return _render(request, sid, context)
```

## La vue

```html
<!-- mvc/views/mfa_challenge/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Challenge de connexion - Forge</title>
</head>
<body>
  <h1>Challenge de connexion</h1>

  {% if error %}
  <p data-level="error"><strong>{{ error }}</strong></p>
  {% endif %}
  {% if verified %}
  <p data-level="success">✓ Challenge validé (méthode : {{ verified }}).</p>
  {% endif %}

  {% if secret %}
  <p>Secret du facteur démo : <code>{{ secret }}</code> - générez un code dans une
  application d'authentification.</p>
  {% endif %}

  <form method="post" action="/mfa-challenge">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <label>Code (TOTP ou récupération)
      <input type="text" name="code" required>
    </label>
    <button type="submit">Valider le challenge</button>
  </form>

  <p>Dans une vraie application, le challenge s'ouvre <strong>après</strong> le mot de
  passe ; les facteurs proviennent de la base, pas de la session.</p>
</body>
</html>
```

## La route

```python
# mvc/routes.py
from mvc.controllers.mfa_challenge_controller import MfaChallengeController

with router.group("", public=True) as public:
    public.add("GET", "/mfa-challenge", MfaChallengeController.index, name="mfa_challenge_index")
    public.add("POST", "/mfa-challenge", MfaChallengeController.verify, name="mfa_challenge_verify")
```

### Comprendre ce code

- Le challenge **ne connecte pas** : il mémorise « cet utilisateur a passé le 1er
  facteur, en attente du 2e ». La connexion réelle suit la validation.
- `verify_mfa_challenge` accepte un code **TOTP ou de récupération**, et limite les
  tentatives (anti-bruteforce).
- Dans une vraie application, le challenge suit le login et les facteurs viennent de
  la base ; ici on simule en session.

## À retenir

- Le challenge est l'étape **entre** mot de passe et connexion effective.
- Il vit **en session**, temporaire, à tentatives limitées.
- TOTP ou code de récupération valident indifféremment le challenge.

## Après ce starter

Le 2e facteur fonctionne. La suite : les codes de récupération en secours.

[Codes de récupération](mfa-recovery.md)
