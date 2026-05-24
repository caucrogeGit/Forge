# CLI-HELP-FLAGS-AUDIT-001 — Audit du support `--help`

## Résumé

Audit exhaustif du support de `--help` dans les commandes CLI Forge
(commit de base `b3bee28`). **62 commandes** sont déclarées dans
`forge.py` et listées dans [forge --help](../../reference/cli-commands.md).

Bilan global :

| Classement | Nombre | Part |
|---|---:|---:|
| `OK_HELP` — aide réelle, exit 0 | **18** | 29 % |
| `ARGUMENT_ERROR` — `Usage:` affiché mais exit 1 | 17 | 27 % |
| `OTHER_ERR` — `--help` traité comme arg/option invalide | 13 | 21 % |
| `RUNS_COMMAND` — la commande s'exécute (effets de bord possibles) | 13 | 21 % |
| Non probable automatiquement (`new`) | 1 | 2 % |
| **Total audité** | **62** | 100 % |

Les groupes les plus exposés sont **Pages publiques** (0/5), **Mail**
(0/5), **Médias/JS** (0/3), **Internationalisation** (0/2),
**Déploiement** (0/2), **RBAC** (0/2), **Schémas JSON** (0/2),
**Projet** (0/4).

Les groupes les plus solides sont **Starters/modules** (5/6) et
**Auth utilisateurs** (8/8 commandes `auth:user:*` argparse-natives).

---

## Méthode d'audit

1. **Recensement** : lecture exhaustive de `forge.py`
   pour extraire les commandes dispatchées (`if command == "..."` /
   `if command in (…)`), croisée avec la sortie de `forge --help` et
   avec [docs/reference/cli-commands.md](../../reference/cli-commands.md).
2. **Probe automatisée** : exécution de `forge <cmd> --help` pour 61
   commandes (`new` exclu car il clonerait un projet et changerait le
   répertoire courant), avec un timeout de 10 s, capture de
   `stdout`, `stderr`, `exit code`, classification heuristique :
   - `OK_HELP` : `exit == 0` + marqueurs `usage`/`options`/`arguments` dans la sortie ;
   - `ARGUMENT_ERROR` : `exit != 0` + une ligne `Usage :` ou message « argument manquant » ;
   - `OTHER_ERR` : `exit != 0` sans pattern d'aide, message explicite « option inconnue », « entité introuvable », etc. ;
   - `RUNS_COMMAND` : sortie longue, exit 0, sans marqueur d'aide ;
   - `TRACEBACK` : trace Python complète.
3. **Lecture de structure** : inspection de chaque `forge_cli/*.py` et
   `forge_cli/entities/*.py` pour identifier le style d'arg-parsing
   (manuel vs argparse) et les éventuels `if arg in {"-h", "--help"}:`.
4. **Probe non commitée** : le script temporaire vit dans `/tmp/` ;
   il n'est pas conservé dans le dépôt (consigne du ticket).
5. **Pas de modification de comportement** : ce ticket n'altère
   aucune commande. La baseline reste celle de `b3bee28`.

---

## Commandes auditées

Liste canonique extraite de `forge.py` (lignes 482-717) et
regroupée comme dans `forge --help` (10 sections + `new` global).

| Section | Commandes |
|---|---|
| Projet | `new`, `doctor`, `project:check`, `project:audit`, `routes:list` |
| Entités | `make:entity`, `make:crud`, `make:pivot-crud`, `make:relation`, `entity:validate`, `sync:entity`, `sync:relations`, `sync:landing`, `build:model`, `check:model` |
| Pages publiques | `make:public-page`, `make:public-list`, `make:public-show`, `make:public-form`, `make:public-contact` |
| Base de données | `db:init`, `db:apply`, `migration:status`, `migration:apply`, `migration:make`, `migration:diff` |
| Schémas JSON | `schema:list`, `schema:doctor` |
| RBAC | `rbac:validate`, `rbac:audit` |
| Starters et modules | `starter:list`, `starter:build`, `module:list`, `module:install`, `module:files`, `module:routes` |
| Auth / Sécurité | `auth:init`, `auth:doctor`, `auth:status`, `auth:list-sql`, `auth:user:create`, `auth:user:list`, `auth:user:show`, `auth:user:disable`, `auth:user:enable`, `auth:user:password`, `auth:user:role:add`, `auth:user:role:remove`, `auth:user:roles` |
| Mail | `mail:init`, `mail:test`, `mail:render`, `mail:doctor`, `mail:logs` |
| Documentation | `docs:pdf` |
| Internationalisation | `i18n:init`, `i18n:check` |
| Médias et JavaScript | `upload:init`, `media:init`, `js:init` |
| Déploiement | `deploy:init`, `deploy:check` |

