# ADR-084 : Niveaux de support des backends BDD pour la série 1.x

## Statut

Acceptée.
Décision de périmètre produit ; relève du mainteneur.
Révisée le 2026-07-19 : PostgreSQL et MSSQL sont promus au niveau plein (voir la section « Révision »).

## Date

2026-07-14 (révision : 2026-07-19)

## Contexte

L'ADR-054 a rendu le cœur agnostique de la base de données et déplacé chaque backend dans un opt-in exclusif découvert par entry point (`forge-mvc-mariadb`, `forge-mvc-sqlite`, `forge-mvc-postgres`, `forge-mvc-mssql`).
L'audit de code du 2026-07-14 a mesuré l'écart entre le contrat et la promesse effective :

- le Protocol `Dialect` (21 méthodes) et le Protocol `DatabaseBackend` sont implémentés à signature identique par les quatre backends, sans `NotImplementedError` ;
- mais `auth:init` émet un DDL exclusivement MariaDB (`ENGINE=InnoDB`, `AUTO_INCREMENT`, `utf8mb4`) quel que soit le backend installé ;
- la génération des relations `many_to_one` code en dur `ALTER TABLE ... ADD CONSTRAINT`, inapplicable sur SQLite, alors que le chemin `many_to_many` voisin est entièrement dialectal ;
- `db:init` refuse tout backend serveur autre que MariaDB, et aucun SQL de provisioning n'existe pour PostgreSQL ni MSSQL ;
- aucun test d'intégration n'exécute une vraie connexion PostgreSQL ou MSSQL, et la récupération d'identité d'insertion y est probablement défectueuse (`SCOPE_IDENTITY()` exécuté hors du scope de l'INSERT côté MSSQL, `SELECT lastval()` fragile côté PostgreSQL).

Le classifier « Alpha » des deux paquets n'était adossé à aucune définition opposable.
Un utilisateur ne pouvait pas savoir ce qu'« Alpha » garantissait ni où la promesse s'arrêtait.
La charte impose de révéler l'écart avant de le corriger (règle B) et de traiter une API publiée comme un contrat de complétude (principe 10).

## Décision

La série 1.x distingue deux niveaux de support opposables.

### Niveau plein : MariaDB et SQLite

- Tout chemin de génération SQL du framework (CRUD, migrations, relations, `auth:init`, provisioning applicable au backend) doit produire du SQL applicable sur ces deux backends, en passant par le dialecte.
- Les deux backends sont couverts par des tests d'intégration réelle (MariaDB en service CI, SQLite en base réelle locale).
- Un chemin qui ne peut pas être honoré sur l'un des deux (exemple : provisioning de comptes serveur, sans objet sur SQLite) doit le dire explicitement, jamais produire du SQL inapplicable.

### Niveau Alpha : PostgreSQL et MSSQL (jusqu'à la révision du 2026-07-19)

- Publiés sur PyPI, contrat `Dialect`/`DatabaseBackend` implémenté, utilisables pour l'exécution de SQL applicatif.
- Aucune garantie de bout en bout sur les chemins de génération et de provisioning.
- Tout chemin non garanti doit **refuser explicitement** avec un message qui nomme la limite et le niveau de support (règle B) ; produire silencieusement du SQL d'un autre dialecte est un bug.
- Le classifier PyPI reste « Alpha » et la doc de référence de chaque paquet énonce ce périmètre.

Ce niveau reste défini pour tout backend futur (voir Limites) ; depuis la révision du 2026-07-19, plus aucun backend livré ne s'y trouve.

### Critères de promotion d'un backend Alpha au niveau plein

Une promotion se fait par révision du présent ADR, quand tous ces critères sont remplis :

1. `db:init` sait générer (et exécuter avec `--run`) le provisioning du backend ;
2. la récupération d'identité d'insertion est correcte et testée (`INSERT ... RETURNING`, `OUTPUT INSERTED`) ;
3. un service CI exécute la suite `-m db` contre une vraie instance du backend ;
4. les chemins de génération SQL (CRUD, migrations, relations, `auth:init`) sont validés dialectalement sur ce backend ;
5. la doc de référence du paquet ne porte plus la mention Alpha.

## Révision du 2026-07-19 : promotion de PostgreSQL et MSSQL au niveau plein

Les critères 1 à 4 sont remplis et prouvés en CI contre de vraies instances (PostgreSQL 16, SQL Server 2022) ; le critère 5 est réalisé par la présente révision.

1. `forge db:init` génère et exécute (`--run`) le provisioning des deux backends (`PG-DB-INIT-PROVISIONING-001`, `MSSQL-DB-INIT-PROVISIONING-001`) ; l'escape hatch `DB_APP_PRIVILEGES` au-delà du DML reste propre à MariaDB et est refusé explicitement.
2. L'identité d'insertion est correcte et prouvée face aux moteurs : `lastval()` sous garde savepoint côté PostgreSQL (`PG-INSERT-IDENTITY-001`), `SCOPE_IDENTITY()` exécuté dans le lot de l'INSERT côté SQL Server (`MSSQL-INSERT-IDENTITY-001`, corrige un retour NULL systématique).
   Le mécanisme retenu est l'équivalent sémantique, au niveau de l'adaptateur, des exemples `INSERT ... RETURNING` / `OUTPUT INSERTED` cités plus haut : il rend `lastrowid` fiable pour tous les appelants de `db.insert` sans réécrire le SQL applicatif visible.
3. Deux jobs CI dédiés (`tests-db-postgres`, `tests-db-mssql`) exécutent les suites `-m db_pg` / `-m db_mssql` contre de vrais serveurs, avec le même garde anti « vert avec 0 test » que MariaDB (`FORGE_REQUIRE_DB_PG`/`FORGE_REQUIRE_DB_MSSQL`).
4. Les chemins de génération sont validés dialectalement : entités (`build_entity_sql`), socle `auth:init`, relations `many_to_one` (`PG/MSSQL-DIALECT-PARITY-TESTS-001`), et le runner de migrations (application, idempotence, dry-run, refus CHANGED, rollback réel, introspection `information_schema`) face aux vrais serveurs (`PG-MIGRATIONS-INTEGRATION-001`, `MSSQL-MIGRATIONS-INTEGRATION-001`).

Effets de la promotion :

- les quatre backends livrés sont au niveau plein ; le classifier PyPI de `forge-mvc-postgres` et `forge-mvc-mssql` passe à « 4 - Beta », comme `forge-mvc-mariadb` et `forge-mvc-sqlite` ;
- les mentions Alpha sont retirées des docstrings, README, docs de référence et parcours welcome des deux paquets, ainsi que de la doc du cœur et de la landing ;
- les messages de refus de `db:init` pour PostgreSQL et MSSQL sont remplacés par le provisioning réel (seul un backend inconnu est encore refusé, règle B).

## Conséquences

- Tickets dérivés immédiats, tous livrés : `AUTH-INIT-DIALECT-DDL-001` (DDL d'`auth:init` via le dialecte), `ENTITIES-RELATIONS-DIALECT-001` (chemin `many_to_one` dialectal ou refus explicite).
- Ticket différé, non bloquant pour 1.0 : `CI-DB-POSTGRES-001` (service PostgreSQL en CI, premier pas vers la promotion), livré, ainsi que `CI-DB-MSSQL-001`.
- Les messages de refus existants de `db:init` pour PostgreSQL et MSSQL sont conservés et doivent référencer ce niveau de support (caduc depuis la révision : `db:init` provisionne les deux backends).
- La landing et la doc ne présentent pas les quatre backends comme équivalents : deux tenus, deux en aperçu (caduc depuis la révision : quatre backends au niveau plein).

## Limites

- Cet ADR n'engage aucun calendrier de promotion de PostgreSQL ni de MSSQL (sans objet depuis la révision du 2026-07-19 : promotion réalisée).
- Il ne couvre pas l'ajout d'un cinquième backend (qui suivrait ADR-054 et entrerait directement au niveau Alpha).
