# Secret chiffré au repos

Objectif : ne **jamais** stocker un secret TOTP en clair — le chiffrer au repos avec
`FORGE_MFA_SECRET_KEY`.

**Ce que vous allez apprendre :** `encrypt_totp_secret` chiffre un secret (préfixe
`enc:`) via Fernet ; `decrypt_totp_secret` le déchiffre au moment de vérifier un
code ; `validate_mfa_secret_key_config` contrôle la clé.

Troisième palier du **niveau avancé** de la progression MFA.

!!! note "Module opt-in — clé requise"
    Ce starter suppose `forge-mvc-mfa` installé et `FORGE_MFA_SECRET_KEY` configurée.
    Sans clé, la page reste **pédagogique**.

## Ce que ce starter montre

- l'état de la clé via `validate_mfa_secret_key_config` ;
- `encrypt_totp_secret(raw)` → valeur `enc:…` (ce qui est stocké) ;
- `decrypt_totp_secret(enc)` → aller-retour identique.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_mfa.encrypt_totp_secret` | Chiffrer un secret TOTP (Fernet). | [MFA](../../../reference/api.md) |
| `forge_mvc_mfa.decrypt_totp_secret` | Déchiffrer un secret stocké. | [MFA](../../../reference/api.md) |
| `forge_mvc_mfa.validate_mfa_secret_key_config` | Contrôler la configuration de la clé. | [MFA](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/mfa-crypto` : saisissez un secret, observez sa version
chiffrée `enc:…` et l'aller-retour.

## Le contrôleur (extrait)

```python
# mvc/controllers/mfa_crypto_controller.py
from forge_mvc_mfa import decrypt_totp_secret, encrypt_totp_secret

encrypted = encrypt_totp_secret(raw)      # "enc:..." — stocké en base
decrypted = decrypt_totp_secret(encrypted)  # == raw, au moment de vérifier
```

### Comprendre ce code

- Seule la valeur préfixée `enc:` est stockée ; la **clé reste hors base**
  (`FORGE_MFA_SECRET_KEY`). Une base volée ne livre pas les secrets.
- `create_totp_factor` applique déjà ce chiffrement : `factor.totp_secret` est `enc:…`.
- `validate_mfa_secret_key_config` doit être appelé au démarrage pour échouer **tôt**
  si la clé manque.

## À retenir

- Un secret TOTP est **chiffré au repos**, jamais en clair.
- La clé Fernet (`FORGE_MFA_SECRET_KEY`) vit hors base.
- Valider la clé au démarrage évite des surprises en production.

## Après ce starter

Vous avez parcouru toute la progression MFA : mécaniques, flux, durcissement.

[Bilan du niveau avancé](bilan.md)
