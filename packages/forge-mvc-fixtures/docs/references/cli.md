# Les modules de forge-mvc-fixtures

Ce document décrit les modules de l'opt-in `forge-mvc-fixtures` (ADR-074, ADR-076) : la classe publique `Factory` et les quatre commandes `fixtures:*`.

Les fichiers de code correspondants sont `forge_mvc_fixtures/factory.py` et `forge_mvc_fixtures/cli/`.

## 1. La classe de base `Factory` (`factory.py`)

Base des factories de fixtures, à sous-classer par entité sous `mvc/fixtures/factories/`.

| Symbole | Rôle |
|---|---|
| `Factory` | Classe de base. Attributs `table` (cible) et `locale` (Faker, défaut `fr_FR`). |
| `Factory(seed=...)` | `self.faker` (instance Faker) ; `seed` rend la génération reproductible. |
| `Factory.definition()` | Renvoie **une** ligne (dict colonne vers valeur). Cas simple. |
| `Factory.rows(count)` | Renvoie **la liste** des lignes ; par défaut répète `definition()`. Surface de code libre (boucles, conditions, tableaux). |
| `Factory.build(count)` | Produit et valide les lignes (table définie, colonnes cohérentes). Lève `FactoryError`. |
| `Factory.reference(table, key_column, value)` | Relie une colonne à l'`Id` d'une autre table par une clé naturelle (ADR-077). Renvoie un `FixtureReference`. |
| `FixtureReference` | Sentinelle de référence ; `fixtures:generate` la rend en sous-requête `(SELECT Id FROM ... LIMIT 1)`. |
| `FactoryError` | Factory mal définie. |

Pour ce que le SQL statique ne peut pas exprimer (import, agrégats), une **fixture callable** sous-classe `Fixture` (`factory.py`, ADR-078) dans `mvc/fixtures/<nom>.py` :

| Symbole | Rôle |
|---|---|
| `Fixture` | Classe de base d'un hook Python. `tables` et `depends_on` pour l'ordre et la purge. |
| `Fixture.load()` | Persiste les données (écrit via `core.database.db`). À surcharger. |
| `Fixture.purge(*, tx=None)` | Démonte (défaut : `DELETE FROM tables` en ordre inverse). Reçoit et propage la transaction de `fixtures:purge` (F52-bis). Surchargeable. |

La factory ne touche jamais la base et ne rend pas de SQL : elle produit des dicts. Elle est importée par le code de factory de l'utilisateur, exécuté par `fixtures:generate`.

## 2. Les commandes (`cli/`)

Découvertes par le cœur via l'entry point `forge_mvc.commands` (ADR-059). `load`, `purge` et `generate` déclarent `config: True` (config projet amorcée avant le handler, ADR-072).

### 2.1 `fixtures:load` (`cli/load.py`)

| Fonction | Rôle |
|---|---|
| `active_env()` | Nom de l'environnement actif (`APP_ENV`, défaut `dev`). |
| `collect_fixture_files(root)` | Fichiers `mvc/fixtures/*.sql`, triés par nom. |
| `collect_callable_fixtures(root)` | Fixtures callable `mvc/fixtures/*.py` (hors `factories/`, ADR-078). Lève `FixtureDiscoveryError` sur import cassé ou ambigu. |
| `order_fixture_files(root, files)` | Ordonne les `.sql` par dépendances FK (tri topologique depuis `relations.json`) ; repli sur le nom (ADR-077). |
| `order_load_units(root, sql_files, callables)` | Ordre unifié des `.sql` et fixtures callable (`LoadUnit`) par graphe fournit/dépend : FK de `relations.json`, sous-requêtes `reference()` et `depends_on` (ADR-078, F50/F51). |
| `split_sql_statements(sql)` | Découpe un script en instructions, en respectant les chaînes `'...'`. |
| `load_fixtures(root, *, run, force, env, no_fk_checks=False)` | Affiche puis (si `run`) exécute les unités (SQL et `load()` callable). Codes : 0, 2, 1. |
| `main(args)` | Point d'entrée ; lit `--run`, `--force`, `--no-fk-checks`. |

### 2.2 `fixtures:purge` (`cli/purge.py`)

| Fonction | Rôle |
|---|---|
| `collect_target_tables(files)` | Tables peuplées par les `.sql`, par ordre de première apparition. |
| `purge_fixtures(root, *, run, force, env)` | Démonte dans l'ordre inverse **exact** du chargement (`order_load_units` renversé) : `.sql` (`DELETE FROM`) et callable (`purge(tx=...)`), enfants avant parents (F52), dans **une transaction unique** encadrée par la désactivation FK du dialecte (F52-bis, `foreign_key_checks_ddl`). |
| `main(args)` | Point d'entrée ; lit `--run` et `--force`. |

### 2.3 `fixtures:generate` (`cli/generate.py`)

| Fonction | Rôle |
|---|---|
| `load_factory(root, entity)` | Importe et instancie la factory de l'entité. |
| `render_value(value, dialect)` | Rend une valeur : sous-requête pour un `FixtureReference` (ADR-077), sinon `dialect.render_literal`. |
| `render_inserts(table, rows, dialect)` | Rend les lignes en `INSERT INTO` (via `render_value`). |
| `timestamp_columns(root, entity)` | Colonnes timestamps `NOT NULL` de l'entité si `options.timestamps` (F46). |
| `apply_timestamps(rows, columns)` | Complète les lignes avec les timestamps manquants (horodatage déterministe ; ne surcharge pas la factory). |
| `generate_fixtures(root, entity, *, rows, seed, force, dialect)` | Affiche puis écrit `mvc/fixtures/<table>.sql` (write-if-new). Codes : 0, 2, 1. |
| `main(args)` | Point d'entrée ; lit `<entity>`, `--rows`, `--seed`, `--force`. |

### 2.4 `fixtures:make-factory` (`cli/make_factory.py`)

| Fonction | Rôle |
|---|---|
| `column_for_field(field)` | Colonne SQL réelle d'un champ (délègue à `forge-mvc-entities`, repli sur le nom ; ADR-077). |
| `provider_for_field(field)` | Provider Faker deviné pour un champ (par type, puis par nom pour les champs textuels). |
| `reference_expr(target_table)` | Scaffold `self.reference(...)` pour une clé étrangère (ADR-077). |
| `fk_targets(root, entity)` | Colonnes FK de l'entité vers leur table cible, depuis `relations.json`. |
| `render_factory(contract, *, fk_map=None)` | Rend le code Python d'une factory riche (colonnes réelles, références FK). |
| `make_factory(root, entity, *, force)` | Affiche puis écrit `mvc/fixtures/factories/<entity>_factory.py` (write-if-new). |
| `main(args)` | Point d'entrée ; lit `<entity>` et `--force`. |

## 3. Contrat commun

- affichage par défaut, `--run` pour exécuter (`load`/`purge`, charte §7) ; `generate`/`make-factory` écrivent un fichier (write-if-new, §9) ;
- `-h` / `--help` intercepté sans effet (ADR-072) ;
- exécution SQL via `core.database.db` (connexion applicative), jamais la connexion d'administration.

## 4. Voir aussi

- [Référence de forge-mvc-fixtures](../reference.md) : rôle, commandes, API, exemples.
- [Welcome-Fixtures](../welcome/debutant/fixtures-welcome.md) : parcours d'apprentissage.
