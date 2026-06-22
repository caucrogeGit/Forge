# Les jetons Auth dans Forge

Ce document décrit les jetons à usage limité (vérification email, reset…).

Le fichier de code correspondant est `core/auth/tokens.py`.

## 1. À quoi sert ce module ?

Certaines actions (vérifier un email, réinitialiser un mot de passe) reposent sur un **jeton à usage limité** : généré, envoyé, vérifié, puis consommé.
Ce module fournit la génération, le hachage et la vérification génériques.

## 2. L'API

| Élément | Rôle |
|---|---|
| `AuthToken` | représentation d'un jeton stockable (hash, expiration, usage) |
| `generate_auth_token()` | génère un token URL-safe cryptographiquement sûr |
| `hash_auth_token(token)` | SHA-256 du token brut (c'est le hash qu'on stocke) |
| `verify_auth_token(token, hash)` | vérifie un token brut contre son hash |
| `token_expires_at(...)` | calcule l'expiration |
| `is_token_expired(...)` / `is_token_usable(...)` | état du jeton |
| `validate_auth_token_contract` / `normalize_auth_token` / `is_valid_auth_token` | contrat |
| `InvalidAuthTokenError` | données de jeton invalides |

## 3. La sécurité

Comme les codes de récupération : on stocke le **hash**, jamais le token brut. La vérification compare les hashs.

## 4. Contextes d'utilisation

- **Vérification email** et **reset password** s'appuient sur ces jetons.

## 5. Voir aussi

- [La vérification email](email.md) et [le reset de mot de passe](reset.md).
