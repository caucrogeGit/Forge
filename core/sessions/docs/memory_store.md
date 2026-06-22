# Le backend de session mémoire dans Forge

Ce document décrit le backend de session par défaut, en mémoire.

Le fichier de code correspondant est `core/sessions/memory_store.py`.

## 1. À quoi sert ce module ?

`MemorySessionStore` garde les sessions dans la mémoire du processus.
C'est le backend **par défaut** : simple, sans dépendance, idéal en développement.

## 2. L'objet

```python
from core.sessions.memory_store import MemorySessionStore

store = MemorySessionStore(ttl=3600)
```

| Élément | Rôle |
|---|---|
| `MemorySessionStore(ttl=3600)` | backend en mémoire ; `ttl` = durée de vie d'une session (secondes) |

Il implémente le [contrat `SessionStore`](contract.md).

## 3. Limites

Les sessions sont **perdues au redémarrage** et **non partagées** entre plusieurs workers.
Pour un déploiement multi-worker ou persistant, utiliser [le backend fichier](file_store.md) ou [MariaDB](mariadb_store.md).

## 4. Contextes d'utilisation

- **Développement / mono-processus** : backend par défaut, rien à configurer.

## 5. Voir aussi

- [Le gestionnaire](manager.md) : pour brancher un autre backend.
- [Le contrat](contract.md).
