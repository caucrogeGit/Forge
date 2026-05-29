# Structure des opt-ins dans un projet Forge

> Ticket : `OPTINS-PROJECT-STRUCTURE-001`. Ce document **pose le contrat**
> d'une convention de branchement local des opt-ins dans une application
> Forge générée. Il est **architecture + documentation uniquement** :
> aucun code n'est généré, aucune commande n'est ajoutée, aucun paquet
> n'est déplacé. L'implémentation viendra dans des tickets ultérieurs.

## Objectif

Donner à un projet Forge un **lieu unique, explicite et lisible** pour
voir et brancher les modules opt-in qu'il active :

- quels opt-ins sont activés ;
- quelles **routes** ils ajoutent ;
- quelles **migrations** ils utilisent ;
- quels **starters** leur sont liés ;
- quelle **documentation locale** existe ;
- comment ils sont branchés dans `mvc/routes.py`.

C'est l'équivalent Forge — volontairement simple et sans magie — de ce
que les **bundles** apportent dans Symfony, mais aligné sur la charte
Forge (pas d'écriture invisible, refus de la magie cachée, une seule
façon officielle de faire).

## Différence entre package opt-in et branchement projet

Deux choses distinctes, à ne jamais confondre :

| | **Package opt-in** | **Branchement projet** |
|---|---|---|
| Où | `packages/forge-mvc-*` (mono-dépôt Forge) + PyPI | dossier `optins/` **dans le projet utilisateur** |
| Contient | le **code complet** du module (logique, API publique) | uniquement le **câblage local** : routes, migrations utilisées, README, docs locales |
| Installé par | `pip install forge-mvc-<module>` | présent dans le projet généré |
| Maintenu par | l'équipe Forge | l'utilisateur (son application) |

Règle verrouillée : **les packages distribués restent dans
`packages/forge-mvc-*`**. Le dossier `optins/` côté projet **ne contient
pas** le code complet du package — il ne fait que le **brancher**.

## Pourquoi pas de découverte automatique

Forge **ne fait pas** de *discovery* magique des opt-ins. Aucune
inspection automatique de `site-packages`, aucun chargement implicite au
démarrage, aucun « plugin scan ».

Raisons (charte v2) :

- **Refuser la magie cachée** (§3) : un opt-in actif doit être visible
  dans le code du projet, pas deviné à l'exécution.
- **Pas d'écriture invisible** (§9) : Forge ne réécrit pas
  silencieusement `mvc/routes.py`.
- **Une seule façon officielle** (§11) : le branchement passe toujours
  par `optins/registry.py`, appelé explicitement.

Conséquence directe : **Forge Core ne dépend pas des opt-ins et ne les
charge pas automatiquement.** Un opt-in absent ne casse jamais le core.

## Dossier `optins/`

Structure cible côté projet utilisateur :

```text
optins/
├── __init__.py
├── registry.py
├── iot/
│   ├── __init__.py
│   ├── routes.py
│   ├── README.md
│   ├── migrations/
│   └── docs/
├── rbac/
│   ├── __init__.py
│   ├── routes.py
│   └── README.md
└── media/
    ├── __init__.py
    ├── routes.py
    └── README.md
```

Chaque sous-dossier `optins/<module>/` est le **point de branchement
local** d'un package opt-in installé. Il reste **mince** : il référence
le package, il ne le duplique pas.

## `optins/registry.py`

Le registre central énumère, **de façon lisible et explicite**, les
opt-ins branchés du projet :

```python
def register_optins(router):
    from optins.iot.routes import register as register_iot

    register_iot(router)
```

Et le projet l'appelle explicitement dans `mvc/routes.py` :

```python
from optins.registry import register_optins

register_optins(router)
```

Pas de décorateur magique, pas d'auto-import : on **lit** dans
`registry.py` la liste exacte des opt-ins actifs.

## `optins/<module>/routes.py`

Chaque opt-in expose une fonction `register(router)` qui délègue à
l'API publique du **package** :

```python
# optins/iot/routes.py
from forge_mvc_iot import register_iot_routes


def register(router):
    register_iot_routes(router)
```

Le code métier vit dans le package (`forge_mvc_iot`) ; `optins/iot/`
fait seulement le pont. C'est l'API publique du package qui reste le
contrat de complétude (charte v2 §10).

## Migrations opt-in

Un opt-in peut apporter des migrations SQL (ex. `iot_events` pour Forge
IoT). La convention :

- la migration **source** est packagée dans le module
  (`forge_mvc_iot/migrations/`, *package data*) ;
- `optins/<module>/migrations/` côté projet reçoit la **copie locale**
  effectivement appliquée (via l'outil dédié du module, ex.
  `forge iot:init`, puis `forge migration:apply`) ;
- le SQL reste **visible** (charte v2 §5) et appliqué explicitement.

Ce ticket ne déplace ni ne copie aucune migration : il fixe seulement
**où** elle se branchera côté projet.

## Starters opt-in

Les **starters restent officiellement gérés par Forge CLI**
(`forge starter:build`, profils `forge new`). Un starter opt-in (ex.
`welcome-iot`) peut, à terme, **générer** une structure `optins/<module>/`
prête à brancher — mais la responsabilité du starter reste côté Forge
CLI. Le dossier `optins/` est la **cible** de cette génération, pas un
système concurrent.

