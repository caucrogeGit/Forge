# La réinitialisation de mot de passe dans Forge

Ce document décrit la demande et la réinitialisation de mot de passe.

Le fichier de code correspondant est `core/auth/reset.py`.

## 1. À quoi sert ce module ?

Quand un utilisateur oublie son mot de passe, il demande un lien de réinitialisation (jeton), puis pose un nouveau mot de passe via ce jeton.

## 2. L'API

| Élément | Rôle |
|---|---|
| `PasswordResetRequest` | données pour envoyer un lien de reset |
| `create_password_reset_request(...)` | crée une demande à partir d'un utilisateur |
| `create_password_reset_token()` | crée le jeton de réinitialisation |
| `verify_password_reset_token(token, hash)` | valide le jeton |
| `password_reset_timestamp()` | datetime UTC pour l'horodatage |
| `validate_new_password(...)` | valide le nouveau mot de passe |
| `reset_password_with_token(...)` | vérifie le jeton et produit le nouveau hash |
| `PasswordResetResult` | résultat de la réinitialisation |

## 3. Contextes d'utilisation

- **Mot de passe oublié** : `create_password_reset_request` -> envoi -> `reset_password_with_token`.

## 4. Voir aussi

- [Les jetons Auth](tokens.md) et [le mot de passe](password.md).