Total : **62 commandes**.

---

## Résultats par commande

Tableau exhaustif (`exit` = code de sortie de `forge <cmd> --help`,
`statut` = classification ; « note » résume la première ligne ou la
cause structurelle).

| Commande | exit | Statut | Note |
|---|---:|---|---|
| `new` | n/a | `RUNS_COMMAND` | non probable : `--help` serait passé à `cmd_new("--help", …)`, ferait échouer la regex de nom |
| `doctor` | 0 | `RUNS_COMMAND` | exécute le rapport `Forge doctor` ; aucun arg-check |
| `project:check` | 0 | `RUNS_COMMAND` | exécute le rapport ; ignore `--help` |
| `project:audit` | 0 | `RUNS_COMMAND` | exécute le rapport ; ignore `--help` |
| `routes:list` | 1 | `ARGUMENT_ERROR` | `cli_fail` « trop d'arguments » — ne sait pas répondre à `--help` |
| `make:entity` | 0 | `OK_HELP` | check explicite `if arg in {"-h", "--help"}` dans `_parse_args` |
| `make:crud` | 1 | `ARGUMENT_ERROR` | usage imprimé puis `SystemExit(1)` |
| `make:pivot-crud` | 1 | `ARGUMENT_ERROR` | `cli_fail` « arguments manquants » avant tout parsing |
| `make:relation` | 0 | `OK_HELP` | check explicite `--help` |
| `entity:validate` | 0 | `RUNS_COMMAND` | exécute la validation (lecture seule, sans effet) ; ignore `--help` |
| `sync:entity` | 1 | `OTHER_ERR` | `--help` traité comme nom d'entité → erreur PascalCase |
| `sync:relations` | 1 | `ARGUMENT_ERROR` | usage imprimé, exit 1 |
| `sync:landing` | 1 | `OTHER_ERR` | « Arguments inconnus : --help » |
| `build:model` | 1 | `ARGUMENT_ERROR` | usage imprimé, exit 1 |
| `check:model` | 1 | `ARGUMENT_ERROR` | usage générique multi-commandes |
| `make:public-page` | 1 | `OTHER_ERR` | `--help` traité comme nom de page |
| `make:public-list` | 1 | `OTHER_ERR` | cherche `mvc/entities/__help/__help.json` |
| `make:public-show` | 1 | `OTHER_ERR` | idem |
| `make:public-form` | 1 | `OTHER_ERR` | idem |
| `make:public-contact` | 1 | `ARGUMENT_ERROR` | « aucun argument attendu » |
| `db:init` | 1 | `OTHER_ERR` | **tente vraiment de provisionner MariaDB** (effet de bord critique) |
| `db:apply` | 0 | `OK_HELP` | **seule commande pour laquelle forge.py intercepte explicitement `--help`** (forge.py:660-665) |
| `migration:status` | 1 | `ARGUMENT_ERROR` | usage imprimé |
| `migration:apply` | 1 | `ARGUMENT_ERROR` | usage imprimé |
| `migration:make` | 0 | `OK_HELP` | usage détaillé multi-modes |
| `migration:diff` | 1 | `ARGUMENT_ERROR` | usage minimal |
| `schema:list` | 1 | `OTHER_ERR` | « option inconnue pour `schema:list` : `--help` » |
| `schema:doctor` | 1 | `OTHER_ERR` | idem |
| `rbac:validate` | 1 | `OTHER_ERR` | « option inconnue pour `rbac:validate` : `--help` » |
| `rbac:audit` | 1 | `OTHER_ERR` | idem |
| `starter:list` | 0 | `RUNS_COMMAND` | exécute le listing (lecture seule) |
| `starter:build` | 0 | `OK_HELP` | usage complet imprimé |
| `module:list` | 0 | `OK_HELP` | usage avec options `--path` |
| `module:install` | 0 | `OK_HELP` | usage avec `--dry-run` |
| `module:files` | 0 | `OK_HELP` | usage avec `--dry-run` |
| `module:routes` | 0 | `OK_HELP` | usage avec `--dry-run` |
| `auth:init` | 1 | `ARGUMENT_ERROR` | usage imprimé, exit 1 |
| `auth:doctor` | 1 | `ARGUMENT_ERROR` | usage imprimé, exit 1 |
| `auth:status` | 1 | `ARGUMENT_ERROR` | usage imprimé, exit 1 |
| `auth:list-sql` | 1 | `ARGUMENT_ERROR` | usage imprimé, exit 1 |
| `auth:user:create` | 0 | `OK_HELP` | **argparse natif** |
| `auth:user:list` | 1 | `ARGUMENT_ERROR` | dispatcher manuel, pas argparse |
| `auth:user:show` | 0 | `OK_HELP` | argparse natif |
| `auth:user:disable` | 0 | `OK_HELP` | argparse natif |
| `auth:user:enable` | 0 | `OK_HELP` | argparse natif |
| `auth:user:password` | 0 | `OK_HELP` | argparse natif |
| `auth:user:role:add` | 0 | `OK_HELP` | argparse natif |
| `auth:user:role:remove` | 0 | `OK_HELP` | argparse natif |
| `auth:user:roles` | 0 | `OK_HELP` | argparse natif |
| `mail:init` | 0 | `RUNS_COMMAND` | **crée/préserve les dossiers `storage/mail` et templates** (effet de bord) |
| `mail:test` | 1 | `ARGUMENT_ERROR` | usage imprimé |
| `mail:render` | 1 | `ARGUMENT_ERROR` | usage imprimé |
| `mail:doctor` | 0 | `RUNS_COMMAND` | exécute le diagnostic |
| `mail:logs` | 0 | `RUNS_COMMAND` | exécute le rapport |
| `docs:pdf` | 1 | `OTHER_ERR` | tente d'invoquer Quarkdown (PATH) |
| `i18n:init` | 0 | `RUNS_COMMAND` | **vérifie/écrit `translations/`** (effet de bord) |
| `i18n:check` | 0 | `RUNS_COMMAND` | exécute la vérification (lecture seule) |
| `upload:init` | 0 | `RUNS_COMMAND` | **crée `storage/uploads/{images,documents}`** (effet de bord) |
| `media:init` | 0 | `RUNS_COMMAND` | idem (alias de `upload:init`) |
| `js:init` | 1 | `ARGUMENT_ERROR` | usage imprimé |
| `deploy:init` | 0 | `RUNS_COMMAND` | exécute l'init de déploiement |
| `deploy:check` | 0 | `RUNS_COMMAND` | exécute la vérification |