## Documentation locale

La **documentation complète** d'un opt-in reste dans la **doc officielle
Forge** (par exemple les pages `docs/iot/*`). Côté projet, chaque
`optins/<module>/README.md` ne reçoit qu'un **README utile et minimal** :
ce que l'opt-in branche dans *ce* projet, les commandes à lancer, et un
lien vers la doc officielle. On ne duplique pas la documentation de
référence dans chaque projet.

## Exemple avec Forge IoT

Activer **Forge IoT** dans un projet, avec la convention cible :

```text
optins/
├── registry.py            # appelle register_iot(router)
└── iot/
    ├── routes.py          # register(router) -> register_iot_routes(router)
    ├── migrations/        # copie locale de *_create_iot_events.sql
    ├── README.md          # « IoT branché ici ; voir docs/iot/ »
    └── docs/              # notes locales minimales
```

```python
# optins/iot/routes.py
from forge_mvc_iot import register_iot_routes


def register(router):
    register_iot_routes(router)   # /api/iot/events, etc.
```

Le package `forge-mvc-iot` (dans `packages/forge-mvc-iot/`) fournit tout
le reste : contrat MQTT, subscriber, repository, API HTTP, CLI
(`forge iot:doctor`, `iot:init`, `iot:listen`, `iot:simulate`). Voir
l'[architecture Forge IoT](../iot/architecture.md) et l'[audit de
clôture IoT](../history/audits/audit-iot-closing.md).

!!! example "Exemple vivant : le starter `welcome-iot`"
    Cette convention n'est pas que théorique : le starter
    [`welcome-iot`](../starters/welcome-iot/index.md) **génère réellement**
    cette structure `optins/iot/` dans le projet créé
    (`OPTINS-IOT-PROJECT-BRIDGE-001`). C'est le premier opt-in officiel
    branché via `optins/registry.py`. Les autres modules (`rbac`,
    `media`…) suivront le même modèle dans des tickets ultérieurs.

## Comparaison avec les bundles Symfony

| Symfony | Forge (cible `optins/`) |
|---|---|
| Bundle = package réutilisable | Package opt-in `forge-mvc-*` |
| `config/bundles.php` liste les bundles actifs | `optins/registry.py` liste les opt-ins branchés |
| Auto-configuration / compiler passes | **Aucune** auto-config — branchement explicite |
| Recipes Flex modifient le projet | Forge **n'écrit jamais** en invisible (§9) |
| Bundle découvert par le framework | **Pas de discovery magique** ; appel explicite |

L'esprit est le même (« un endroit pour voir les modules activés »), mais
Forge reste **plus explicite** : tout le branchement est du Python
lisible que l'utilisateur contrôle, sans couche d'auto-magie.

## Décisions verrouillées

1. Les packages distribués **restent** dans `packages/forge-mvc-*`.
2. Le dossier `optins/` côté projet **ne contient pas** le code complet
   du package.
3. `optins/` sert au **branchement local** : routes, migrations, README,
   docs locales.
4. Le branchement est **explicite** via `optins/registry.py`.
5. **Forge Core ne charge pas automatiquement** tous les opt-ins.
6. **Pas de discovery magique.**
7. Les starters opt-in restent gérés par Forge CLI, mais peuvent
   **générer** une structure `optins/`.
8. La documentation complète reste dans la doc officielle ; le projet
   local reçoit seulement un **README utile**.

## Hors périmètre

Ce ticket **pose le contrat**. Ne sont **pas** faits ici :

- pas de commande `forge optin:enable` / `forge optin:disable` ;
- pas de génération automatique de `optins/` ;
- pas de modification de `forge new` ;
- pas de déplacement des packages ;
- aucune modification fonctionnelle IoT / RBAC / media / workflow /
  stats / MFA ;
- pas de refonte des starters existants ;
- pas de migration automatique.

## Tickets suivants

- `OPTINS-IOT-PROJECT-BRIDGE-001` (**livré**) — applique concrètement
  cette structure à Forge IoT : le starter `welcome-iot` génère
  `optins/iot/` et branche l'API via `optins/registry.py`.
- `OPTINS-CLI-ENABLE-AUDIT-001` (**livré**) — cadre la future commande
  `forge optin:enable` : voir l'[audit `forge optin:enable`](optins-cli-enable-audit.md)
  (commande cible, idempotence, dry-run, gestion des conflits, sans
  discovery ni écrasement silencieux).
- `OPTINS-CLI-ENABLE-IOT-001` (**livré**) — implémente
  `forge optin:enable iot` (dry-run par défaut, `--apply`, idempotent).
  Voir la
  [référence CLI](../reference/cli-commands.md#opt-ins-branchement-projet).
- `OPTINS-CLI-ENABLE-ROUTES-APPLY-001` (**livré**) — `--apply` branche
  `mvc/routes.py` **si la structure est reconnue** (`router = Router()`),
  sinon `[WARN]` + instruction manuelle (aucune modification).
- `OPTINS-CLI-LIST-001` (**livré**) — `forge optin:list`, commande
  **lecture seule** qui affiche l'état local des opt-ins (`absent` /
  `partiel` / `activé` pour `iot`), sans rien créer ni modifier.
