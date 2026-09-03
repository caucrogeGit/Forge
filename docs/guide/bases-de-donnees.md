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
| `forge-mvc-postgres` | PostgreSQL | Oui | RC | production sur PostgreSQL |
| `forge-mvc-mssql` | SQL Server | Oui | RC | production sur SQL Server |

!!! note "Quatre backends au niveau plein"
    Les quatre backends sont au niveau plein (ADR-084, révision du 2026-07-19) : dialecte, provisioning `db:init` et intégration validés en continu contre de vrais serveurs.
    MariaDB reste la référence historique de production ; SQLite reste le démarrage sans serveur.

## 3. SQLite, sans serveur

SQLite stocke toute la base dans un fichier (`DB_NAME`), sans serveur ni dépendance externe.
C'est le moyen le plus simple de démarrer et de tester un projet Forge.

```bash
pip install --pre forge-mvc-sqlite
```

Documentation : [backend SQLite](../sqlite/index.md) et sa [progression pas à pas](../sqlite/welcome/debutant/sqlite-welcome.md).

## 4. MariaDB, serveur de production

MariaDB est un backend de production pour Forge, au-dessus d'un serveur MariaDB, avec un pool de connexions.
`forge db:init` provisionne la base et le compte applicatif avec les identifiants d'administration (`DB_ADMIN_*`, ADR-033).

```bash
pip install --pre forge-mvc-mariadb
```

Documentation : [backend MariaDB](../mariadb/index.md) et sa [progression pas à pas](../mariadb/welcome/debutant/mariadb-welcome.md).
Pour installer le serveur et les comptes, voir aussi [Préparer MariaDB](../install/mariadb.md).

## 5. PostgreSQL

PostgreSQL est un backend de niveau plein : dialecte, provisioning `forge db:init` (affiché par défaut, `--run` pour exécuter) et intégration validés en CI contre un vrai serveur.

```bash
pip install --pre forge-mvc-postgres
```

Documentation : [backend PostgreSQL](../postgres/index.md).

## 6. SQL Server

SQL Server est un backend de niveau plein, au même stade que PostgreSQL.
Il requiert un pilote ODBC système (« ODBC Driver 18 for SQL Server » par défaut).

```bash
pip install --pre forge-mvc-mssql
```

Documentation : [backend SQL Server](../mssql/index.md).

## 7. Comment choisir

!!! tip "Aide au choix"
    - Vous débutez, prototypez ou testez : **SQLite** (aucun serveur).
    - Vous visez la production : **MariaDB** (client-serveur, éprouvé), la référence historique de Forge.
    - Vous avez une contrainte PostgreSQL ou SQL Server : les deux backends sont au **niveau plein**, choisissez celui de votre environnement.

Le passage d'un backend à l'autre se fait en changeant l'opt-in installé et la configuration de connexion ; le code applicatif (modèles, SQL, contrôleurs) ne change pas.

## 8. Les écarts de dialecte, et qui les porte

Forge écrit son SQL une fois pour les quatre backends.
Ce n'est possible que parce que le contrat `Dialect` porte chaque écart, et il en existe plus qu'on ne croit (`DOC-DIALECT-ECARTS-001`).

Cette section les nomme.
Un écart connu se contourne ; un écart ignoré se découvre en production, sur le seul backend où il mord.

### Borner un nombre de lignes

| Backend | Forme |
|---|---|
| MariaDB, SQLite, PostgreSQL | `LIMIT ? OFFSET ?` |
| SQL Server | `OFFSET ? ROWS FETCH NEXT ? ROWS ONLY` |

T-SQL ne connaît pas `LIMIT`, et sa forme **inverse l'ordre des deux paramètres** : le décalage précède le nombre de lignes.

!!! danger "Les deux méthodes vont par paire"
    `pagination_clause()` rend la clause, `pagination_param_order()` rend l'ordre des paramètres.

    Lire la première sans la seconde produit une pagination inversée, silencieuse : la page 2 affiche les lignes 20 à 40 au lieu de 10 à 20, et personne ne s'en aperçoit avant de compter.

La clause de T-SQL exige par ailleurs un `ORDER BY`, là où les trois autres l'acceptent sans.

