# Revalidation (step-up)

Objectif : exiger une **MFA récente** avant une action sensible, même déjà connecté, le *step-up*.

**Ce que vous allez apprendre :** `mark_mfa_revalidated` enregistre une revalidation en session ; `has_recent_mfa_revalidation` dit si elle est encore fraîche.
Le décorateur `require_recent_mfa` s'appuie sur ces briques pour protéger une route.

Premier palier du **niveau avancé** de la progression MFA.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-mfa` installé.
    Démo **en session** (utilisateur démo), aucune clé requise.

## Ce que ce starter montre

- `has_recent_mfa_revalidation(request, user_id)` → l'état courant ;
- `mark_mfa_revalidated(request, user_id)` → enregistre une revalidation ;
- le principe du décorateur `require_recent_mfa`.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_mfa.mark_mfa_revalidated` | Enregistrer une revalidation MFA en session. | MFA |
| `forge_mvc_mfa.has_recent_mfa_revalidation` | Dire si la revalidation est encore récente. | MFA |
| `forge_mvc_mfa.require_recent_mfa` | Décorateur protégeant une action sensible. | MFA |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/mfa-revalidation` : l'état « MFA récente »
passe à oui après avoir cliqué « Revalider ».

## Le contrôleur

```python
# mvc/controllers/mfa_revalidation_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController
from core.security.session import get_session, get_session_id
from core.sessions.manager import get_session_store

from forge_mvc_mfa import has_recent_mfa_revalidation, mark_mfa_revalidated

_DEMO_USER_ID = 1
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
    response = BaseController.render("mfa_revalidation/index.html", context=context, request=request)
    response.headers["Set-Cookie"] = _COOKIE.format(sid=sid)
    return response


def _is_recent(request) -> bool:
    try:
        return bool(has_recent_mfa_revalidation(request, _DEMO_USER_ID))
    except Exception:
        return False


class MfaRevalidationController(BaseController):
    """Starter pédagogique : exiger une MFA récente avant une action sensible."""

    @staticmethod
    def index(request: Request) -> Response:
        _, sid, _ = _ensure_session(request)
        return _render(request, sid, {
            "csrf_token": BaseController.csrf_token(request),
            "recent": _is_recent(request),
        })

    @staticmethod
    def revalidate(request: Request) -> Response:
        _, sid, _ = _ensure_session(request)
        context = {"csrf_token": BaseController.csrf_token(request)}
        try:
            mark_mfa_revalidated(request, _DEMO_USER_ID)
            context["marked"] = True
        except Exception as exc:
            context["error"] = f"Revalidation impossible : {exc}"
        context["recent"] = _is_recent(request)
        return _render(request, sid, context)
```

## La vue

```html
<!-- mvc/views/mfa_revalidation/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Revalidation (step-up) - Forge</title>
</head>
<body>
  <h1>Revalidation (step-up)</h1>

  {% if error %}
  <p data-level="error"><strong>{{ error }}</strong></p>
  {% endif %}
  {% if marked %}
  <p data-level="success">Revalidation enregistrée.</p>
  {% endif %}

  <p>MFA récente : <strong>{% if recent %}oui{% else %}non{% endif %}</strong></p>

  <form method="post" action="/mfa-revalidation">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <button type="submit">Revalider maintenant</button>
  </form>

  <p>Une action sensible décorée par <code>require_recent_mfa</code> n'est autorisée
  que si <code>has_recent_mfa_revalidation</code> renvoie vrai.</p>
</body>
</html>
```

## La route

```python
# mvc/routes/__init__.py
from mvc.controllers.mfa_revalidation_controller import MfaRevalidationController

with router.group("", public=True) as public:
    public.add("GET", "/mfa-revalidation", MfaRevalidationController.index, name="mfa_revalidation_index")
    public.add("POST", "/mfa-revalidation", MfaRevalidationController.revalidate, name="mfa_revalidation_mark")
```

### Comprendre ce code

- Le *step-up* protège les actions à risque (changer le mot de passe, supprimer le compte) même au sein d'une session déjà authentifiée.
- La fraîcheur expire (`max_age_minutes`) : passé le délai, on redemande une MFA.
- `require_recent_mfa` est le **décorateur** qui applique cette règle à une route.

## À retenir

- Le step-up exige une MFA **récente** avant une action sensible.
- `mark_mfa_revalidated` / `has_recent_mfa_revalidation` sont les briques.
- `require_recent_mfa` les applique de façon déclarative à une route.

## Après ce starter

La suite : empêcher le rejeu d'un même code TOTP.

[Anti-rejeu TOTP](mfa-replay.md)
