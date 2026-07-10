# Sessions partagées entre workers

Objectif : comprendre pourquoi un déploiement multi-worker exige un store partagé, et comment `DbSessionStore` le fournit.

**Ce que vous allez apprendre :** en production, Gunicorn lance plusieurs processus (workers) pour servir les requêtes en parallèle.
Chaque worker a sa propre mémoire : un `MemorySessionStore` n'est donc pas partagé entre eux.
`DbSessionStore` range les sessions dans une base commune, que tous les workers lisent et écrivent.

Premier palier du **niveau intermédiaire** de la progression Sessions BDD.

!!! note "Module opt-in"
    Si `forge-mvc-sessions-db` n'est pas installé, l'import échoue.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet.

## Ce que ce starter montre

- pourquoi `MemorySessionStore` échoue en multi-worker ;
- comment `DbSessionStore` partage l'état via la base ;
- brancher le store partagé une fois pour toute l'application.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `DbSessionStore(ttl=...)` | Construit un store partagé entre tous les processus. | Opt-ins |
| `forge.configure(session_store=...)` | Déclare ce store partagé pour l'application. | Opt-ins |
| `get(sid)` | Relit une session écrite par un autre worker. | Opt-ins |

## 1. Le problème du store mémoire en multi-worker

```text
Gunicorn --workers 4 : quatre processus Python indépendants.

Worker A : crée la session S, la garde dans SON dictionnaire mémoire.
Worker B : reçoit la requête suivante, ne connaît pas S, la session semble perdue.
```

### Comprendre ce code

- Chaque worker Gunicorn est un processus distinct, avec sa propre mémoire.
- `MemorySessionStore` stocke les sessions dans un dictionnaire local à un seul processus.
- Le répartiteur de charge envoie les requêtes à n'importe quel worker : l'utilisateur paraît déconnecté au hasard.

## 2. Le store BDD comme état partagé

```python
import core.forge as forge
from forge_mvc_sessions_db import DbSessionStore

forge.configure(session_store=DbSessionStore(ttl=3600))
```

### Comprendre ce code

- Tous les workers construisent leur `DbSessionStore`, mais tous parlent à la même base via `core.database.db`.
- Une session créée par le worker A est écrite dans `forge_sessions`, donc lisible par le worker B.
- L'état partagé vit dans la base, pas dans la mémoire d'un processus : la répartition de charge devient transparente.

## 3. Vérifier le partage

```python
from forge_mvc_sessions_db import DbSessionStore

# Worker A
store = DbSessionStore(ttl=3600)
sid = store.create({"utilisateur": "alice"})

# Worker B (autre processus, même base)
autre_store = DbSessionStore(ttl=3600)
print(autre_store.get(sid)["utilisateur"])   # alice
```

### Comprendre ce code

- Deux instances de `DbSessionStore`, dans deux processus, lisent la même table.
- `get(sid)` renvoie la session quel que soit le worker qui l'a créée.
- C'est exactement le comportement attendu derrière un Gunicorn multi-worker.

## À retenir

- Chaque worker Gunicorn est un processus séparé, avec sa propre mémoire.
- `MemorySessionStore` n'est pas partagé entre workers : les sessions semblent aléatoirement perdues.
- `DbSessionStore` range l'état dans une base commune, donc partagé par tous les workers.

## Après ce starter

Les sessions partagées s'accumulent en base, y compris celles qui ont expiré.
Voyons comment les nettoyer.

[Nettoyer les sessions expirées](sessions-db-cleanup.md)
