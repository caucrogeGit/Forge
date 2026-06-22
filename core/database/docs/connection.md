# Le pool de connexions dans Forge

Ce document décrit l'emprunt et la restitution de connexions MariaDB.

Le fichier de code correspondant est `core/database/connection.py`.

## 1. À quoi sert ce module ?

Ouvrir une connexion à chaque requête serait coûteux.
Ce module gère un **pool** de connexions MariaDB : on emprunte une connexion, on l'utilise, on la restitue.

C'est une API **interne** : en usage normal, on passe par [les helpers SQL](db.md) qui gèrent le pool pour vous.

## 2. L'API

| Fonction | Rôle |
|---|---|
| `get_connection()` | emprunte une connexion au pool (créé au premier appel) |
| `close_connection(connection)` | restitue la connexion au pool |

## 3. Contextes d'utilisation

- **Usage courant** : ne pas appeler directement ; utiliser `fetch_*` / `execute` / `insert`.
- **Usage avancé** : emprunter une connexion pour un cas non couvert par les helpers, et la restituer systématiquement.

## 4. Voir aussi

- [Les helpers SQL](db.md) : l'API publique qui s'appuie sur ce pool.
- [Les transactions](transaction.md).
