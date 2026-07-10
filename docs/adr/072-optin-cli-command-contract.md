# ADR-072 : contrat des commandes CLI des opt-ins (amorçage config, interception de l'aide)

## Statut

Acceptée (2026-07-10).

## Contexte

Les opt-ins livrent leurs propres commandes CLI, découvertes par les entry points
`forge_mvc.commands` et exécutées par `dispatch_optin` (ADR-059). Le dispatch se
contentait d'importer le handler et de l'appeler avec les arguments.

Deux frictions remontées par le banc d'essai RéférenCiel (retour terrain 016,
F39 et F40) montrent que ce dispatch minimal n'offre pas les mêmes garanties que
les commandes du cœur :

- **F39, config projet non amorcée.** `forge sessions:gc` ouvre une connexion BDD
  via le store, mais le dispatch n'avait pas chargé la configuration du projet
  (`env/dev`). Le pool MariaDB se rabattait sur l'utilisateur système sans mot de
  passe (`Access denied`). Les commandes du cœur adossées à la base (`forge
  migration:apply`, `forge db:apply`) amorcent l'environnement via
  `load_project_config()` ; les commandes d'opt-in sautaient cette étape. Résultat :
  `sessions:gc` inutilisable en cron/systemd, précisément l'usage prévu (réponse à
  F35).

- **F40, `--help` exécute l'effet.** `forge sessions:gc --help` lançait la purge,
  `forge sessions:init --help` copiait la migration : aucune n'affichait son aide.
  Le dispatch appelait le handler sans intercepter `-h`/`--help`, contrairement aux
  commandes du cœur.

Le contrat fonctionnel des opt-ins (ici le store durci en 016) n'est pas en cause :
les deux frictions sont dans la **couche de dispatch CLI** commune.

## Décision

`dispatch_optin` (ADR-059) offre deux garanties transverses à **toutes** les
commandes d'opt-in, et la table `COMMANDS` d'un opt-in gagne une clé déclarative.

### 1. Interception de l'aide avant tout effet (F40)

Avant d'exécuter le handler, le dispatch intercepte `-h`/`--help` : il affiche
l'aide (l'aide riche `format_command_help` si elle existe, sinon une ligne
générique renvoyant à la documentation de l'opt-in) et **n'exécute jamais l'effet**.

Les commandes Forge documentées restent interceptées en amont par
`format_command_help` (dispatcher central) ; ce filet du dispatch couvre en plus
les opt-ins tiers dont les commandes n'ont pas d'aide riche enregistrée.

### 2. Amorçage déclaratif de la config projet (F39)

La table `COMMANDS` d'un opt-in peut marquer une commande adossée à la base avec
`config: True` :

```python
COMMANDS = {
    "sessions:init": {"module": "forge_mvc_sessions_db.cli.init"},
    "sessions:gc":   {"module": "forge_mvc_sessions_db.cli.gc", "config": True},
}
```

Quand ce drapeau est présent, `dispatch_optin` appelle `load_project_config()`
avant le handler : la configuration du projet est chargée (`env/dev`), avec les
mêmes identifiants applicatifs que le runtime. `load_project_config()` s'exécute
depuis la racine du projet (il y `chdir` le temps du chargement), ce qui résout
aussi les chemins relatifs de `config.py` (`load_dotenv("env/dev")`).

Le drapeau est **explicite et par commande** : une commande qui ne fait que copier
des fichiers (`sessions:init`, `audit:init`, `images:init`…) ne le pose pas et ne
paie donc pas le coût d'un projet configuré. Une commande adossée à la base
(`sessions:gc`) le pose. Rien n'est amorcé implicitement (principe 3).

Si `config: True` est posé hors d'un projet Forge (pas de `config.py`), la commande
échoue proprement avec un message renvoyant à la racine du projet, plutôt que par
une erreur de connexion opaque.

## Conséquences

- `forge sessions:gc` fonctionne en cron/systemd : il amorce `env/dev` et se
  connecte avec les identifiants applicatifs, comme `forge migration:apply`.
- Aucune commande d'opt-in n'exécute son effet sur `--help`.
- Le contrat de la table `COMMANDS` gagne une clé optionnelle `config` (défaut
  `False`) : additive, rétro-compatible avec les opt-ins existants.
- Les autres opt-ins adossés à la base (par exemple une commande qui écoute un
  flux et insère en base) peuvent adopter `config: True` au besoin ; ce n'est pas
  imposé rétroactivement dans cet ADR.
- Le store lui-même reste inchangé : il ne force pas le chargement de la config
  (au runtime, `app.py` l'a déjà chargée). L'amorçage vit dans la couche CLI, là
  où il manquait.

## Alternatives écartées

- **Amorcer la config pour toutes les commandes d'opt-in.** Rejeté : les commandes
  qui ne touchent pas la base (copie de migration, diagnostics statiques) n'en ont
  pas besoin et pourraient tourner hors d'un projet configuré. Le drapeau par
  commande est plus juste.
- **Charger la config dans le store.** Rejeté : le store est une bibliothèque
  aussi utilisée au runtime (où la config est déjà chargée) ; lui faire charger
  `env/dev` serait un couplage surprenant et une double autorité.
- **Documenter un contournement projet (script maison + cron).** Rejeté : c'est le
  contournement que le banc d'essai a dû écrire ; la charte demande de retirer la
  cause (règle A), pas de documenter le symptôme.

## Charte appliquée

- Principe 3 (refuser la magie cachée) : l'amorçage est déclaré explicitement par
  commande (`config: True`), jamais implicite.
- Principe 10 (une API publique est un contrat de complétude) : une commande CLI
  livrée doit être utilisable (config amorcée) et découvrable (`--help`), pas
  seulement présente.
- Principe 11 (une seule façon officielle) : les commandes d'opt-in adossées à la
  base s'amorcent comme les commandes du cœur, via `load_project_config()`.
- Règle A (retirer la cause) : le dispatch amorce la config au lieu de laisser
  chaque projet réécrire un script cron.
- Relations : étend le dispatch d'ADR-059, s'appuie sur la convention de
  provisioning d'ADR-071 et sur `load_project_config` (chargement d'`env/dev`,
  ADR-060/066).
