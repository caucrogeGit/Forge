# La vérification email dans Forge

Ce document décrit la vérification d'adresse email d'un utilisateur.

Le fichier de code correspondant est `core/auth/email.py`.

## 1. À quoi sert ce module ?

Pour confirmer qu'une adresse appartient bien à l'utilisateur, on lui envoie un jeton de vérification, qu'il renvoie pour marquer son email comme vérifié.

## 2. L'API

| Fonction | Rôle |
|---|---|
| `create_email_verification_token()` | crée un jeton de vérification email |
| `verify_email_verification_token(token, hash)` | `True` si le token brut est valide |
| `email_verification_timestamp()` | datetime UTC courante pour `email_verified_at` |
| `is_email_verified(email_verified_at)` | `True` si l'email a été vérifié |

## 3. Contextes d'utilisation

- **Inscription** : créer un jeton, l'envoyer par mail, le vérifier au retour.

## 4. Voir aussi

- [Les jetons Auth](tokens.md) : le mécanisme de jeton sous-jacent.
- [Le reset de mot de passe](reset.md) : même schéma.
