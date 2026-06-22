# Le chargeur de requêtes SQL dans Forge

Ce document décrit le chargement de modules de requêtes SQL par environnement.

Le fichier de code correspondant est `core/database/sql_loader.py`.

## 1. À quoi sert ce module ?

Pour garder le SQL **visible et organisé**, on peut ranger ses requêtes dans des modules SQL dédiés.
Ce module charge dynamiquement un fichier de requêtes depuis le dossier SQL de l'environnement courant.

## 2. L'API

```python
from core.database.sql_loader import charger_queries

queries = charger_queries("article")   # depuis {SQL_DIR}/{APP_ENV}/article...
```

| Fonction | Rôle |
|---|---|
| `charger_queries(nom_fichier)` | charge et retourne un module de requêtes SQL depuis `{SQL_DIR}/{APP_ENV}/` |

Le chargement dépend de `APP_ENV` : on peut donc avoir des requêtes spécifiques par environnement.

## 3. Contextes d'utilisation

- **Organisation du SQL** : centraliser les requêtes d'une entité dans un module dédié.

## 4. Voir aussi

- [Les helpers SQL](db.md) : exécuter les requêtes chargées.
