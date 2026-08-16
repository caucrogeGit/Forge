# Première session persistante

!!! note "Prérequis : installer l'opt-in"
    Installez `forge-mvc-sessions-db` avant de commencer : voir sa [référence](../../reference.md).

    ```bash
    pip install --pre forge-mvc-sessions-db    # installe le paquet
    forge opt-in:enable sessions-db          # le branche au projet
    ```

    Sans le paquet, l'application refuse de démarrer sur un `ModuleNotFoundError` au chargement des routes.

    `forge opt-in:install sessions-db` **affiche** la commande d'installation adaptée à votre environnement, pipx compris ; il n'installe rien lui-même (ADR-016).

Objectif : premier contact avec le module **opt-in** `forge-mvc-sessions-db`.

**Ce que vous allez apprendre :** `DbSessionStore` est un store de session qui range ses données en base, dans la table `forge_sessions`.
On le branche sur l'application avec `forge.configure`, puis on crée une session avec `create()` et on la relit avec `get()`.
La table de stockage doit d'abord exister.

Premier palier du **niveau débutant** de la progression Sessions BDD.

!!! note "Module opt-in"
    Si `forge-mvc-sessions-db` n'est pas installé, l'import échoue.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet : il fournit `MemorySessionStore` et `FileSessionStore`.

## Ce que ce starter montre

- créer la table `forge_sessions` à partir du script SQL fourni ;
- brancher `DbSessionStore` sur l'application avec `forge.configure` ;
- créer une session avec `create()` et la relire avec `get()`.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `DbSessionStore(ttl=...)` | Construit le store de session adossé à la base. | Opt-ins |
| `forge.configure(session_store=...)` | Déclare le store à utiliser dans l'application. | Opt-ins |
| `create(data=None)` | Crée une session et renvoie son identifiant. | Opt-ins |
| `get(sid)` | Relit les données d'une session. | Opt-ins |

## 1. Créer la table

La table n'est pas créée automatiquement.
`forge sessions:init` copie la migration embarquée du paquet dans `mvc/migrations/`.
Appliquez-la sur votre base, une seule fois.

```bash
forge sessions:init
forge db:config          # amorce la connexion dans env/ (une seule fois)
forge db:init            # provisionne la base
forge migration:apply
```

### Comprendre ce code

- `sessions:init` dépose la migration qui définit la table `forge_sessions`, `migration:apply` l'exécute.
- Une écriture en base reste explicite : rien n'est créé en silence.
- Sans cette table, `create()` et `get()` échouent faute de support de stockage.

## 2. Brancher le store sur l'application

```python
import core.forge as forge
from forge_mvc_sessions_db import DbSessionStore

forge.configure(session_store=DbSessionStore(ttl=3600))
```

### Comprendre ce code

- `DbSessionStore(ttl=3600)` construit un store dont les sessions expirent au bout d'une heure.
- `forge.configure(session_store=...)` dit à l'application d'utiliser ce store plutôt que celui du cœur.
- Par défaut, le store parle à la base via `core.database.db` : aucune configuration de connexion supplémentaire.

## 3. Créer et relire une session

```python
from forge_mvc_sessions_db import DbSessionStore

store = DbSessionStore(ttl=3600)

sid = store.create({"panier": []})
print(sid)              # identifiant hexadécimal de 64 caractères

session = store.get(sid)
print(session["panier"])   # []
```

### Comprendre ce code

- `create({"panier": []})` insère une nouvelle ligne dans `forge_sessions` et renvoie son identifiant.
- Forge complète la session avec ses champs standard : `authenticated`, `user`, `csrf_token`, `expires_at`.
- `get(sid)` recharge la session depuis la base et renvoie le dictionnaire des données, ou `None` si elle est absente ou expirée.

## À retenir

- Une session persistante se crée avec `create()` et se relit avec `get()`.
- Le store se branche sur l'application avec `forge.configure(session_store=...)`.
- La table `forge_sessions` doit exister au préalable (`forge sessions:init` puis `forge migration:apply`).

## Après ce starter

Vous avez créé et relu une première session en base.
Voyons ce qui distingue vraiment ce store du store mémoire : la survie au redémarrage.

[Une session qui survit au redémarrage](sessions-db-persist.md)