---

## Commandes avec `--help` correct

**18 commandes** (29 %) — toutes ont une logique explicite, soit
`argparse`, soit une vérification manuelle `if arg in {"-h", "--help"}` :

- `make:entity`, `make:relation` — check manuel précoce dans `_parse_args`.
- `db:apply` — **seul cas** où l'interception est faite au niveau du
  dispatcher `forge.py:660-665`.
- `migration:make`, `starter:build` — check manuel dans le main.
- `module:list`, `module:install`, `module:files`, `module:routes` —
  pattern uniforme du module `forge_cli/modules.py`.
- `auth:user:create`, `auth:user:show`, `auth:user:disable`,
  `auth:user:enable`, `auth:user:password`, `auth:user:role:add`,
  `auth:user:role:remove`, `auth:user:roles` — **argparse natif**
  dans `forge_cli/auth.py` (8 commandes, le seul module de la CLI
  totalement aligné).

---

## Commandes sans `--help` exploitable

**44 commandes** (71 %), réparties en trois sous-catégories :

### A. `ARGUMENT_ERROR` — un `Usage :` est imprimé mais `exit 1` (17)

`routes:list`, `make:crud`, `make:pivot-crud`, `sync:relations`,
`build:model`, `check:model`, `make:public-contact`, `migration:status`,
`migration:apply`, `migration:diff`, `auth:init`, `auth:doctor`,
`auth:status`, `auth:list-sql`, `auth:user:list`, `mail:test`,
`mail:render`, `js:init`.

