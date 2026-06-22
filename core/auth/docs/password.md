# Le mot de passe dans Forge

Ce document décrit le hachage et la vérification des mots de passe.

Le fichier de code correspondant est `core/auth/password.py`.

## 1. À quoi sert ce module ?

Forge hache les mots de passe en **Argon2id**.
Ce module est l'API canonique de hachage et de vérification ; le PBKDF2 hérité reste dans `core/security/hashing` pour la migration.

## 2. L'API

| Fonction | Rôle |
|---|---|
| `hash_password(password)` | retourne un hash Argon2id |
| `verify_password(password, stored_hash)` | vérifie un mot de passe contre un hash Argon2id |
| `password_needs_rehash(stored_hash)` | `True` si le hash doit être régénéré (paramètres obsolètes) |

```python
from core.auth import hash_password, verify_password

h = hash_password(clear)
ok = verify_password(clear, h)
```

## 3. Contextes d'utilisation

- **Création de compte** : `hash_password`.
- **Connexion** : `verify_password`, puis re-hacher si `password_needs_rehash`.

## 4. Voir aussi

- [La session Auth/User](session.md).
- [Le hachage legacy (core/security)](../core-security/hashing.md) : migration PBKDF2 -> Argon2id.
