# Audit de clôture du chantier opt-ins

> Ticket : `OPTINS-CLOSING-AUDIT-001`. Audit **documentaire** de fin de
> chantier — aucun code fonctionnel n'est ajouté. Instantané pris après
> le dernier ticket opt-ins (`efc2f70`, `OPTINS-CLI-LIST-001`).

## Verdict

**Le chantier opt-ins est clôturable.** Le modèle de **branchement local
des opt-ins** tient sur un cas réel et complet — Forge IoT — avec un
cycle cohérent :

```text
optins/ (contrat) → starter welcome-iot → forge optin:enable iot
→ --apply (fichiers + mvc/routes.py si reconnu) → forge optin:list (état)
```

Le modèle est **explicite, lisible, idempotent, lecture-seule par
défaut, sans discovery magique**. Il n'est validé que pour `iot` — c'est
**volontaire** : la généralisation à RBAC/media/… est reportée à des
tickets d'audit dédiés, après cette clôture.

## Résumé exécutif

- **6 tickets opt-ins livrés** (contrat → bridge starter → audit enable →
  enable iot → routes apply → list), tous commités sur `main`.
- **2 commandes CLI** : `forge optin:enable <name>` (dry-run par défaut,
  `--apply` pour écrire) et `forge optin:list` (lecture seule).
- **Couche `optins/`** générée à l'identique par le starter `welcome-iot`
  **et** par `forge optin:enable iot` — structure cohérente.
- **99 tests opt-ins** verts (`tests/test_optins_*.py` +
  `tests/meta/test_optins_*.py`).
- Les **packages restent** dans `packages/forge-mvc-*` ; `optins/` est une
  **couche de branchement local**, jamais une copie du code.

## Tickets livrés

| Ticket | Commit | Sujet |
|---|---|---|
| `OPTINS-PROJECT-STRUCTURE-001` | `2cc45e2` | Contrat de la structure `optins/` |
| `OPTINS-IOT-PROJECT-BRIDGE-001` | `7dd5f69` | `welcome-iot` génère `optins/iot/` |
| `OPTINS-CLI-ENABLE-AUDIT-001` | `9d275cf` | Conception de `forge optin:enable` |
| `OPTINS-CLI-ENABLE-IOT-001` | `6dbc247` | `forge optin:enable iot` (dry-run/apply) |
| `OPTINS-CLI-ENABLE-ROUTES-APPLY-001` | `3a97ab6` | Branchement prudent de `mvc/routes.py` |
| `OPTINS-CLI-LIST-001` | `efc2f70` | `forge optin:list` (lecture seule) |

Le présent ticket `OPTINS-CLOSING-AUDIT-001` n'ajoute que cet audit et
son garde-fou méta.

## Architecture obtenue

- **Packages distribués** : inchangés, dans `packages/forge-mvc-*` (source
  de vérité, PyPI). Aucun déplacement.
- **`optins/`** : couche **côté projet utilisateur**, branchement local
  uniquement (routes, README, repères de migration) — pas le code du
  paquet.
- **Forge Core indépendant des opt-ins** : ni `core/` ni la commande
  `optin:list` n'importent `forge_mvc_iot` ; `optin:enable` vérifie la
  présence du paquet via `importlib.util.find_spec`, sans l'importer.
- **Pas de discovery magique** : le branchement est explicite via
  `optins/registry.py`, appelé depuis `mvc/routes.py`.

## Structure `optins/`

Modèle cible (contrat `OPTINS-PROJECT-STRUCTURE-001`), généré tel quel
pour IoT :

```text
optins/
├── __init__.py
├── registry.py
└── iot/
    ├── __init__.py
    ├── routes.py
    ├── README.md
    └── migrations/
        └── README.md
```

Rappels verrouillés :

- les **packages restent dans `packages/forge-mvc-*`** ;
- **`optins/` est une couche de branchement local**, pas une copie du
  paquet ;
- le README local reste **court** et renvoie vers la doc officielle.

## Cas Forge IoT

Le seul opt-in branché par ce chantier. `optins/iot/routes.py` délègue à
l'API publique du paquet :

```python
from forge_mvc_iot import register_iot_routes

def register(router):
    register_iot_routes(router)   # /api/iot/events, etc.
```

Et `optins/registry.py` l'appelle explicitement :

```python
def register_optins(router):
    from optins.iot.routes import register as register_iot
    register_iot(router)
```

## Commandes CLI disponibles

| Commande | Rôle | Écrit ? |
|---|---|---|
| `forge optin:enable iot` | aperçu (dry-run) du branchement IoT | non |
| `forge optin:enable iot --apply` | crée `optins/iot/` + branche `mvc/routes.py` si reconnu | oui |
| `forge optin:list` | affiche l'état local des opt-ins | **non (lecture seule)** |

## Comportement de `forge optin:enable iot`

