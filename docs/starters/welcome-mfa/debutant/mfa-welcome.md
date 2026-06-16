# Bonjour Forge MFA

Objectif : premier contact avec le module **opt-in** `forge-mvc-mfa`.

**Ce que vous allez apprendre :** vérifier que le module répond et **inspecter ses
briques** : facteurs (`TOTP`, `recovery`), statuts (`pending`/`active`/`disabled`),
et la présence de la clé de chiffrement `FORGE_MFA_SECRET_KEY` (sans la révéler).

Premier palier du **niveau débutant** de la progression MFA
([vue d'ensemble des starters](../../index.md)).

!!! note "Module opt-in"
    Ce parcours décortique **chaque brique** MFA isolément, pour comprendre
    chaque API avant de la câbler dans votre propre flux Auth. Installé via
    `pip install --pre forge-mvc-mfa` (palier « Installation »).

## Ce que ce starter montre

- une route texte de **premier contact** (`GET /mfa-welcome`) ;
- les facteurs et statuts MFA + l'état de la clé (`GET /mfa-welcome/inspect`).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_mfa.MFA_FACTOR_TOTP` / `MFA_FACTOR_RECOVERY` | Les deux types de facteurs. | [MFA](../../../reference/api.md) |
| `forge_mvc_mfa.validate_mfa_secret_key_config` | Vérifier que la clé de chiffrement est configurée. | [MFA](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/mfa-welcome` puis `/mfa-welcome/inspect`.

## Le contrôleur

```python
# mvc/controllers/mfa_welcome_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_mfa import (
    MFA_FACTOR_RECOVERY,
    MFA_FACTOR_TOTP,
    MFA_STATUS_ACTIVE,
    MFA_STATUS_DISABLED,
    MFA_STATUS_PENDING,
    validate_mfa_secret_key_config,
)


def _capabilities() -> dict:
    """Décrit les facteurs/statuts MFA et l'état de la clé de chiffrement."""
    try:
        validate_mfa_secret_key_config()
        secret_key = "configurée"
    except Exception as exc:  # clé absente, invalide, ou placeholder
        secret_key = f"non configurée ({type(exc).__name__})"
    return {
        "factors": [MFA_FACTOR_TOTP, MFA_FACTOR_RECOVERY],
        "statuses": [MFA_STATUS_PENDING, MFA_STATUS_ACTIVE, MFA_STATUS_DISABLED],
        "secret_key": secret_key,
    }


class MfaWelcomeController(BaseController):
    """Starter pédagogique : premier contact avec Forge MFA."""

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge MFA")

    @staticmethod
    def inspect(request: Request) -> Response:
        return Response.json(_capabilities())
```

## La route

```python
# mvc/routes.py
from mvc.controllers.mfa_welcome_controller import MfaWelcomeController

with router.group("", public=True) as public:
    public.add("GET", "/mfa-welcome", MfaWelcomeController.index, name="mfa_welcome_index")
    public.add("GET", "/mfa-welcome/inspect", MfaWelcomeController.inspect, name="mfa_welcome_inspect")
```

### Comprendre ce code

- MFA repose sur **deux facteurs** : un code TOTP (application d'authentification) et
  des **codes de récupération** (secours).
- Un facteur passe par trois **statuts** : `pending` (créé), `active` (confirmé),
  `disabled`.
- La clé `FORGE_MFA_SECRET_KEY` chiffre les secrets au repos : on vérifie sa présence
  sans jamais l'exposer.

## À retenir

- MFA = TOTP + codes de récupération, avec un cycle de statuts explicite.
- Les secrets sont **chiffrés au repos** (clé Fernet obligatoire pour l'enrôlement).
- Ce parcours montre chaque brique isolée, à câbler ensuite dans votre flux Auth.

## Après ce starter

Premier contact établi. La suite : générer un secret TOTP.

[Secret TOTP et QR](mfa-secret.md)
