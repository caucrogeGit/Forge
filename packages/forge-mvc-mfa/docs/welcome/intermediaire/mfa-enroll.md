# Enrôler un facteur TOTP

Objectif : créer un facteur TOTP **pending**, puis le **confirmer** : l'enrôlement en deux temps.

**Ce que vous allez apprendre :** `create_totp_factor` crée un facteur pending dont le secret est déjà **chiffré au repos** ; `confirm_totp_factor` l'active après vérification d'un premier code (preuve que l'utilisateur a enregistré le secret).

Premier palier du **niveau intermédiaire** de la progression MFA.

!!! note "Module opt-in, clé requise"
    Ce starter suppose `forge-mvc-mfa` installé et `FORGE_MFA_SECRET_KEY` configurée.
    Sans clé, la page reste **pédagogique**.

## Ce que ce starter montre

- `create_totp_factor(user_id)` → un `TotpSetup` (secret, facteur pending, URI) ;
- le facteur pending gardé **en session** pour la démo ;
- `confirm_totp_factor(factor, code)` → facteur actif.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_mfa.create_totp_factor` | Créer un facteur TOTP pending (secret chiffré). | MFA |
| `forge_mvc_mfa.confirm_totp_factor` | Activer le facteur après vérification d'un code. | MFA |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/mfa-enroll` : un secret/URI s'affiche, saisissez un code valide pour confirmer le facteur.

## Le contrôleur

```python
# mvc/controllers/mfa_enroll_controller.py
import dataclasses

from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController
from core.security.session import get_session, get_session_id
from core.sessions.manager import get_session_store

from forge_mvc_mfa import AuthMfaFactor, confirm_totp_factor, create_totp_factor

_DEMO_USER_ID = 1
_SESSION_KEY = "mfa_enroll_pending_factor"
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
    response = BaseController.render("mfa_enroll/index.html", context=context, request=request)
    response.headers["Set-Cookie"] = _COOKIE.format(sid=sid)
    return response


class MfaEnrollController(BaseController):
    """Starter pédagogique : enrôler et confirmer un facteur TOTP."""

    @staticmethod
    def index(request: Request) -> Response:
        store, sid, session = _ensure_session(request)
        context = {"csrf_token": BaseController.csrf_token(request)}
        try:
            setup = create_totp_factor(_DEMO_USER_ID, account_name="demo@forge.example")
        except Exception as exc:
            context["error"] = f"Enrôlement impossible (clé MFA ?) : {exc}"
            return _render(request, sid, context)
        store.set(sid, {**session, _SESSION_KEY: dataclasses.asdict(setup.factor)})
        context["secret"] = setup.secret
        context["uri"] = setup.provisioning_uri
        return _render(request, sid, context)

    @staticmethod
    def confirm(request: Request) -> Response:
        store, sid, session = _ensure_session(request)
        context = {"csrf_token": BaseController.csrf_token(request)}
        data = (session or {}).get(_SESSION_KEY)
        code = (request.form("code") or "").strip()
        if not data:
            context["error"] = "Démarrez d'abord l'enrôlement (rechargez la page)."
            return _render(request, sid, context)
        active = confirm_totp_factor(AuthMfaFactor(**data), code)
        if active is None:
            context["error"] = "Code invalide - facteur non confirmé."
        else:
            context["confirmed"] = True
            store.set(sid, {k: v for k, v in session.items() if k != _SESSION_KEY})
        return _render(request, sid, context)
```

## La vue

```html
<!-- mvc/views/mfa_enroll/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Enrôler un facteur TOTP - Forge</title>
</head>
<body>
  <h1>Enrôler un facteur TOTP</h1>

  {% if error %}
  <p data-level="error"><strong>{{ error }}</strong></p>
  {% endif %}
  {% if confirmed %}
  <p data-level="success">✓ Facteur TOTP confirmé et actif.</p>
  {% endif %}

  {% if secret %}
  <p>Secret (à enregistrer une seule fois) : <code>{{ secret }}</code></p>
  <p>URI : <code>{{ uri }}</code></p>
  {% endif %}

  <form method="post" action="/mfa-enroll">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <label>Code de confirmation
      <input type="text" name="code" inputmode="numeric" pattern="[0-9]*" required>
    </label>
    <button type="submit">Confirmer le facteur</button>
  </form>

  <p>Le facteur <em>pending</em> est gardé en session pour la démonstration. Dans une
  vraie application, on le persiste en base (table <code>auth_mfa_factors</code>).</p>
</body>
</html>
```

## La route

```python
# mvc/routes.py
from mvc.controllers.mfa_enroll_controller import MfaEnrollController

with router.group("", public=True) as public:
    public.add("GET", "/mfa-enroll", MfaEnrollController.index, name="mfa_enroll_index")
    public.add("POST", "/mfa-enroll", MfaEnrollController.confirm, name="mfa_enroll_confirm")
```

### Comprendre ce code

- `create_totp_factor` **ne touche pas la base** : il retourne des objets.
  La **persistance est le job de l'application** : ici on simule avec la session.
- Le secret du facteur (`factor.totp_secret`) est déjà **chiffré** (`enc:…`).
- La confirmation prouve que l'utilisateur a bien enregistré le secret avant de l'activer.

## À retenir

- Enrôlement = créer **pending** puis **confirmer** avec un code.
- Le package fournit les objets ; l'application les persiste (`auth_mfa_factors`).
- Le secret est chiffré au repos dès la création.

## Après ce starter

Le facteur est actif.
La suite : le second facteur au moment de la connexion.

[Challenge de connexion](mfa-challenge.md)