- **dry-run par défaut** : sans `--apply`, rien n'est écrit (`[DRY-RUN] …
  serait créé`) ;
- **`--apply` nécessaire pour écrire** : crée les fichiers `optins/`
  absents ;
- **idempotence** : fichier absent → créé ; identique → `[OK] déjà
  présent` ; **différent → `[WARN]` + aucune écriture** (jamais
  d'**écrasement silencieux**) ;
- **paquet absent** → `[ERREUR]` + `pip install --pre forge-mvc-iot`
  (exit 1, même en dry-run) ;
- **pas de discovery magique** (aucun `pkgutil`/scan).

### `mvc/routes.py`

- **`--apply` ne branche `mvc/routes.py` que si la structure est
  reconnue** (présence de `router = Router()`) : insère alors l'import
  `from optins.registry import register_optins` + l'appel
  `register_optins(router)`, **idempotemment** ;
- **structure ambiguë** (ou fichier absent) → `[WARN]` + **instruction
  manuelle**, aucune modification ;
- **pas de marqueurs imposés** (idempotence par présence de l'appel) ;
- **aucune modification arbitraire** de fichiers.

## Comportement de `forge optin:list`

- **strictement lecture seule** : ne crée, ne modifie, n'installe rien ;
- **n'importe pas `forge_mvc_iot`** ni aucun paquet opt-in (lecture de
  texte uniquement) ;
- états `iot` : `absent`, `partiel` (structure présente mais
  `register_optins(router)` absent de `mvc/routes.py`), `activé` ;
- **pas de discovery magique**, pas de scan global des paquets installés ;
- exit `0` toujours.

## Starter `welcome-iot`

`OPTINS-IOT-PROJECT-BRIDGE-001` a fait du starter l'exemple vivant :

- `welcome-iot` **génère `optins/iot/`** (mêmes fichiers que
  `optin:enable iot`) ;
- `optins/registry.py` est **explicite** ;
- `optins/iot/routes.py` appelle **`register_iot_routes`** ;
- un **README local** court existe (`optins/iot/README.md`).

## Documentation disponible

- [Structure des opt-ins (projet)](../../architecture/optins-project-structure.md) ;
- [Audit `forge optin:enable`](../../architecture/optins-cli-enable-audit.md) ;
- [Référence CLI — Opt-ins](../../reference/cli-commands.md#opt-ins-branchement-projet)
  (`optin:enable`, `optin:list`) ;
- [Starter Bonjour IoT](../../starters/welcome-iot/index.md).

## Tests et validations

- **99 tests opt-ins** verts : `tests/test_optins_*.py` (commande +
  bridge) + `tests/meta/test_optins_*.py` (contrat, audit, clôture).
- Garde-fous transverses : `core/` n'importe pas les opt-ins ; `optin:list`
  sans import IoT ni écriture (AST) ; cohérence CLI ↔ doc
  (`test_forge_help_coverage_001`, `test_cli_help_flags_closing_audit_001`).
- Validations standard vertes : `compileall`, `ruff check .`,
  `mkdocs build --strict`, `git diff --check`.

## Limites assumées

Le chantier opt-ins est **volontairement minimal** :

- **seul `iot` est supporté** (enable + list) ;
- **pas de `rbac` / `media` / `workflow` / `stats` / `mfa`** ;
- pas de `forge optin:disable` ;
- pas de `forge optin:list --json` ;
- pas de gestion avancée des conflits (un fichier divergent → WARN, pas
  de fusion/diff) ;
- pas de rollback automatique ;
- pas de `migration:apply` automatique (l'utilisateur lance
  `forge iot:init` puis `forge migration:apply`) ;
- pas de modification de fichiers arbitraires (seuls `optins/` et, si
  reconnu, `mvc/routes.py`) ;
- **pas de discovery magique** des opt-ins.

## Dettes restantes

- Généralisation du modèle à un 2e opt-in (RBAC) non encore éprouvée —
  c'est l'objet du prochain audit.
- `forge optin:list` ne distingue pas encore l'état `conflit` (minimum
  utile : `absent`/`partiel`/`activé`).

## Tickets reportés

- `OPTINS-CLI-ENABLE-RBAC-AUDIT-001` — auditer l'extension à RBAC.
- `OPTINS-CLI-ENABLE-MEDIA-AUDIT-001` — auditer l'extension à media.
- `OPTINS-CLI-DISABLE-AUDIT-001` — concevoir un éventuel `optin:disable`.
- `OPTINS-CLI-LIST-JSON-001` — sortie `--json` pour `optin:list`.
- `OPTINS-CONFLICT-REPORT-001` — rapport de conflits plus détaillé.

## Décision de clôture

**Chantier opt-ins : CLÔTURÉ** pour le périmètre `iot`. Le cycle
`enable` → routes apply → `list` est cohérent, testé, documenté ; les
limites sont explicites et la dette structurelle (généralisation) est
isolée dans des tickets reportés. Deux chemins possibles ensuite :
`OPTINS-CLI-ENABLE-RBAC-AUDIT-001` (généraliser prudemment) ou
`RELEASE-BETA12-PRE-AUDIT-001` (préparer une bêta après IoT + opt-ins).
La généralisation à RBAC/media ne doit **pas** être ouverte avant
validation de cet audit.
