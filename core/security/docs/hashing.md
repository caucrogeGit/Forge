# Le hachage legacy dans Forge

Ce document décrit la vérification des mots de passe au format PBKDF2 hérité.

Le fichier de code correspondant est `core/security/hashing.py`.

## 1. À quoi sert ce module ?

Forge hache les mots de passe en **Argon2id** (via `core.auth.password`).
Ce module est **legacy** : il sert uniquement à vérifier d'anciens hashes PBKDF2 et à signaler qu'ils doivent migrer vers Argon2id.

## 2. L'API

| Fonction | Rôle |
|---|---|
| `verify_password_legacy(password, stored_hash)` | vérifie un mot de passe contre un hash PBKDF2 stocké |
| `pbkdf2_needs_rehash(stored_hash)` | `True` pour tout hash PBKDF2 (tous doivent migrer vers Argon2id) |

## 3. La migration transparente

À la connexion, si `verify_password_legacy` réussit et que `pbkdf2_needs_rehash` est vrai, l'application re-hache le mot de passe en Argon2id et remplace le hash stocké : la migration se fait sans action de l'utilisateur.

Les nouveaux projets utilisent directement `core.auth.password` (Argon2id) ; ce module ne sert qu'à la transition.

## 4. Contextes d'utilisation

- **Migration de base existante** : vérifier puis re-hacher les anciens mots de passe.

## 5. Voir aussi

- [Les décorateurs de sécurité](decorators.md) et [la session](session.md) pour l'authentification.
