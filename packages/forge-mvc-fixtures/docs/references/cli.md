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
| `FactoryError` | Factory mal définie. |

La factory ne touche jamais la base et ne rend pas de SQL : elle produit des dicts. Elle est importée par le code de factory de l'utilisateur, exécuté par `fixtures:generate`.

## 2. Les commandes (`cli/`)

Découvertes par le cœur via l'entry point `forge_mvc.commands` (ADR-059). `load`, `purge` et `generate` déclarent `config: True` (config projet amorcée avant le handler, ADR-072).

### 2.1 `fixtures:load` (`cli/load.py`)

| Fonction | Rôle |
|---|---|
| `active_env()` | Nom de l'environnement actif (`APP_ENV`, défaut `dev`). |
| `collect_fixture_files(root)` | Fichiers `mvc/fixtures/*.sql`, triés par nom. |
| `split_sql_statements(sql)` | Découpe un script en instructions, en respectant les chaînes `'...'`. |
| `load_fixtures(root, *, run, force, env)` | Affiche puis (si `run`) exécute les fixtures. Codes : 0, 2 (refus prod), 1 (erreur SQL). |
| `main(args)` | Point d'entrée ; lit `--run` et `--force`. |

### 2.2 `fixtures:purge` (`cli/purge.py`)

| Fonction | Rôle |
|---|---|
| `collect_target_tables(files)` | Tables peuplées par les fixtures, par ordre de première apparition. |
| `purge_fixtures(root, *, run, force, env)` | Affiche puis (si `run`) exécute les `DELETE FROM` en ordre inverse. |
| `main(args)` | Point d'entrée ; lit `--run` et `--force`. |

### 2.3 `fixtures:generate` (`cli/generate.py`)

| Fonction | Rôle |
|---|---|
| `load_factory(root, entity)` | Importe et instancie la factory de l'entité. |
| `render_inserts(table, rows, dialect)` | Rend les lignes en `INSERT INTO` via `dialect.render_literal` (ADR-075). |
| `generate_fixtures(root, entity, *, rows, seed, force, dialect)` | Affiche puis écrit `mvc/fixtures/<table>.sql` (write-if-new). Codes : 0, 2, 1. |
| `main(args)` | Point d'entrée ; lit `<entity>`, `--rows`, `--seed`, `--force`. |

### 2.4 `fixtures:make-factory` (`cli/make_factory.py`)

| Fonction | Rôle |
|---|---|
| `provider_for_field(field)` | Provider Faker deviné pour un champ (par type, puis par nom pour les champs textuels). |
| `render_factory(contract)` | Rend le code Python d'une factory riche depuis un contrat d'entité. |
| `make_factory(root, entity, *, force)` | Affiche puis écrit `mvc/fixtures/factories/<entity>_factory.py` (write-if-new). |
| `main(args)` | Point d'entrée ; lit `<entity>` et `--force`. |

## 3. Contrat commun

- affichage par défaut, `--run` pour exécuter (`load`/`purge`, charte §7) ; `generate`/`make-factory` écrivent un fichier (write-if-new, §9) ;
- `-h` / `--help` intercepté sans effet (ADR-072) ;
- exécution SQL via `core.database.db` (connexion applicative), jamais la connexion d'administration.

## 4. Voir aussi

- [Référence de forge-mvc-fixtures](../reference.md) : rôle, commandes, API, exemples.
- [Welcome-Fixtures](../welcome/debutant/fixtures-welcome.md) : parcours d'apprentissage.
