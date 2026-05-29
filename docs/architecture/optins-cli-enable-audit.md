# Audit `forge optin:enable`

> Ticket : `OPTINS-CLI-ENABLE-AUDIT-001`. **Audit de conception** — ce
> document **cadre** la future commande `forge optin:enable` sans
> l'implémenter. Aucun code fonctionnel n'est ajouté : pas de
> modification de `forge.py`, `forge_cli/`, du starter `welcome-iot`, ni
> du paquet `forge-mvc-iot`. L'implémentation fera l'objet du ticket
> `OPTINS-CLI-ENABLE-IOT-001`, **après validation de ce contrat**.

!!! success "Implémenté pour `iot` (OPTINS-CLI-ENABLE-IOT-001 + OPTINS-CLI-ENABLE-ROUTES-APPLY-001)"
    Ce contrat est désormais **réalisé** pour le premier opt-in :
    `forge optin:enable iot` existe (dry-run par défaut, `--apply` pour
    écrire, idempotent). Le branchement de `mvc/routes.py` est implémenté
    par `OPTINS-CLI-ENABLE-ROUTES-APPLY-001` : insertion **uniquement si
    la structure est reconnue** (`router = Router()`), **sans marqueurs**
    (l'idempotence repose sur la présence de l'appel `register_optins`) ;
    structure ambiguë ou fichier absent → `[WARN]` + instruction
    manuelle, aucune écriture. Ce document reste la **référence de
    conception** ; voir la
    [référence CLI](../reference/cli-commands.md#opt-ins-branchement-projet).
    Les autres opt-ins (`rbac`, `media`…) restent à venir.

## Objectif

Définir précisément ce qu'une commande `forge optin:enable <name>` aura
le droit de faire pour **brancher localement** un opt-in dans un projet
Forge, en respectant la convention figée par
[la structure des opt-ins](optins-project-structure.md) :

- quels fichiers elle peut **créer** ;
- quels fichiers elle peut **modifier** (et avec quelle prudence) ;
- comment elle reste **idempotente** ;
- comment elle gère les **conflits** ;
- comment elle reste **explicite, lisible, réversible, pédagogique** et
  **sans découverte automatique**.

## Pourquoi ne pas coder directement

`forge optin:enable` est une commande **sensible** : elle touche
potentiellement `optins/`, `mvc/routes.py`, `mvc/migrations/`, un README
local et des fichiers de configuration. Coder trop vite risquerait
d'introduire :

- de la **magie cachée** (charte v2 §3) — un branchement deviné plutôt
  qu'écrit ;
- une **écriture invisible** dans le code utilisateur (charte v2 §9) —
  une modification non maîtrisée de `mvc/routes.py` ;
- des modifications **difficiles à relire ou à annuler**.

D'où cet audit préalable : on verrouille le contrat **avant** d'écrire la
moindre ligne.

## Commande cible

```bash
forge optin:enable <name>
```

- **Premier opt-in supporté : `iot`** (`forge optin:enable iot`), parce
  qu'il a déjà routes HTTP, migration packagée, CLI, starter et
  documentation. Les autres modules (`rbac`, `media`, `workflow`,
  `stats`, `mfa`) viendront plus tard, **un par un**, jamais en bloc.
- Options **futures** envisagées (non décidées définitivement ici, mais
  cadrées) :

| Option | Effet envisagé |
|---|---|
| `--dry-run` | n'écrit **rien** ; affiche ce qui serait créé / modifié (patch, instructions). **Doit exister dès la v1.** |
| `--apply` | autorise la modification réelle de `mvc/routes.py` (sinon : instruction manuelle affichée). |
| `--no-migrations` | ne touche pas à `mvc/migrations/` (l'utilisateur fera `forge iot:init` lui-même). |
| `--no-routes` | crée la couche `optins/` mais ne propose pas de brancher `mvc/routes.py`. |

Pas de `forge optin:disable` dans cette trajectoire (hors périmètre, à
auditer séparément si besoin).

## Modèle de branchement

La commande **n'invente rien** : elle matérialise le modèle déjà
documenté, identique à celui généré par le starter `welcome-iot`.

```python
# mvc/routes.py
from optins.registry import register_optins

register_optins(router)
```

```python
# optins/registry.py
def register_optins(router):
    from optins.iot.routes import register as register_iot

    register_iot(router)
```

```python
# optins/iot/routes.py
from forge_mvc_iot import register_iot_routes

def register(router):
    register_iot_routes(router)
```

Règles **verrouillées** sur le branchement :

- **pas de scan automatique** de dossiers (`optins/*` n'est pas « activé
  parce qu'il existe ») ;
- **pas d'`importlib` / `pkgutil`** pour charger tout ce qui traîne ;
- chaque opt-in actif est **importé et appelé explicitement** dans
  `optins/registry.py` ;
- **Forge Core ne dépend pas des opt-ins** et n'en charge aucun tout
  seul.

## Fichiers créés

Pour `forge optin:enable iot`, la commande pourra **créer** (write-if-new)
la couche locale, si absente :

```text
optins/
├── __init__.py
├── registry.py                    # créé s'il n'existe pas
└── iot/
    ├── __init__.py
    ├── routes.py
    ├── README.md
    └── migrations/
        └── README.md
```

Ces fichiers sont du **câblage local** ; ils ne dupliquent pas le code du
paquet `forge-mvc-iot`. Le README local reste **court** et renvoie vers
la documentation officielle.

## Fichiers modifiés

Deux fichiers existants peuvent devoir évoluer — traités avec **prudence
maximale** :

### `optins/registry.py`

S'il existe déjà, la commande doit **ajouter** l'appel de l'opt-in
(`register_iot`) **sans réécrire** le reste du fichier (qui peut contenir
d'autres opt-ins ou du code manuel). Si la forme du registre n'est pas
reconnue de façon non ambiguë → **WARN + instruction manuelle**, pas de
réécriture.

### `mvc/routes.py`

C'est le point le plus sensible (code utilisateur, charte v2 §9).
Politique **retenue et implémentée** (`OPTINS-CLI-ENABLE-ROUTES-APPLY-001`) :

- **en dry-run** : la commande **n'écrit pas** dans `mvc/routes.py` —
  elle annonce le branchement (`serait branché`) ;
- **avec `--apply`, si la structure est reconnue** (présence de
  `router = Router()`, même heuristique que `make:public-page`) : elle
  insère l'import `from optins.registry import register_optins` (près des
  imports) et l'appel `register_optins(router)` (en fin de fichier),
  **idempotemment** ;
- **sans marqueurs** : l'idempotence repose sur la présence de l'appel
  `register_optins(router)` (un 2e `--apply` ne duplique rien). Choix
  délibéré pour ne pas ajouter de bruit `# forge-optin: …` dans le
  fichier utilisateur ;
- si `mvc/routes.py` a une **structure non reconnue** (ou est absent) →
  **WARN + instruction manuelle**, jamais d'insertion « au jugé ».

### `mvc/migrations/`

La commande **ne crée pas** de migration elle-même : elle réutilise le
flux existant `forge iot:init` (copie la migration packagée) puis
`forge migration:apply`. `--no-migrations` permet de sauter cette
proposition. Le SQL reste **visible** et appliqué **explicitement**
(charte v2 §5).

## Idempotence

La commande doit pouvoir être **relancée sans casser le projet** :

```bash
forge optin:enable iot
forge optin:enable iot
```

Deuxième appel attendu (aucun doublon) :

```text
[OK] opt-in iot déjà présent
[OK] registre déjà configuré
[OK] routes déjà branchées
```

Règles :

- aucun **doublon** dans `optins/registry.py` (l'appel `register_iot`
  n'est ajouté qu'une fois) ;
- aucun **doublon** dans `mvc/routes.py` (l'import et l'appel
  `register_optins(router)` ne sont insérés qu'une fois ; si l'appel est
  déjà là → `[OK] déjà branché`) ;
- un fichier **déjà présent et identique** → `[OK]` silencieux, exit 0 ;
- un fichier **présent mais différent** → voir conflits.

## Gestion des conflits

Règle générale : **ne jamais écraser silencieusement** un fichier
utilisateur. En cas d'ambiguïté → **WARN + instructions manuelles**,
exit non bloquant.

| Situation | Comportement attendu |
|---|---|
| `optins/iot/routes.py` existe et **diffère** | `[WARN]` : ne pas écraser ; afficher le contenu attendu / un diff, laisser l'utilisateur décider |
| `optins/registry.py` existe avec du **code manuel** | `[WARN]` : ne pas réécrire ; afficher la ligne à ajouter |
| `mvc/routes.py` a une **structure non reconnue** | `[WARN]` : afficher l'instruction de branchement manuelle |
| la **migration existe déjà** dans `mvc/migrations/` | `[OK]` idempotent (déléguer à `forge iot:init`, déjà idempotent) |
| `forge-mvc-iot` **n'est pas installé** | `[ERREUR]` claire : `pip install forge-mvc-iot`, ne rien écrire qui dépende du paquet |

## Mode dry-run

`--dry-run` est **obligatoire dès la première version** :

- n'écrit **aucun** fichier, ne modifie **rien** ;
- affiche la liste de ce qui **serait** créé, le patch qui **serait**
  appliqué à `mvc/routes.py`, et les commandes migrations suggérées ;
- exit 0.

C'est le mode de **revue** : on voit l'effet complet avant de
l'appliquer. Cohérent avec l'esprit `forge iot:init` (copie idempotente,
sans exécuter le SQL) et `forge update --dry-run`.

## Cas Forge IoT

`forge optin:enable iot` produira exactement la structure que le starter
[`welcome-iot`](../starters/welcome-iot/index.md) génère déjà
(`OPTINS-IOT-PROJECT-BRIDGE-001`) :

1. crée `optins/` + `optins/iot/` (write-if-new) ;
2. ajoute `register_iot` dans `optins/registry.py` (idempotent) ;
3. propose (ou applique avec `--apply`) le branchement
   `register_optins(router)` dans `mvc/routes.py` ;
4. rappelle `forge iot:init` + `forge migration:apply` pour la table
   `iot_events` ;
5. renvoie vers la [doc IoT officielle](../iot/http-api.md).

La commande et le starter doivent rester **cohérents** : même structure,
même branchement explicite, mêmes fichiers. La commande est l'équivalent
« sur un projet existant » de ce que le starter fait « à la création ».

## Hors périmètre

Ce ticket **ne fait que cadrer**. Ne sont **pas** réalisés ici :

- pas de `forge optin:enable` **fonctionnel** ;
- pas de `forge optin:disable` ;
- pas de modification de `forge.py` ni de `forge_cli/` ;
- pas de génération automatique de fichiers ;
- pas de modification de `mvc/routes.py` ;
- pas de modification du starter `welcome-iot` ;
- pas de modification du paquet `forge-mvc-iot` ;
- pas de support `rbac` / `media` / `workflow` / `stats` / `mfa`.

## Décision

Trajectoire **validée pour conception** (implémentation au ticket
suivant) avec les règles **verrouillées** :

1. la commande cible sera **`forge optin:enable <name>`** ;
2. le **premier opt-in supporté sera `iot`** ;
3. la commande devra être **idempotente** ;
4. le **`--dry-run` devra exister** dès la première version ;
5. **aucune découverte automatique** ne sera introduite ;
6. **aucun fichier utilisateur ne sera écrasé silencieusement** ;
7. le branchement restera **explicite via `optins/registry.py`** ;
8. **Forge Core ne dépendra toujours pas des opt-ins**.

Ce ticket **n'implémente pas** la commande : il ne crée aucun code
fonctionnel, il fixe seulement le contrat. Prochain ticket :
`OPTINS-CLI-ENABLE-IOT-001` — implémentation réelle de
`forge optin:enable iot`, conforme à ce contrat.
