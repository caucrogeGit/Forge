# Injecter les exécuteurs pour tester

Objectif : tester `DbSessionStore` sans base réelle, en injectant `fetch_one` et `execute`.

**Ce que vous allez apprendre :** le constructeur accepte deux callables, `fetch_one` et `execute`.
Par défaut, ils passent par `core.database.db` ; en test, on fournit des versions factices.
On vérifie ainsi la logique du store, sans connexion ni table réelle.

Deuxième palier du **niveau avancé** de la progression Sessions BDD.

## Ce que ce starter montre

- les deux exécuteurs injectables du constructeur ;
- remplacer la base par des fonctions factices en test ;
- vérifier un appel du store sans base réelle.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `DbSessionStore(fetch_one=..., execute=...)` | Accepte des accesseurs base injectables. | Opt-ins |
| `create(data=None)` | Appelle `execute` avec la requête d'insertion. | Opt-ins |
| `get(sid)` | Appelle `fetch_one` avec la requête de lecture. | Opt-ins |

## 1. Les deux exécuteurs injectables

```text
DbSessionStore(fetch_one=None, execute=None, ttl=SESSION_TTL)

fetch_one(sql, params) -> dict | None   : lit une ligne.
execute(sql, params)   -> int           : écrit et renvoie le nombre de lignes touchées.
```

### Comprendre ce code

- Par défaut, `fetch_one` et `execute` délèguent à `core.database.db`.
- Les deux callables sont des points d'injection : on peut les remplacer entièrement.
- La logique du store (validation, merge, expiration) ne change pas selon la provenance de ces callables.

## 2. Injecter des fonctions factices

```python
from forge_mvc_sessions_db import DbSessionStore

lignes = {}   # une base en mémoire, pour le test

def fake_execute(sql, params):
    # On note simplement l'appel ; un vrai fake stockerait la ligne.
    lignes["dernier_sql"] = sql
    return 1

def fake_fetch_one(sql, params):
    return {"data": '{"langue": "fr"}'}

store = DbSessionStore(fetch_one=fake_fetch_one, execute=fake_execute)
```

### Comprendre ce code

- `fake_execute` et `fake_fetch_one` respectent les signatures attendues.
- Aucun accès réseau ni base : tout se passe en mémoire du test.
- On contrôle exactement ce que la « base » répond, donc les cas limites deviennent faciles à couvrir.

## 3. Vérifier un appel sans base réelle

```python
sid = store.create({"panier": []})
assert lignes["dernier_sql"].startswith("INSERT")

session = store.get(sid)
assert session["langue"] == "fr"
```

### Comprendre ce code

- `create()` a appelé `fake_execute` : on vérifie que la requête était bien une insertion.
- `get()` a appelé `fake_fetch_one`, qui a renvoyé une ligne factice ; le store l'a désérialisée.
- Le test valide la logique du store, indépendamment du moteur BDD.

## À retenir

- Le constructeur accepte `fetch_one` et `execute`, injectables pour le test.
- Par défaut, ils passent par `core.database.db` ; en test, on fournit des factices.
- On vérifie ainsi le store sans base réelle, en contrôlant les réponses.

## Après ce starter

Vous avez fait le tour du socle.
Place au bilan du niveau avancé.

[Bilan avancé](bilan.md)
