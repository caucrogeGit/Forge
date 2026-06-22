# Le backend de session MariaDB dans Forge

Ce document décrit le backend de session en base de données.

Le fichier de code correspondant est `core/sessions/mariadb_store.py`.

## 1. À quoi sert ce module ?

`MariaDbSessionStore` stocke les sessions dans une table MariaDB.
C'est le backend adapté à un déploiement **multi-worker** ou **multi-nœud** : la session est partagée via la base.

## 2. L'objet

```python
from core.sessions.mariadb_store import MariaDbSessionStore
from core.sessions.manager import set_session_store

set_session_store(MariaDbSessionStore(ttl=3600))
```

| Élément | Rôle |
|---|---|
| `MariaDbSessionStore(fetch_one=None, execute=None, ttl=3600)` | backend MariaDB ; exécuteurs SQL injectables (tests), durée de vie |

Il implémente le [contrat `SessionStore`](contract.md). Les exécuteurs `fetch_one`/`execute` sont injectables pour les tests ; à défaut, la connexion du noyau est utilisée.

## 3. Contextes d'utilisation

- **Production scalable** : sessions partagées entre plusieurs workers/nœuds.
- **Tests** : injecter `fetch_one`/`execute` simulés.

## 4. Voir aussi

- [Le gestionnaire](manager.md) et [le contrat](contract.md).
- [Backend mémoire](memory_store.md), [fichier](file_store.md).
