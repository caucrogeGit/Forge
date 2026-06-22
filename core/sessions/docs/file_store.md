# Le backend de session fichier dans Forge

Ce document décrit le backend de session sur disque.

Le fichier de code correspondant est `core/sessions/file_store.py`.

## 1. À quoi sert ce module ?

`FileSessionStore` stocke chaque session dans un fichier sous un dossier dédié.
Les sessions **survivent au redémarrage** du processus, sans base de données.

## 2. L'objet

```python
from core.sessions.file_store import FileSessionStore
from core.sessions.manager import set_session_store

set_session_store(FileSessionStore(sessions_dir="storage/sessions", ttl=3600))
```

| Élément | Rôle |
|---|---|
| `FileSessionStore(sessions_dir="storage/sessions", ttl=3600)` | backend fichier ; dossier de stockage et durée de vie |

Il implémente le [contrat `SessionStore`](contract.md).

## 3. Contextes d'utilisation

- **Persistance simple** : conserver les sessions entre redémarrages, sans base.
- **Mono-serveur** : un seul nœud lit/écrit le dossier ; pour plusieurs nœuds, préférer [MariaDB](mariadb_store.md).

## 4. Voir aussi

- [Le gestionnaire](manager.md) et [le contrat](contract.md).
- [Backend mémoire](memory_store.md), [MariaDB](mariadb_store.md).
