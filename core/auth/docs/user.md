# Le contrat utilisateur dans Forge

Ce document décrit la représentation minimale d'un utilisateur authentifié.

Le fichier de code correspondant est `core/auth/user.py`.

## 1. À quoi sert ce module ?

Forge n'impose pas de modèle utilisateur métier riche : il définit un **contrat minimal** (`AuthUser`) que l'application étend.

## 2. L'API

| Élément | Rôle |
|---|---|
| `AuthUser` | représentation Python minimale d'un utilisateur authentifié |
| `validate_auth_user_contract(data)` | valide le contrat minimal |
| `normalize_auth_user(data)` | normalise un dict brut en `AuthUser` |
| `is_valid_auth_user(user)` | `True` si structurellement valide |

## 3. Le principe

L'identité locale est minimale (id, email, hash, actif…) ; les rôles et permissions vivent ailleurs (module de contrôle d'accès optionnel), pas dans `users`.

## 4. Contextes d'utilisation

- **Loader applicatif** : produire un `AuthUser` depuis la base.

## 5. Voir aussi

- [La session Auth/User](session.md) et [le mot de passe](password.md).
