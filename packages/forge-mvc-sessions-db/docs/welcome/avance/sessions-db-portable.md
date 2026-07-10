# Un SQL portable, tous backends

Objectif : comprendre pourquoi `DbSessionStore` fonctionne sur tous les backends BDD sans adaptation.

**Ce que vous allez apprendre :** un store de session naïf utilise souvent une fonction date propriétaire comme `NOW()`.
Ces fonctions changent d'un moteur à l'autre, ce qui casse la portabilité.
`DbSessionStore` calcule ses horodatages côté Python et les passe en paramètres, donc son SQL reste identique sur mariadb, sqlite, postgres et mssql (ADR-054).

Premier palier du **niveau avancé** de la progression Sessions BDD.

!!! note "Module opt-in"
    Si `forge-mvc-sessions-db` n'est pas installé, l'import échoue.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet.

## Ce que ce starter montre

- pourquoi les fonctions date propriétaires nuisent à la portabilité ;
- comment les horodatages sont calculés côté Python et passés en paramètres ;
- pourquoi le même store marche sur tous les backends via `core.database.db`.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `DbSessionStore(ttl=...)` | Store dont le SQL est portable, sans fonction date propriétaire. | Opt-ins |
| `create(data=None)` | Insère une session avec des horodatages calculés en Python. | Opt-ins |
| `cleanup_expired()` | Compare l'expiration à un horodatage Python passé en paramètre. | Opt-ins |

## 1. Le piège des fonctions date propriétaires

```text
MariaDB     : NOW()
SQL Server  : GETDATE()
SQLite      : datetime('now')
PostgreSQL  : CURRENT_TIMESTAMP
```

### Comprendre ce code

- Chaque moteur nomme différemment sa fonction « maintenant ».
- Un SQL qui code en dur `NOW()` ne s'exécute pas tel quel sur SQLite ou SQL Server.
- Un store qui dépend de ces fonctions se lie à un seul moteur : la portabilité est perdue.

## 2. Des horodatages calculés en Python

```python
from forge_mvc_sessions_db import DbSessionStore

store = DbSessionStore(ttl=3600)
sid = store.create({"panier": []})
```

### Comprendre ce code

- Au moment du `create()`, le store calcule l'instant courant et l'expiration en Python.
- Ces valeurs partent dans la requête comme paramètres, aux côtés des autres colonnes.
- Le SQL ne contient aucune fonction date : il ne dit que `INSERT ... VALUES (?, ?, ?, ?, ?)`.

## 3. Le même store, tous les backends

```python
# Le store parle toujours à la base via core.database.db,
# qui dispatche vers le backend BDD actif de l'application.
from forge_mvc_sessions_db import DbSessionStore

store = DbSessionStore(ttl=3600)   # identique sous mariadb, sqlite, postgres, mssql
```

### Comprendre ce code

- `core.database.db` route la requête vers le backend configuré, quel qu'il soit.
- Comme le SQL n'emploie aucune fonction propriétaire, il s'exécute à l'identique partout.
- C'est l'esprit de l'ADR-054 : un cœur agnostique, des backends interchangeables, un SQL portable.

## À retenir

- Les fonctions date propriétaires (`NOW()`, `GETDATE()`, `datetime('now')`) lient un store à un seul moteur.
- `DbSessionStore` calcule ses horodatages en Python et les passe en paramètres.
- Le même store fonctionne sur mariadb, sqlite, postgres et mssql via `core.database.db` (ADR-054).

## Après ce starter

Vous savez pourquoi le store est portable.
Voyons comment le tester sans base réelle, en injectant ses exécuteurs.

[Injecter les exécuteurs pour tester](sessions-db-inject.md)