> Comportement intermédiaire : l'utilisateur voit un usage minimal mais
> le code de sortie est 1. Acceptable en CI/script comme « hint », pas
> comme contrat `--help`.

### B. `OTHER_ERR` — `--help` traité comme argument positionnel ou option inconnue (13)

`sync:entity`, `sync:landing`, `make:public-page`, `make:public-list`,
`make:public-show`, `make:public-form`, `db:init`, `schema:list`,
`schema:doctor`, `rbac:validate`, `rbac:audit`, `docs:pdf`.

> Cas dégradé : l'utilisateur reçoit un message d'erreur étranger
> (« nom d'entité invalide », « option inconnue ») et doit deviner.

### C. `RUNS_COMMAND` — la commande s'exécute, parfois avec effets de bord (13)

Lecture seule (acceptable) : `doctor`, `project:check`, `project:audit`,
`entity:validate`, `starter:list`, `mail:doctor`, `mail:logs`,
`i18n:check`, `deploy:check`.

**Effets de bord (À CORRIGER en priorité)** :

- `mail:init` — crée `storage/mail/` et copie des templates.
- `i18n:init` — crée/préserve `translations/fr.json`.
- `upload:init` / `media:init` — créent `storage/uploads/{images,documents}`.
- `deploy:init` — initialise la configuration de déploiement.

Le plus critique :

- `db:init` (classé `OTHER_ERR`) — **tente vraiment de se connecter à
  MariaDB en tant que `forge_admin`** avant d'échouer sur le droit.

> Une option `--help` ne doit jamais déclencher d'effet de bord. C'est
> une convention universelle (POSIX, GNU, argparse), et l'absence de
> respect ici peut générer des fichiers parasites ou des connexions DB
> inattendues lors d'une simple curiosité utilisateur.

---

## Causes probables

### Cause 1 — Le dispatcher central n'intercepte pas `--help`

Dans `forge.py:482-491`, seul `args[0] in ("help",
"--help", "-h")` est intercepté **avant** la sélection de la commande.
Une fois la commande choisie, `--help` n'est plus filtré : il est
transmis tel quel au `main()` de la sous-commande, qui doit donc le
gérer individuellement.

### Cause 2 — Deux styles de CLI coexistent

| Style | Modules | Conséquence |
|---|---|---|
| **Argparse natif** | `forge_cli/auth.py` (8 commandes `auth:user:*`) | `--help` géré gratuitement par `argparse` |
| **Parseur manuel** | tous les autres modules | `--help` doit être traité explicitement ; n'arrive presque jamais en pratique |

Le seul module pleinement argparse-iso est `forge_cli/auth.py`. Tous
les `forge_cli/entities/*.py`, `forge_cli/mail.py`, `forge_cli/modules.py`,
`forge_cli/i18n.py`, `forge_cli/uploads.py`, etc., utilisent un
parseur maison à base de `args[0] == "..."`. Le pattern « `--help`
explicite » a été appliqué de façon hétérogène.

### Cause 3 — Les commandes « init » ne parsent pas leurs arguments

`mail:init`, `i18n:init`, `upload:init`, `media:init`, `deploy:init`,
`db:init`, `doctor`, `project:check`, `project:audit`, `entity:validate`,
`starter:list` — toutes ces commandes **ignorent totalement leurs
arguments** : elles appellent directement la routine principale.
N'importe quel argument (y compris `--help`) est silencieusement
ignoré, et la commande s'exécute. C'est la principale cause d'effets
de bord sur `--help`.

### Cause 4 — Le seul cas correctement traité au dispatcher est `db:apply`

`forge.py:660-665` — `db:apply` est le seul endroit
où `if "--help" in args:` est testé au niveau du dispatcher, juste
avant de déléguer. C'est le pattern à généraliser, mais il faudrait
au préalable se doter d'un mécanisme de description par commande
(par ex. `HELP_TEXT = {…}`) pour éviter de hardcoder une chaîne.

### Cause 5 — Les commandes « schema:* » et « rbac:* » ont un parseur strict

Les modules récents `forge_cli/schemas/*.py`, `forge_cli/rbac_validate.py`
et `forge_cli/rbac_audit.py` rejettent explicitement les options
inconnues avec « option inconnue pour `<cmd>` : ... ». C'est plus rigoureux
que les anciens modules, mais ils ne reconnaissent pas `--help` ; le
résultat est un message hostile au lieu d'une aide. Ces modules sont
les plus simples à corriger (un seul `if "--help" in args:` à ajouter
dans leur `main`).

### Cause 6 — La doc CLI ne sert pas de garde-fou

[docs/reference/cli-commands.md](../../reference/cli-commands.md) liste
les commandes avec un usage textuel, mais sans contrat « cette
commande supporte `--help` ». Le test
`tests/meta/test_forge_help_coverage_001.py`
limite déjà l'échantillon de `TestIndividualCommandHelp` aux 11
commandes qui supportent `--help` correctement (constat lucide
documenté dans le docstring). Cette dette n'est donc pas masquée,
juste pas encore corrigée.

---

## Risques si non corrigé

1. **Effets de bord inattendus sur `--help`** — `mail:init`,
   `i18n:init`, `upload:init`, `media:init`, `deploy:init`, `db:init`
   modifient l'arborescence projet (ou se connectent à MariaDB) quand
   un utilisateur teste innocemment `forge mail:init --help`.
2. **DX dégradée** — un développeur Forge ne peut pas se reposer sur
   `--help` pour découvrir une commande. Il doit lire la doc ou
   le code source. C'est contraire à la convention POSIX/GNU.
3. **Régression possible dans `forge --help` global** — la sortie
   `forge --help` reste cohérente, mais elle ne décrit pas les
   arguments individuels ; sans `forge <cmd> --help` fiable, l'aide
   contextuelle manque.
4. **Tests qui plafonnent** — `test_forge_help_coverage_001::TestIndividualCommandHelp`
   ne paramétrise que 11 commandes au lieu des 62 ; étendre le test
   à plus de commandes provoquerait des échecs immédiats.
5. **Friction sur CI/scripts** — un `forge db:init --help` dans un
   pipeline tenterait vraiment de provisionner la base, ou
   `forge upload:init --help` créerait des dossiers parasites dans
   `/tmp` ou dans le workspace CI.

---

## Stratégie de correction recommandée

L'objectif est de découper la dette en tickets courts et homogènes,
chacun ne touchant qu'un module CLI à la fois et n'ajoutant que la
gestion de `--help`. Aucune logique métier ne doit bouger.

### Ticket recommandé en premier — `CLI-HELP-FLAGS-DISPATCHER-001`

**Objectif** : généraliser le pattern `db:apply` au niveau du
dispatcher `forge.py:482`.

**Approche minimale** : un dictionnaire `HELP_TEXT: dict[str, str]`
au niveau module, et une interception unique au début de `main()` :

```python
if len(args) >= 2 and args[-1] in ("--help", "-h"):
    text = HELP_TEXT.get(args[0])
    if text:
        print(text)
        raise SystemExit(0)
```

Le dictionnaire est rempli au fil des tickets suivants. Tant qu'une
commande n'a pas d'entrée, son comportement actuel reste inchangé
(pas de régression). C'est le **point d'entrée minimal viable** pour
ne plus avoir d'effets de bord sur `--help`.

### Ticket suivant — `CLI-HELP-FLAGS-INIT-COMMANDS-001`

**Objectif** : neutraliser en priorité les 6 commandes à effet de
bord critique (`db:init`, `mail:init`, `i18n:init`, `upload:init`,
`media:init`, `deploy:init`). Ajouter leur entrée dans `HELP_TEXT`
livré par le ticket précédent. **C'est le ticket le plus important
en termes de sécurité d'usage.**

### Ticket suivant — `CLI-HELP-FLAGS-SCHEMA-RBAC-001`

**Objectif** : ajouter `--help` aux 4 commandes récentes
(`schema:list`, `schema:doctor`, `rbac:validate`, `rbac:audit`).
Ces modules sont déjà rigoureux dans leur parseur ; ajouter un cas
`if "--help" in args: print(...); return` est trivial et homogène.

### Ticket suivant — `CLI-HELP-FLAGS-PUBLIC-PAGES-001`

**Objectif** : corriger les 5 commandes `make:public-*`, qui
interprètent actuellement `--help` comme un nom de page/entité.
Vérifier que le check `--help` arrive avant tout filesystem access.

### Ticket suivant — `CLI-HELP-FLAGS-MAIL-MIGRATIONS-001`

**Objectif** : ajouter `--help` aux commandes restantes du groupe
Mail (`mail:test`, `mail:render`, `mail:doctor`, `mail:logs`) et
Migrations (`migration:status`, `migration:apply`, `migration:diff`).
Pattern uniforme.

### Ticket suivant — `CLI-HELP-FLAGS-AUTH-COMPLETION-001`

**Objectif** : aligner les 5 commandes auth restantes (`auth:init`,
`auth:doctor`, `auth:status`, `auth:list-sql`, `auth:user:list`) sur
le style argparse déjà en place pour `auth:user:*`. Peut être un
simple ajout de `--help` manuel si la migration argparse complète
est trop lourde pour un seul ticket.

### Ticket optionnel — `CLI-HELP-FLAGS-TEST-EXTEND-001`

**Objectif** : étendre `COMMANDS_WITH_HELP_SUPPORT` dans
`tests/meta/test_forge_help_coverage_001.py`
au fur et à mesure des tickets précédents pour empêcher toute
régression. À traiter à la toute fin.

---

## Hors périmètre confirmé

Ce ticket n'a délibérément **pas** :

- modifié `forge.py` ni aucun module `forge_cli/*` ;
- migré la CLI vers `argparse` globalement ;
- corrigé une seule commande ;
- modifié la documentation `cli-commands.md` ;
- altéré le comportement métier d'aucune commande ;
- créé les tickets proposés dans le code (ils sont décrits ici, à
  ouvrir par l'utilisateur quand il le souhaitera) ;
- modifié les modules opt-in (RBAC, MFA, workflow, stats, media) ;
- ajouté ou retiré de test du dépôt.

Le seul artefact produit est ce rapport.

---

## Validations

- `python -m pytest tests/meta/test_forge_help_coverage_001.py -q` —
  **19 passed** en 2,07 s (inchangé, baseline préservée).
- `mkdocs build --strict` — Documentation built in ~9,5 s, aucun
  warning.
- `git diff --check` — silencieux.

Aucun code Python modifié → `compileall` et `ruff` non requis.

---

## Prochain ticket recommandé

**`CLI-HELP-FLAGS-DISPATCHER-001`** — poser l'infrastructure
`HELP_TEXT` au niveau du dispatcher (pré-requis de tous les tickets
suivants), puis enchaîner avec **`CLI-HELP-FLAGS-INIT-COMMANDS-001`**
pour éliminer les 6 effets de bord critiques.
