# Codes de récupération

Objectif : générer un lot de **codes de récupération** à usage unique, et en consommer un quand le TOTP est indisponible.

**Ce que vous allez apprendre :** `create_recovery_codes` génère un lot (montré **une fois**, stocké **haché**) ; `verify_recovery_code` confronte un code à son hash ; `consume_recovery_code` le marque utilisé (usage **unique**).

Troisième palier du **niveau intermédiaire** de la progression MFA.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-mfa` installé.
    **Aucune clé de chiffrement requise** ici : les codes sont **hachés**, pas chiffrés.
    Démo en session.

## Ce que ce starter montre

- `create_recovery_codes(user_id)` → `RecoveryCodesSetup` (codes bruts + records) ;
- les codes affichés **une seule fois**, les records (hachés) gardés en session ;
- `verify_recovery_code` + `consume_recovery_code` pour utiliser un code.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_mfa.create_recovery_codes` | Générer un lot de codes (bruts + records hachés). | MFA |
| `forge_mvc_mfa.verify_recovery_code` | Confronter un code à son hash. | MFA |
| `forge_mvc_mfa.consume_recovery_code` | Marquer un code utilisé (usage unique). | MFA |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/mfa-recovery` : un lot de codes s'affiche ; saisissez-en un pour le consommer.

## Le contrôleur

```python
# mvc/controllers/mfa_recovery_controller.py
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
```

## La vue

```html
<!-- mvc/views/mfa_recovery/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Codes de récupération - Forge</title>
</head>
<body>
  <h1>Codes de récupération</h1>

  {% if codes %}
  <p>Codes générés (à conserver hors ligne, montrés <strong>une seule fois</strong>) :</p>
  <ul>
    {% for code in codes %}<li><code>{{ code }}</code></li>{% endfor %}
  </ul>
  {% endif %}

  {% if consumed is defined and consumed %}
  <p data-level="success">✓ Code de récupération consommé (usage unique).</p>
  {% elif consumed is defined and not consumed %}
  <p data-level="error">✗ Code inconnu ou déjà utilisé.</p>
  {% endif %}

  <form method="post" action="/mfa-recovery">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <label>Code de récupération
      <input type="text" name="code" required>
    </label>
    <button type="submit">Consommer</button>
  </form>

  <p>Les codes sont stockés <strong>hachés</strong> (jamais en clair). En production,
  on les persiste dans <code>auth_mfa_recovery_codes</code>.</p>
</body>
</html>
```

## La route

```python
# mvc/routes.py
from mvc.controllers.mfa_recovery_controller import MfaRecoveryController

with router.group("", public=True) as public:
    public.add("GET", "/mfa-recovery", MfaRecoveryController.index, name="mfa_recovery_index")
    public.add("POST", "/mfa-recovery", MfaRecoveryController.consume, name="mfa_recovery_consume")
```

### Comprendre ce code

- Les codes bruts sont montrés **une seule fois** ; seul leur **hash** est conservé (comme un mot de passe).
- `verify_recovery_code` utilise une comparaison à temps constant (anti-timing).
- `consume_recovery_code` garantit l'**usage unique** : un code consommé ne repasse pas.

## À retenir

- Les codes de récupération sauvent l'accès quand le TOTP est perdu.
- Stockés **hachés**, montrés une seule fois, **à usage unique**.
- En production, persistés dans `auth_mfa_recovery_codes`.

## Après ce starter

Vous maîtrisez le flux MFA.
La suite (avancé) : le durcissement.

[Bilan du niveau intermédiaire](bilan.md)
