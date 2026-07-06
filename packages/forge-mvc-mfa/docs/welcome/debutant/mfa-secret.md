# Secret TOTP et QR

Objectif : générer le **secret** TOTP et l'URI `otpauth://` que lit une application d'authentification.

**Ce que vous allez apprendre :** `generate_totp_secret` produit un secret base32 ; `totp_provisioning_uri` construit l'URI `otpauth://` (ce que code un QR) à présenter à l'utilisateur lors de l'enrôlement.

Deuxième palier du **niveau débutant** de la progression MFA.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-mfa` installé (palier « Installation »).
    Aucune clé de chiffrement requise ici : le secret n'est pas encore stocké.

## Ce que ce starter montre

- `generate_totp_secret()` → un secret base32 ;
- `totp_provisioning_uri(secret, account, issuer)` → l'URI `otpauth://` ;
- une transformation **pure** (rien n'est stocké).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_mfa.generate_totp_secret` | Produire un secret TOTP base32. | MFA |
| `forge_mvc_mfa.totp_provisioning_uri` | Construire l'URI `otpauth://` (QR). | MFA |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/mfa-secret` : un secret et son URI s'affichent.
Rechargez pour en générer un nouveau.

## Le contrôleur

```python
# mvc/controllers/mfa_secret_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_mfa import generate_totp_secret, totp_provisioning_uri


class MfaSecretController(BaseController):
    """Starter pédagogique : générer un secret TOTP et son URI de provisioning."""

    @staticmethod
    def index(request: Request) -> Response:
        secret = generate_totp_secret()
        uri = totp_provisioning_uri(secret, account_name="demo@forge.example", issuer_name="Forge Demo")
        return BaseController.render(
            "mfa_secret/index.html",
            context={"secret": secret, "uri": uri},
            request=request,
        )
```

## La vue

```html
<!-- mvc/views/mfa_secret/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Secret TOTP et QR - Forge</title>
</head>
<body>
  <h1>Secret TOTP et QR</h1>

  <p>Secret base32 (à scanner une seule fois dans l'application d'authentification) :</p>
  <p><code>{{ secret }}</code></p>

  <p>URI de provisioning <code>otpauth://</code> (ce que code un QR) :</p>
  <p><code>{{ uri }}</code></p>

  <p>Rechargez la page pour générer un nouveau secret. Un secret réel n'est montré
  à l'utilisateur <strong>qu'une seule fois</strong>, à l'enrôlement.</p>
</body>
</html>
```

## La route

```python
# mvc/routes.py
from mvc.controllers.mfa_secret_controller import MfaSecretController

with router.group("", public=True) as public:
    public.add("GET", "/mfa-secret", MfaSecretController.index, name="mfa_secret_index")
```

### Comprendre ce code

- Le **secret** est partagé une seule fois entre serveur et application d'authentification ; ensuite, les deux calculent le même code à partir de l'heure.
- L'URI `otpauth://` encode secret + compte + émetteur : l'utilisateur la scanne en QR.
- Rien n'est persisté ici : la génération est une **primitive pure**.

## À retenir

- L'enrôlement TOTP commence par un **secret** partagé.
- `otpauth://` est le format standard lu par les applications d'authentification.
- Un secret réel n'est montré **qu'une seule fois**.

## Après ce starter

Le secret est généré.
La suite : vérifier un code calculé à partir de lui.

[Vérifier un code TOTP](mfa-verify.md)
