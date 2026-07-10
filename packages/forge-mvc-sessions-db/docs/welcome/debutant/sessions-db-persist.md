# Une session qui survit au redémarrage

Objectif : constater qu'une session BDD persiste après l'arrêt et le redémarrage du processus.

**Ce que vous allez apprendre :** le store mémoire du cœur (`MemorySessionStore`) perd tout quand le processus s'arrête.
`DbSessionStore` range ses données en base, donc une session écrite reste lisible après un redémarrage.
On écrit une donnée avec `set()`, on redémarre, puis on la retrouve avec `get()`.

Deuxième palier du **niveau débutant** de la progression Sessions BDD.

## Ce que ce starter montre

- écrire une donnée dans une session avec `set()` ;
- retrouver cette donnée après un redémarrage du processus ;
- comprendre le contraste avec `MemorySessionStore`.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `create(data=None)` | Crée une session et renvoie son identifiant. | Opt-ins |
| `set(sid, data)` | Fusionne des données dans une session existante. | Opt-ins |
| `get(sid)` | Relit les données d'une session. | Opt-ins |

## 1. Écrire une donnée dans la session

```python
from forge_mvc_sessions_db import DbSessionStore

store = DbSessionStore(ttl=3600)

sid = store.create()
store.set(sid, {"langue": "fr"})

print(store.get(sid)["langue"])   # fr
```

### Comprendre ce code

- `create()` crée la session et renvoie son identifiant.
- `set(sid, {"langue": "fr"})` fusionne la clé `langue` dans les données existantes.
- `set()` est un merge : les clés déjà présentes sont conservées, celles fournies sont ajoutées ou remplacées.

## 2. Redémarrer et retrouver la donnée

Notez l'identifiant `sid`, arrêtez le processus Python, relancez-le, puis relisez la session avec le même identifiant.

```python
from forge_mvc_sessions_db import DbSessionStore

store = DbSessionStore(ttl=3600)

# sid provient de l'exécution précédente, avant le redémarrage.
session = store.get(sid)
print(session["langue"])   # fr, la donnée a survécu
```

### Comprendre ce code

- La donnée n'était pas en mémoire : elle est dans la table `forge_sessions`.
- Un nouveau processus construit un nouveau `DbSessionStore`, mais lit la même base.
- Tant que la session n'est pas expirée, `get(sid)` la retrouve intacte.

## 3. Le contraste avec le store mémoire

```text
MemorySessionStore : les sessions vivent dans un dictionnaire Python.
Arrêt du processus  : le dictionnaire disparaît, toutes les sessions sont perdues.

DbSessionStore      : les sessions vivent dans la table forge_sessions.
Arrêt du processus  : la table reste, les sessions sont rechargées au démarrage suivant.
```

### Comprendre ce code

- Le store mémoire convient à un seul processus, sans persistance : parfait pour les tests ou un prototype.
- Le store BDD survit aux redémarrages : un utilisateur reste connecté après un déploiement.
- Le choix se fait à la configuration, sans changer le code des contrôleurs.

## À retenir

- `set(sid, data)` fusionne des données dans une session existante.
- Une session BDD survit au redémarrage du processus, car elle est stockée en base.
- Le store mémoire du cœur, lui, perd tout à l'arrêt du processus.

## Après ce starter

Vous savez créer, écrire et retrouver une session persistante.
Faisons le point sur ce niveau débutant.

[Bilan](bilan.md)
