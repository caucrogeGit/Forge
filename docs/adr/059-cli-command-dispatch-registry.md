# ADR-059 : Registre de dispatch des commandes CLI

## Statut

Accepté (2026-06-30). Incréments 1 et 2 livrés : table de dispatch des
commandes opt-in (`cli/commands/optin_dispatch.py`) et table de dispatch des
commandes du cœur déléguées (`forge.py`, `CORE_COMMANDS`). Incrément 3 amorcé :
découverte des commandes opt-in par *entry points* (`forge_mvc.commands`) ;
`forge-mvc-iot` migré en pilote, le cœur ne le liste plus.

## Contexte

`forge.py` centralise la résolution de toutes les commandes CLI dans une
fonction `main()` d'environ 520 lignes : une longue chaîne de `if command
== "…"` (46 branches). Une grande partie de cette chaîne est consacrée aux
commandes livrées par les opt-ins (`mail:*`, `iot:*`, `video:*`, `audio:*`,
`admin:*`, `settings:init`, `audit:init`, `jobs:init`, `notifications:init`,
`deploy:*`, `rbac:*`, `upload:init`), chacune répétant le même bloc :

```python
if command == "iot:doctor":
    try:
        from forge_mvc_iot.cli.doctor import main as iot_doctor_main
    except ImportError:
        cli_fail("module forge-mvc-iot non installé.", hint="…")
    rc = iot_doctor_main(args[1:])
    if rc:
        sys.exit(rc)
    return
```

Conséquences :

- ajouter une commande opt-in impose de modifier le fichier central du cœur,
  ce qui contredit l'esprit « noyau minimal, briques opt-in » (charte, principe
  8) : le cœur connaît en dur la liste des commandes de chaque opt-in ;
- la duplication (le même `try/except ImportError` répété une douzaine de fois)
  est une dette de maintenance et un risque d'incohérence ;
- `main()` grossit à chaque opt-in, jamais l'inverse.

## Décision

Introduire un **registre de dispatch** explicite, hors de `forge.py`, sous
`cli/commands/`. `forge.py` reste le lanceur, mais délègue la résolution.

Cet ADR pose la direction et livre le **premier incrément** : une table
de dispatch des commandes opt-in.

- `cli/commands/optin_dispatch.py` déclare une table `OPTIN_COMMANDS`
  (nom de commande -> descripteur `OptinCommand` : module à importer
  paresseusement, paquet, mode de passage des arguments, gestion du code de
  retour) et une fonction `dispatch_optin(command, args) -> bool`.
- `forge.py` remplace tous les blocs opt-in dupliqués par un unique appel
  `if dispatch_optin(command, args): return`, placé après les branches du
  cœur et avant l'erreur « commande inconnue ».

Le comportement est **strictement préservé** : mêmes commandes, même import
paresseux (l'opt-in n'est tiré qu'à l'invocation), mêmes messages d'erreur
« module … non installé », même passage d'arguments et même gestion du code
de retour.

Le registre reste **explicite** (table de données lisible, pas de scan
d'imports caché), conforme au principe « refuser la magie cachée ».

### Incrément 1 : table opt-in (`cli/commands/optin_dispatch.py`)

Sont déplacés dans la table opt-in : `upload:init`/`media:init`, `mail:*`,
`settings:init`, `audit:init`, `jobs:init`, `notifications:init`, `iot:*`,
`audio:doctor`, `video:*`, `admin:*`, `deploy:*`, `rbac:*`.

### Incrément 2 : table des commandes du cœur déléguées (`forge.py`, `CORE_COMMANDS`)

Les commandes du cœur qui ne font que déléguer à un sous-module `cli.*` sont
décrites dans la table `CORE_COMMANDS` : `run`, `update`, `make:entity`,
`make:crud`, `make:public-*`, `make:relation`, `entity:validate`,
`sync:entity`, `js:init`, `i18n:*`, `auth:*`, `agents:init`, `opt-in:*`,
`module:*`, `docs:pdf`, `sync:relations`/`build:model`/`check:model`,
`migration:*`, `schema:*`.

**Cette table vit dans `forge.py`, pas sous `cli/commands/`**, et appelle ses
handlers via une lambda qui les résout dans les globals de `forge.py` au moment
de l'appel (liaison tardive). Raison : de nombreux tests de routage patchent le
handler sur le module (`monkeypatch.setattr(forge, "<handler>", fake)`) ; les
handlers du cœur doivent donc rester des noms patchables du module `forge`. Une
table dans un module séparé, à capture immédiate, casserait ce contrat de test.

Restent natives dans `forge.py` (hors table) les commandes que `forge.py`
implémente lui-même ou qui ont une logique propre : `new` (analyse `--profile`),
`db:init`/`db:apply`, `routes:list`, `doctor`, `project:check`,
`project:audit`, `make:pivot-crud` (contrôle d'arguments + opt-in).

## Conséquences

- Ajouter ou retirer une commande (opt-in ou cœur déléguée) se fait par une
  ligne de table, sans toucher la chaîne `if/elif`.
- `main()` de `forge.py` passe d'une chaîne de 46 branches (~520 lignes) à un
  noyau mince : quelques commandes natives, puis `dispatch_core` et
  `dispatch_optin`.
### Incrément 3 : découverte par *entry points*

Chaque opt-in déclare ses commandes CLI dans son propre `pyproject.toml` via le
groupe d'entry points `forge_mvc.commands` (à l'image des backends BDD, ADR-054),
pointant vers une table déclarative légère `<pkg>.commands:COMMANDS` (chaînes :
module, attr, `full`, `exit_rc`). `dispatch_optin` les découvre à l'exécution
(`entry_points(group="forge_mvc.commands")`, mémoïsé) et importe le handler
paresseusement à l'invocation. But final : le cœur ne liste plus aucune commande
opt-in ; ajouter une commande dans un opt-in ne touche jamais le cœur.

`all_optin_commands()` (union table statique + découverte) est la source unique
des garde-fous, quel que soit le mode d'enregistrement.

Migration incrémentale : `forge-mvc-iot` migré en pilote (retiré de la table
statique) ; les autres opt-ins suivent, paquet par paquet, jusqu'au retrait
complet de la table statique.

## Alternatives écartées

- **Découverte automatique par scan de paquets** : rejetée, magie cachée
  (principe 3) ; on préfère une table explicite, puis des *entry points*
  déclaratifs.
- **Tout réécrire d'un coup (cœur + opt-ins)** : rejeté, contraire à « petits
  tickets, une responsabilité » et risqué sur un fichier central testé par de
  nombreuses suites.
