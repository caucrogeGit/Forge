# ADR-059 : Registre de dispatch des commandes CLI

## Statut

Accepté (2026-06-30). Premier incrément livré : table de dispatch des
commandes opt-in.

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

### Périmètre exact de l'incrément

Sont déplacés dans la table : `upload:init`/`media:init`, `mail:*`,
`settings:init`, `audit:init`, `jobs:init`, `notifications:init`, `iot:*`,
`audio:doctor`, `video:*`, `admin:*`, `deploy:*`, `rbac:*`.

Restent dans `forge.py` (hors périmètre de cet incrément) :

- les commandes du cœur (`new`, `run`, `make:*`, `db:*`, `migration:*`,
  `doctor`, `project:*`, `routes:list`, `auth:*`, etc.) ;
- `make:pivot-crud`, qui porte un contrôle d'arguments spécifique avant
  l'import paresseux ;
- les commandes qui importent paresseusement un module **du cœur** sans
  sémantique « opt-in non installé » (`agents:init`, `opt-in:*`, `schema:*`,
  `docs:pdf`).

## Conséquences

- Ajouter ou retirer une commande opt-in se fait par une ligne de table,
  sans toucher la chaîne `if/elif` du cœur.
- `forge.py` rétrécit (suppression d'environ 230 lignes dupliquées) et cesse
  de grossir à chaque opt-in.
- Fondation posée pour des incréments ultérieurs (tickets distincts) :
  registre des commandes du cœur, puis découverte des commandes opt-in par
  *entry points* (à l'image des backends BDD, ADR-054), pour que chaque opt-in
  déclare ses commandes sans aucune entrée dans le cœur.

## Alternatives écartées

- **Découverte automatique par scan de paquets** : rejetée, magie cachée
  (principe 3) ; on préfère une table explicite, puis des *entry points*
  déclaratifs.
- **Tout réécrire d'un coup (cœur + opt-ins)** : rejeté, contraire à « petits
  tickets, une responsabilité » et risqué sur un fichier central testé par de
  nombreuses suites.
