# ADR-067 : `forge db:init` génère le SQL de provisioning par défaut

## Statut

Proposée (2026-07-07).

## Contexte

Le provisioning d'une base (créer la base, créer les comptes, accorder les
privilèges) est, par nature, une opération de **niveau serveur** : `CREATE DATABASE`
et `CREATE USER` ne s'accordent pas depuis un compte cantonné à une seule base.

Jusqu'ici, `forge db:init` réalisait ce provisioning en **se connectant** avec le
compte `DB_ADMIN_*` lu dans `env/`, qui devait donc être un compte
d'administration du **serveur** (droits `CREATE DATABASE`, `CREATE USER`, `GRANT`).
Ce choix a trois défauts :

- il fait vivre un quasi-root du serveur dans un fichier `env/`, ce qui est un
  risque et, sur une base managée ou mutualisée, tout simplement impossible : on
  n'y dispose jamais du root serveur ;
- sur Ubuntu/Debian, le root MariaDB s'authentifie par socket (`sudo mariadb`),
  sans mot de passe : fabriquer un compte serveur à mot de passe utilisable par
  Forge est un détour pénible ;
- c'est l'opération la moins conforme à la charte : Forge agit avec des
  identifiants puissants, de façon peu explicite, au lieu de montrer ce qu'il fait.

Or la charte prévoit un mode « **Forge affiche** » (§7) : produire du code à
copier-coller plutôt que d'agir silencieusement.

## Décision

`forge db:init` **génère et affiche** par défaut le script SQL de provisioning,
dérivé de `env/`, sans se connecter ni exiger de droits serveur.

- **`forge db:init`** (défaut, mode « affiche ») : lit `env/dev`
  (`DB_NAME`, `DB_HOST`, `DB_CHARSET`, `DB_COLLATION`, `DB_ADMIN_LOGIN/PWD`,
  `DB_APP_LOGIN/PWD`) et écrit sur la sortie standard le script à exécuter dans une
  session d'administration MariaDB (typiquement `sudo mariadb`).
- **`forge db:init --run`** (opt-in, mode « agit ») : exécute directement le
  provisioning, pour les contextes qui disposent d'un compte d'administration
  serveur et veulent une commande unique (CI, conteneurs, serveur auto-géré, tests
  e2e). Ce mode reprend le comportement historique et suppose donc que `DB_ADMIN_*`
  a les droits serveur nécessaires.

Le défaut est ainsi le comportement **sûr et explicite** ; l'exécution automatique
devient un choix conscient (principe « sécuriser par défaut »).

### Vérification préalable

Dans les **deux modes**, avant toute génération ou exécution, `db:init` vérifie que
les variables requises sont **renseignées** (présentes et non vides) dans `env/dev` :
`DB_NAME`, `DB_ADMIN_LOGIN`, `DB_ADMIN_PWD`, `DB_APP_LOGIN`, `DB_APP_PWD`.
(`DB_HOST`, `DB_PORT`, `DB_CHARSET` et `DB_COLLATION` ont des valeurs par défaut et
ne sont pas exigées.)

Si l'une manque ou est vide, la commande s'arrête **sans rien produire ni exécuter**
et affiche la liste précise des clés à renseigner, en rappelant `forge db:config`
pour les amorcer, puis `env/dev` pour saisir les valeurs.

`db:init` vérifie en outre que `DB_NAME` est un **nom de base valide** : non vide,
au plus 64 caractères, sans les caractères interdits par MariaDB dans un nom de base
(`/`, `\`, `.`, caractère nul ou de contrôle) ni espace en tête ou en fin. Un nom
invalide arrête la commande avec un message expliquant la règle et la valeur fautive,
avant toute génération ou exécution. Les autres caractères (dont le trait d'union)
restent admis : Forge protège l'identifiant par des accents graves (`` ` ``).

### Script généré

Le script débute par la création de la base définie dans `env/`, puis crée les
deux comptes en les **scellant à cette base** (jamais `*.*`) :

```sql
CREATE DATABASE IF NOT EXISTS `<DB_NAME>`
  CHARACTER SET <DB_CHARSET> COLLATE <DB_COLLATION>;

-- Compte d'administration de la base : DDL du schéma (db:apply, migrations).
CREATE OR REPLACE USER '<DB_ADMIN_LOGIN>'@'<DB_HOST>' IDENTIFIED BY '<DB_ADMIN_PWD>';
GRANT ALL PRIVILEGES ON `<DB_NAME>`.* TO '<DB_ADMIN_LOGIN>'@'<DB_HOST>';

-- Compte applicatif : runtime, DML uniquement.
CREATE OR REPLACE USER '<DB_APP_LOGIN>'@'<DB_HOST>' IDENTIFIED BY '<DB_APP_PWD>';
GRANT SELECT, INSERT, UPDATE, DELETE ON `<DB_NAME>`.* TO '<DB_APP_LOGIN>'@'<DB_HOST>';

FLUSH PRIVILEGES;
```

- `CREATE OR REPLACE USER` évite l'échec « 1396 » si le compte existe déjà.
- L'hôte du grant vaut `DB_HOST` (cohérent avec la connexion, ADR-066).
- Les deux comptes restent séparés (ADR-033) : administration de la base d'un côté
  (DDL), applicatif de l'autre (DML strict).

### Signification des comptes

Trois niveaux, désormais distincts et documentés :

- **root du serveur** (accès humain `sudo mariadb`) : n'apparaît **jamais** dans
  `env/` ; sert uniquement à exécuter le script généré ;
- **`DB_ADMIN_*`** : le **propriétaire de la base du projet** (droits complets sur
  `DB_NAME` seulement), utilisé par Forge pour la DDL (`db:apply`, migrations) ;
- **`DB_APP_*`** : le compte applicatif de runtime (DML strict).

L'utilisateur « Admin » de l'application, lui, n'est pas un compte MariaDB : c'est
une donnée gérée par le RBAC applicatif, qui passe par `DB_APP_*` comme tout le monde.

## Conséquences

- Le mode par défaut n'exige plus aucun identifiant serveur dans `env/` : compatible
  hébergement mutualisé et bases managées.
- Le SQL est dérivé de `env/` : pas de double saisie.
- Les parcours welcome MariaDB (« Provisionner la base ») montrent le script à
  coller, puis renvoient à `--run` pour l'exécution automatique éventuelle.
- Les tests e2e provisionnent via `db:init --run`.
- Idéalement, la génération du SQL est portée par le **backend** (son dialecte),
  pour rester agnostique BDD (ADR-054) et permettre à postgres/mssql de suivre ;
  la première mise en œuvre couvre MariaDB.
- Nuance assumée : en mode `--run`, `DB_ADMIN_*` doit avoir les droits serveur
  (comportement historique) ; en mode par défaut, `DB_ADMIN_*` désigne le compte
  scellé à la base que le script provisionne. Un raffinement ultérieur (identifiant
  de bootstrap distinct pour `--run`) fera l'objet d'un ADR dédié si le besoin
  apparaît.
- Rupture interne assumée en phase bêta (inversion du défaut de `db:init`), sans
  alias de compatibilité.

## Charte appliquée

- §7 (Forge affiche) : le provisioning devient un script montré, pas une action
  silencieuse.
- Principe 3 (refuser la magie cachée) et principe 7 (sécuriser par défaut) : le
  comportement puissant (exécuter avec des droits serveur) devient un opt-in explicite.
- Relations : révise le rôle de `DB_ADMIN_*` posé en ADR-033, s'inscrit dans le
  cœur agnostique BDD (ADR-054), lit `env/` selon ADR-060, aligne l'hôte du grant
  sur ADR-066.
