# Le chiffrement des secrets MFA dans Forge

Ce document décrit le chiffrement au repos du secret TOTP et la validation de la clé de chiffrement.

Le fichier de code correspondant est `forge_mvc_mfa/secret_crypto.py`.

## 1. À quoi sert ce module ?

Un secret TOTP ne peut pas être hashé : le serveur doit pouvoir le **relire** pour recalculer les codes.
Il est donc **chiffré au repos** (Fernet, bibliothèque `cryptography`) avec la clé `FORGE_MFA_SECRET_KEY`, au lieu d'être stocké en clair.

Le chiffrement est **obligatoire** : démarrer sans la clé lève `MfaSecretKeyMissing`.
Ce module met en œuvre le ticket `SEC-MFA-SECRET-ENCRYPTION-001`.

## 2. Chiffrer et déchiffrer

```python
from forge_mvc_mfa import encrypt_totp_secret, decrypt_totp_secret

stored = encrypt_totp_secret(raw_secret)   # "enc:..."
raw = decrypt_totp_secret(stored)
```

| Fonction | Comportement |
|---|---|
| `encrypt_totp_secret(raw)` | chiffre un secret brut ; retourne la valeur préfixée `enc:` |
| `decrypt_totp_secret(stored)` | déchiffre un secret stocké ; lève `MfaSecretNotEncrypted` si non préfixé |

Le préfixe `enc:` distingue les secrets chiffrés d'éventuelles valeurs legacy.

## 3. Valider la clé au démarrage

```python
from forge_mvc_mfa import validate_mfa_secret_key_config

validate_mfa_secret_key_config()   # à appeler au bootstrap applicatif
```

`validate_mfa_secret_key_config()` échoue **tôt** sur une configuration dangereuse, plutôt qu'au moment où un utilisateur tente de s'enrôler.
Sont refusés : clé absente ou vide, valeurs placeholder évidentes (`change-me`, `secret`, `dev`…), clé non Fernet.
Aucun message ne contient la valeur de la clé tentée, pour ne pas fuir un secret dans un log.

## 4. Les exceptions

| Exception | Cause |
|---|---|
| `MfaSecretKeyMissing` | `FORGE_MFA_SECRET_KEY` absente de l'environnement |
| `MfaSecretKeyPlaceholder` | la clé contient une valeur placeholder évidente |
| `MfaSecretInvalidKey` | clé invalide, ou déchiffrement impossible |
| `MfaSecretNotEncrypted` | secret legacy non chiffré détecté |

## 5. Contextes d'utilisation

- **Démarrage** : `validate_mfa_secret_key_config()` au bootstrap.
- **Stockage** : `encrypt_totp_secret(secret)` avant d'écrire en base.
- **Vérification** : `decrypt_totp_secret(stored)` avant de recalculer un code.

## 6. Voir aussi

- [Le cœur MFA](mfa.md) : `generate_totp_secret` produit le secret à chiffrer.
- [Vue d'ensemble et politique de sécurité](../reference.md) : la politique complète de stockage.
