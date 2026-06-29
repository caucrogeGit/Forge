# Bases de données dans Forge

Forge laisse le choix du moteur de base de données.
Le cœur est agnostique (ADR-054) : il découvre le backend installé et n'en utilise qu'un seul par projet.
Vous installez le backend qui convient à votre projet comme un opt-in, et le code applicatif reste le même.

## 1. Le principe

Le cœur de Forge ne parle jamais directement à un moteur de base de données.
Il délègue la connexion, le dialecte SQL et le provisionnement à un backend, déclaré comme opt-in.

Un projet active un seul backend à la fois.
Les commandes `forge db:init`, `forge db:apply` et les migrations passent toutes par ce backend.

!!! note "Un backend par projet"
    Les backends sont mutuellement exclusifs : installez-en un seul par projet.
    Changer de moteur, c'est changer de backend, pas de code applicatif.

## 2. Les quatre backends

| Backend | Moteur | Serveur requis | Maturité | Idéal pour |
|---------|--------|----------------|----------|------------|
| `forge-mvc-sqlite` | SQLite | Non (un fichier) | RC | démarrer, prototyper, tester |
| `forge-mvc-mariadb` | MariaDB / MySQL | Oui | RC | production de référence |
| `forge-mvc-postgres` | PostgreSQL | Oui | Alpha | PostgreSQL (en validation) |
| `forge-mvc-mssql` | SQL Server | Oui | Alpha | SQL Server (en validation) |

!!! warning "Backends Alpha"
    PostgreSQL et SQL Server sont en Alpha : le dialecte et l'adaptateur sont testés, l'intégration de bout en bout reste à valider.
    Pour la production, préférez MariaDB ; pour démarrer sans serveur, SQLite.

## 3. SQLite, sans serveur

SQLite stocke toute la base dans un fichier (`DB_NAME`), sans serveur ni dépendance externe.
C'est le moyen le plus simple de démarrer et de tester un projet Forge.

```bash
pip install --pre forge-mvc-sqlite
```

Documentation : [backend SQLite](../sqlite/index.md) et sa [progression pas à pas](../sqlite/welcome/installation.md).

## 4. MariaDB, production de référence

MariaDB est le backend de production de référence de Forge, au-dessus d'un serveur MariaDB, avec un pool de connexions.
`forge db:init` provisionne la base et le compte applicatif avec les identifiants d'administration (`DB_ADMIN_*`, ADR-033).

```bash
pip install --pre forge-mvc-mariadb
```

Documentation : [backend MariaDB](../mariadb/index.md) et sa [progression pas à pas](../mariadb/welcome/installation.md).
Pour installer le serveur et les comptes, voir aussi [Préparer MariaDB](../install/mariadb.md).

## 5. PostgreSQL (Alpha)

PostgreSQL est disponible en Alpha : le dialecte et l'adaptateur sont en place et testés, l'intégration complète est en cours de validation.

```bash
pip install --pre forge-mvc-postgres
```

Documentation : [backend PostgreSQL](../postgres/index.md).

## 6. SQL Server (Alpha)

SQL Server est disponible en Alpha, au même stade que PostgreSQL.

```bash
pip install --pre forge-mvc-mssql
```

Documentation : [backend SQL Server](../mssql/index.md).

## 7. Comment choisir

!!! tip "Aide au choix"
    - Vous débutez, prototypez ou testez : **SQLite** (aucun serveur).
    - Vous visez la production : **MariaDB** (backend de référence, éprouvé).
    - Vous avez une contrainte PostgreSQL ou SQL Server : les backends existent en **Alpha**, à valider sur votre environnement.

Le passage d'un backend à l'autre se fait en changeant l'opt-in installé et la configuration de connexion ; le code applicatif (modèles, SQL, contrôleurs) ne change pas.

## Voir aussi

- [ADR-054 : backends de base de données opt-in](../adr/054-database-backend-optins.md) : la décision et le modèle exclusif.
- [Préparer MariaDB](../install/mariadb.md) et [Comptes MariaDB d'un projet](../install/mariadb-comptes.md) : mise en place du serveur de production.
- [Migrations SQL](../features/migrations.md) : appliquer les changements de schéma, quel que soit le backend.