### Les booléens

| Backend | Vrai | Type de colonne |
|---|---|---|
| MariaDB | `1` | `BOOLEAN`, alias de `TINYINT(1)` |
| SQLite | `1` | `INTEGER` |
| PostgreSQL | `TRUE` | `BOOLEAN` natif |
| SQL Server | `1` | `BIT` |

PostgreSQL est le seul à refuser `1` là où un booléen est attendu, et le seul à rendre un vrai `bool` en lecture.
Les trois autres rendent un entier, que Python considère comme vrai ou faux sans se plaindre.

!!! warning "Un `DEFAULT` de booléen n'est pas un littéral de requête"
    `Dialect.boolean_default_literal()` est distinct de `render_literal()` (ADR-075).

    Le premier écrit du DDL, relu et joué une fois ; le second écrit un artefact de données. Les confondre marcherait sur trois backends et casserait sur PostgreSQL.

### L'insertion conditionnelle

Aucune forme n'est portable, et Forge n'en fournit **aucune**.

| Backend | Forme propre au moteur |
|---|---|
| MariaDB | `INSERT ... ON DUPLICATE KEY UPDATE` |
| SQLite | `INSERT ... ON CONFLICT DO UPDATE` |
| PostgreSQL | `INSERT ... ON CONFLICT DO UPDATE` |
| SQL Server | `MERGE`, avec ses propres pièges de concurrence |

!!! info "Pourquoi Forge n'en propose pas"
    Les quatre formes n'ont pas la même sémantique de verrouillage, et `MERGE` de SQL Server est connu pour des conditions de course que les trois autres n'ont pas.

    Une abstraction qui les recouvrirait promettrait une équivalence qui n'existe pas. Le motif portable est de **tenter l'insertion et de rattraper le doublon**, `UniqueViolationError` étant qualifiée sur les quatre backends.

### Les erreurs

Aucun signal n'est portable, et c'est pourquoi Forge les traduit.

| Condition | MariaDB | SQLite | PostgreSQL | SQL Server |
|---|---|---|---|---|
| Doublon | errno 1062 | message | SQLSTATE 23505 | numéro 2627 ou 2601 |
| Clé étrangère | errno 1451, 1452 | message | SQLSTATE 23503 | numéro 547 |
| Droit refusé | errno 1044, 1142, 1227 | sans objet | SQLSTATE 42501 | numéro 229 |

!!! danger "Le SQLSTATE ne discrimine pas partout"
    MariaDB rend `23000` pour un doublon **comme** pour un `NOT NULL` et pour une clé étrangère.

    SQL Server rend `23000` pour les trois également. Seuls l'errno et le numéro natif discriminent, et c'est pourquoi le contrat les lit plutôt que le SQLSTATE.

!!! warning "Un message d'erreur est traduit"
    PostgreSQL rend « droit refusé pour ... » sur un serveur en français.

    Le message n'est donc jamais un signal, sauf sur SQLite, qui ne traduit pas les siens et n'offre rien d'autre.

Attrapez `core.database.errors.UniqueViolationError` et `ForeignKeyViolationError`, jamais `mariadb.IntegrityError` : une application qui attrape l'exception d'un pilote n'est portable sur aucun autre backend (ADR-054).

### Ce qui reste hors du contrat

L'extraction d'une date, la troncature d'un horodatage, l'ajout d'un intervalle et le rendu d'un littéral y sont, chacun avec sa méthode.

Les fonctions de fenêtrage n'y sont **pas** : les quatre les écrivent différemment, et une abstraction masquerait quatre dialectes derrière un générateur, ce que le principe 5 refuse.
Une application qui en a besoin écrit son SQL, et sait alors sur quel backend elle tourne.

## Voir aussi

- [ADR-054 : backends de base de données opt-in](../adr/054-database-backend-optins.md) : la décision et le modèle exclusif.
- [Préparer MariaDB](../install/mariadb.md) et [Comptes MariaDB d'un projet](../install/mariadb-comptes.md) : mise en place du serveur de production.
- [Migrations SQL](../features/migrations.md) : appliquer les changements de schéma, quel que soit le backend.
