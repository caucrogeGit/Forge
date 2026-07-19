# ADR-054 : Cœur agnostique BDD et backends en opt-in

## Statut

Acceptée, Forge 1.0.0-rc.x (ticket `DB-BACKEND-OPTIN-STRATEGY-001`).
Le cœur est agnostique BDD (plus aucun pilote SGBD en dépendance) et découvre les backends par entry points exclusifs.
Quatre backends sont livrés en opt-in : `forge-mvc-mariadb`, `forge-mvc-sqlite`, `forge-mvc-postgres` et `forge-mvc-mssql`, tous au niveau plein (PostgreSQL et MSSQL promus par la révision d'ADR-084 du 2026-07-19).

---

## Date

2026-06-27

---

## Contexte

Forge ne prend en charge qu'un seul SGBD : MariaDB.
Le pilote `mariadb` est une dépendance runtime du cœur (`pyproject.toml`), et tout le code BDD est écrit pour son dialecte.

Le couplage est concentré mais réel :

- `core/database/connection.py` importe `mariadb` et utilise `mariadb.ConnectionPool` / `mariadb.PoolError` ;
- `core/database/db.py` s'appuie sur `cursor(dictionary=True)` et `lastrowid` ;
- le SQL généré (`make:crud`, `cli/entities/migrations.py`, `cli/entities/db_init.py`) emploie `AUTO_INCREMENT`, `utf8mb4`, les guillemets obliques et `INFORMATION_SCHEMA` ;
- le provisioning (`DB_ADMIN_*` vs `DB_APP_*`, `CREATE USER` / `GRANT`) suppose un serveur avec comptes ;
- le store de session BDD (`core/sessions/mariadb_store.py`) est spécifique à MariaDB.

Le besoin exprimé : prendre aussi en charge SQLite, PostgreSQL et Microsoft SQL Server, sans renier la charte.

Deux contraintes de charte cadrent la réponse :

1. Le cœur doit rester minimal et les capacités s'ajouter en briques opt-in (principe 8, ADR-004).
2. Le SQL reste visible et Forge refuse l'ORM (principe 5), ce qui interdit d'abstraire le SQL applicatif derrière un générateur de requêtes portable.

---

## Décision

**Le cœur devient agnostique BDD.**
Il ne dépend plus d'aucun pilote et ne contient aucune prise en charge d'un SGBD particulier.
Il définit un contrat de backend et un mécanisme de découverte ; chaque SGBD est fourni par un opt-in séparé qui implémente ce contrat.
MariaDB elle-même devient un opt-in (`forge-mvc-mariadb`), au même rang que les autres.

### Un seul backend à la fois

Un projet installe **au plus un** opt-in de backend BDD.
S'il n'en installe aucun, le cœur n'a pas de prise en charge BDD : la façade `core.database.db` lève une erreur explicite (« aucun backend BDD installé »).
Si plusieurs backends sont présents, `forge doctor` et le résolveur refusent de démarrer avec un message clair.

Cette exclusivité préserve le principe 11 (une seule façon officielle de faire chaque chose) : un projet, un SGBD.
Comme le SQL reste visible et qu'il n'y a qu'un SGBD par projet, le SQL applicatif reste du SQL natif assumé, sans fausse promesse de portabilité.

### Découverte par entry points

Chaque opt-in de backend s'enregistre via un entry point de packaging, dans le groupe `forge_mvc.db_backend`.
Le cœur découvre le backend installé avec `importlib.metadata.entry_points(group="forge_mvc.db_backend")`, sans configuration : l'application « voit » l'opt-in installé et se câble dessus.

Précédent dans le dépôt : `forge-mvc-testing` enregistre déjà son plugin via `[project.entry-points.pytest11]`.

Exemple de déclaration côté opt-in :

```toml
[project.entry-points."forge_mvc.db_backend"]
mariadb = "forge_mvc_mariadb.backend:MariaDBBackend"
```

Une variable d'environnement facultative (`DB_BACKEND`) tranche les cas ambigus et sert de garde-fou explicite, mais n'est pas requise dans le cas nominal.

### Le contrat de backend

Un backend fournit trois facettes au cœur :

1. **Connexion** : ouverture, pool éventuel, restitution, et un curseur restituant les lignes en dictionnaires (remplace l'usage direct de `cursor(dictionary=True)`).
2. **Exécution** : la sémantique de `fetch_one`, `fetch_all`, `execute` et `insert`, dont la stratégie d'insertion qui renvoie l'identifiant créé (`lastrowid` en MariaDB et SQLite, `RETURNING` en PostgreSQL, `OUTPUT` ou `SCOPE_IDENTITY()` en SQL Server).
3. **Dialecte et provisioning** : style de paramètres (`?` ou `%s`), guillemets d'identifiants, syntaxe d'auto-incrément, requêtes d'introspection, et la mise en place via `db:init` (MariaDB crée base et comptes ; SQLite crée un fichier ; PostgreSQL crée base et rôle).

Le cœur définit ce contrat sous forme de `Protocol` (ou ABC) plus un objet `Dialect`.
Les générateurs (`make:crud`, migrations) demandent le dialecte au backend actif au lieu d'émettre du SQL MariaDB en dur.

### Ce qui reste dans le cœur

- La façade publique `core.database.db` (`fetch_one`, `fetch_all`, `execute`, `insert`), qui délègue au backend actif.
- Le résolveur de backend : découverte, exclusivité mutuelle, erreur « aucun backend ».
- Les définitions du contrat (`Protocol`, `Dialect`).
- La répartition des commandes `db:*` vers le provisioning du backend actif.

Le store de session adossé à la BDD utilise la façade générique ou passe dans l'opt-in du backend ; il ne référence plus MariaDB directement.

---

## Conséquences

Positives :

- Cœur réellement minimal et agnostique BDD, fidèle à ADR-004 et au principe 8.
- Prise en charge de nouveaux SGBD sans toucher au cœur : il suffit d'un nouvel opt-in.
- La tension du principe 11 disparaît grâce à l'exclusivité mutuelle.
- Mise en cohérence avec les extractions déjà faites (Pillow ADR-018, mail ADR-022, i18n ADR-027).

Coûts et limites :

- Rupture interne : `mariadb` quitte les dépendances du cœur ; le squelette dépend désormais de `forge-mvc` plus un opt-in de backend, et `forge new` doit poser le bon backend. Acceptable avant le tag 1.0.0 stable (pas d'alias de dépréciation requis).
- Refactor de `core/database`, des générateurs (`cli/entities`) et du store de session.
- Le SQL applicatif reste lié au SGBD choisi : Forge rend le cadre pluggable, pas le SQL utilisateur portable. C'est assumé (principe 5).
- La matrice de tests grandit ; un harnais d'intégration par backend devient nécessaire.

---

## Trajectoire

1. **`forge-mvc-mariadb`** : extraire le code existant derrière le nouveau contrat, sans changement de comportement. Le cœur perd sa dépendance `mariadb`.
2. **`forge-mvc-sqlite`** : backend sans serveur ni comptes (fichier), idéal en développement, tests et onboarding sans installation.
3. **`forge-mvc-postgres`** : backend de production alternatif (placeholders `%s`, `RETURNING`).
4. **`forge-mvc-mssql`** : à la demande, dialecte propriétaire (`IDENTITY`, crochets, `OUTPUT`).

---

## Alternatives rejetées

**Garder MariaDB dans le cœur, les autres en opt-in.**
Moins de rupture, mais le cœur n'est plus minimal et MariaDB reste un cas privilégié, ce qui rouvre la tension du principe 11.

**Introduire un ORM ou un générateur de requêtes portable.**
Résoudrait la portabilité du SQL applicatif, mais contredit frontalement le principe 5 (SQL visible) et le périmètre du cœur.

**Autoriser plusieurs backends simultanés.**
Multiplierait les façons de faire (principe 11) et le SQL applicatif ne serait de toute façon pas portable. Un projet, un SGBD.

---

## Charte appliquée

Principe 5 (garder SQL visible), principe 8 (noyau minimal, briques opt-in), principe 11 (une seule façon officielle de faire chaque chose), ADR-004 (périmètre du cœur), ADR-052 (stratégie des opt-ins).

---

## Addendum : extraction du store de session BDD (AUDIT-SESSION-STORE-EXTRACT-001)

L'ADR notait que `core/sessions/mariadb_store.py` restait spécifique MariaDB dans un cœur voulu agnostique.
Le volet backend (contrat `Dialect`) et le volet générateurs (ADR-070) ont été livrés, mais le store de session était resté en l'état.

Ce volet est désormais réalisé de la façon suivante :

- le store BDD quitte le cœur pour l'opt-in **`forge-mvc-sessions-db`**, sous le nom générique **`DbSessionStore`** ;
- le cœur ne fournit plus que `MemorySessionStore`, `FileSessionStore` et le contrat `SessionStore` (un cœur agnostique n'embarque pas de store BDD) ;
- le SQL du store devient portable : les horodatages (`created_at`, `updated_at`, comparaison d'expiration) sont calculés côté Python et passés en paramètres, supprimant toute fonction propriétaire (`NOW()` MariaDB, `GETDATE()` SQL Server, `datetime('now')` SQLite). Le store fonctionne donc sur tous les backends via `core.database.db` ;
- un seul store générique est publié (pas de copie par backend) : configuration via `forge.configure(session_store=DbSessionStore())`.
