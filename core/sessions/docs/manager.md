# Le gestionnaire de backend de session dans Forge

Ce document décrit comment choisir le backend de session actif.

Le fichier de code correspondant est `core/sessions/manager.py`.

## 1. À quoi sert ce module ?

L'application choisit où stocker ses sessions.
Ce module expose le backend **actif** et permet d'en injecter un autre.

## 2. L'API

```python
from core.sessions.manager import get_session_store, set_session_store
from core.sessions.file_store import FileSessionStore

set_session_store(FileSessionStore())   # bascule sur le backend fichier
store = get_session_store()             # le backend actif
```

| Fonction | Rôle |
|---|---|
| `get_session_store()` | retourne le backend de session actif |
| `set_session_store(store)` | fixe le backend ; `None` réinitialise au backend mémoire par défaut |

## 3. Le backend par défaut

Sans configuration, le backend est [`MemorySessionStore`](memory_store.md) (mono-processus, sessions perdues au redémarrage).

## 4. Contextes d'utilisation

- **Démarrage** : `set_session_store(...)` au câblage pour un backend persistant.
- **Tests** : réinitialiser avec `set_session_store(None)`.

## 5. Voir aussi

- [Le contrat](contract.md) : l'interface attendue de `store`.
- [Backend fichier](file_store.md), [MariaDB](mariadb_store.md), [mémoire](memory_store.md).
