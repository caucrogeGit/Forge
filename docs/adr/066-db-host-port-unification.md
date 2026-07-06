# ADR-066 : Contrat d'environnement BDD, `DB_HOST`/`DB_PORT` partagés

## Statut

Acceptée (2026-07-06).

## Contexte

Depuis ADR-060, la configuration de connexion des backends BDD est lue dans
l'environnement, plus dans `config.py`.
Le contrat initial exposait, pour les backends client-serveur, deux jeux
complets de paramètres de connexion :

- `DB_APP_HOST`, `DB_APP_PORT`, `DB_APP_LOGIN`, `DB_APP_PWD` pour le runtime ;
- `DB_ADMIN_HOST`, `DB_ADMIN_PORT`, `DB_ADMIN_LOGIN`, `DB_ADMIN_PWD` pour le
  provisioning et la DDL (ADR-033).

Or le compte applicatif et le compte d'administration visent **le même serveur
de base de données** : `DB_APP_HOST`/`DB_APP_PORT` et `DB_ADMIN_HOST`/`DB_ADMIN_PORT`
portent, en pratique, toujours la même valeur.
Cette duplication a deux défauts :

- elle alourdit inutilement `env/dev` (deux fois la même adresse) ;
- elle crée un piège silencieux : renseigner `DB_APP_HOST` sur un serveur distant
  en oubliant `DB_ADMIN_HOST` fait retomber l'administration sur `localhost` sans
  avertissement, ce qui contredit le principe « refuser la magie cachée ».

Seuls les **identifiants** (`LOGIN`/`PWD`) portent une information réellement
distincte : deux comptes aux privilèges différents.

## Décision

Le contrat d'environnement des backends client-serveur (`forge-mvc-mariadb`,
`forge-mvc-postgres`, `forge-mvc-mssql`) unifie l'adresse du serveur :

- `DB_HOST` (défaut `localhost`) et `DB_PORT` (défaut propre au backend :
  `3306`, `5432`, `1433`) décrivent le serveur, partagés par la connexion
  applicative et la connexion d'administration ;
- `DB_NAME` nomme la base ;
- `DB_APP_LOGIN` / `DB_APP_PWD` restent le compte runtime (DML) ;
- `DB_ADMIN_LOGIN` / `DB_ADMIN_PWD` restent le compte d'administration
  (provisioning, DDL ; ADR-033) ;
- `DB_ODBC_DRIVER` reste propre à `forge-mvc-mssql`.

`DB_APP_HOST`, `DB_APP_PORT`, `DB_ADMIN_HOST` et `DB_ADMIN_PORT` disparaissent du
contrat.

Pour MariaDB, `forge db:init` continue de poser le grant
`'DB_APP_LOGIN'@'<hôte>'` ; l'hôte d'origine du grant vaut désormais `DB_HOST`.
C'est le comportement déjà en vigueur (l'ancien `DB_APP_HOST` servait à la fois
d'hôte du pool et d'origine du grant) : utiliser `DB_HOST` garantit que l'hôte du
grant coïncide avec l'hôte de connexion, ce qui évite l'écart classique entre
`localhost` (socket) et `127.0.0.1` (TCP).

Le `env_template` de chaque backend (ADR-064), amorcé par `forge db:config`,
reflète ce contrat.

## Conséquences

- `env/dev` d'un projet BDD ne porte plus qu'une seule adresse serveur.
- Les backends, `forge db:init`, `forge db:config`, l'audit projet
  (`DB_HOST` devient une clé requise) et la documentation sont alignés.
- Le déploiement (`forge-mvc-deploy`) contrôle `DB_HOST` au lieu de `DB_APP_HOST`.
- Rupture interne assumée en phase bêta (pas d'alias de compatibilité) : les
  projets existants remplacent `DB_APP_HOST`/`DB_ADMIN_HOST` par `DB_HOST` et
  `DB_APP_PORT`/`DB_ADMIN_PORT` par `DB_PORT`.
- Un déploiement où l'application et le serveur BDD sont sur des machines
  distinctes reste possible : `DB_HOST` pointe le serveur ; l'origine du grant
  suit `DB_HOST`. Un réglage plus fin de l'origine du grant, si le besoin
  apparaît, fera l'objet d'un ADR dédié plutôt que d'une duplication anticipée.

## Charte appliquée

- Principe 3 (refuser la magie cachée) : suppression du piège
  `DB_APP_HOST` renseigné / `DB_ADMIN_HOST` oublié.
- Principe 8 (noyau minimal) et principe 11 (une seule façon de faire) :
  une seule adresse serveur, une seule façon de la déclarer.
- Règle A (retirer la cause) : on retire la duplication, pas seulement son
  symptôme documentaire.
