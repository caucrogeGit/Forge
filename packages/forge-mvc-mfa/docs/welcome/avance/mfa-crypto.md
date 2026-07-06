# Secret chiffré au repos

Objectif : ne **jamais** stocker un secret TOTP en clair : le chiffrer au repos avec `FORGE_MFA_SECRET_KEY`.

**Ce que vous allez apprendre :** `encrypt_totp_secret` chiffre un secret (préfixe `enc:`) via Fernet ; `decrypt_totp_secret` le déchiffre au moment de vérifier un code ; `validate_mfa_secret_key_config` contrôle la clé.

Troisième palier du **niveau avancé** de la progression MFA.

!!! note "Module opt-in, clé requise"
    Ce starter suppose `forge-mvc-mfa` installé et `FORGE_MFA_SECRET_KEY` configurée.
    Sans clé, la page reste **pédagogique**.

## Ce que ce starter montre

- l'état de la clé via `validate_mfa_secret_key_config` ;
- `encrypt_totp_secret(raw)` → valeur `enc:…` (ce qui est stocké) ;
- `decrypt_totp_secret(enc)` → aller-retour identique.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_mfa.encrypt_totp_secret` | Chiffrer un secret TOTP (Fernet). | MFA |
| `forge_mvc_mfa.decrypt_totp_secret` | Déchiffrer un secret stocké. | MFA |
| `forge_mvc_mfa.validate_mfa_secret_key_config` | Contrôler la configuration de la clé. | MFA |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/mfa-crypto` : saisissez un secret, observez sa version chiffrée `enc:…` et l'aller-retour.

## Le contrôleur

```python
# mvc/controllers/mfa_crypto_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_mfa import (
    decrypt_totp_secret,
    encrypt_totp_secret,
    generate_totp_secret,
    validate_mfa_secret_key_config,
)


def _key_state() -> str:
    try:
        validate_mfa_secret_key_config()
        return "configurée"
    except Exception as exc:
        return f"non configurée ({type(exc).__name__})"


class MfaCryptoController(BaseController):
    """Starter pédagogique : chiffrer/déchiffrer un secret TOTP au repos."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "mfa_crypto/index.html",
            context={"csrf_token": BaseController.csrf_token(request), "key_state": _key_state()},
            request=request,
        )

    @staticmethod
    def demo(request: Request) -> Response:
        raw = (request.form("secret") or "").strip() or generate_totp_secret()
        context = {"csrf_token": BaseController.csrf_token(request), "key_state": _key_state(), "raw": raw}
        try:
            encrypted = encrypt_totp_secret(raw)
            decrypted = decrypt_totp_secret(encrypted)
            context["encrypted"] = encrypted
            context["roundtrip_ok"] = decrypted == raw
        except Exception as exc:
            context["error"] = f"Chiffrement impossible (clé MFA ?) : {exc}"
        return BaseController.render("mfa_crypto/index.html", context=context, request=request)
```

## La vue

```html
<!-- mvc/views/mfa_crypto/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Secret chiffré au repos - Forge</title>
</head>
<body>
  <h1>Secret chiffré au repos</h1>

  <p>Clé <code>FORGE_MFA_SECRET_KEY</code> : <strong>{{ key_state }}</strong></p>

  {% if error %}
  <p data-level="error"><strong>{{ error }}</strong></p>
  {% endif %}

  {% if encrypted %}
  <ul>
    <li>Secret en clair : <code>{{ raw }}</code></li>
    <li>Chiffré (stocké en base) : <code>{{ encrypted }}</code></li>
    <li>Aller-retour déchiffré identique : <strong>{% if roundtrip_ok %}oui{% else %}non{% endif %}</strong></li>
  </ul>
  {% endif %}

  <form method="post" action="/mfa-crypto">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <label>Secret à chiffrer (vide = généré)
      <input type="text" name="secret">
    </label>
    <button type="submit">Chiffrer puis déchiffrer</button>
  </form>

  <p>Seule la valeur préfixée <code>enc:</code> est stockée ; la clé reste hors base.</p>
</body>
</html>
```

## La route

```python
# mvc/routes.py
from mvc.controllers.mfa_crypto_controller import MfaCryptoController

with router.group("", public=True) as public:
    public.add("GET", "/mfa-crypto", MfaCryptoController.index, name="mfa_crypto_index")
    public.add("POST", "/mfa-crypto", MfaCryptoController.demo, name="mfa_crypto_demo")
```

### Comprendre ce code

- Seule la valeur préfixée `enc:` est stockée ; la **clé reste hors base** (`FORGE_MFA_SECRET_KEY`).
  Une base volée ne livre pas les secrets.
- `create_totp_factor` applique déjà ce chiffrement : `factor.totp_secret` est `enc:…`.
- `validate_mfa_secret_key_config` doit être appelé au démarrage pour échouer **tôt** si la clé manque.

## À retenir

- Un secret TOTP est **chiffré au repos**, jamais en clair.
- La clé Fernet (`FORGE_MFA_SECRET_KEY`) vit hors base.
- Valider la clé au démarrage évite des surprises en production.

## Après ce starter

Vous avez parcouru toute la progression MFA : mécaniques, flux, durcissement.

[Bilan du niveau avancé](bilan.md)
