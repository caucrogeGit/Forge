# Référence par module

Modules Python de `forge-mvc-fixtures`. Le paquet expose une classe publique
(`Factory`) importée par le code de factory de l'utilisateur, et quatre commandes
CLI découvertes par le cœur.

## `factory.py` : la classe de base `Factory` (API publique)

| Élément | Rôle |
|---|---|
| `Factory` | Base d'une factory de fixtures, à sous-classer par entité. Attributs `table` (cible) et `locale` (Faker, défaut `fr_FR`). |
| `Factory(seed=...)` | `self.faker` (instance Faker) ; `seed` rend la génération reproductible. |
| `Factory.definition()` | Renvoie **une** ligne (dict colonne vers valeur). À surcharger pour le cas simple. |
| `Factory.rows(count)` | Renvoie **la liste** des lignes ; par défaut répète `definition()` `count` fois. Surchargez-la pour coder votre génération (boucles, conditions, tableaux). |
| `Factory.build(count)` | Produit et valide les lignes (table définie, colonnes cohérentes). Lève `FactoryError`. |
| `FactoryError` | Factory mal définie. |

La factory ne touche jamais la base et ne rend pas de SQL : elle produit des dicts.

## `commands.py` : table des commandes (ADR-059)

Expose `COMMANDS`, la table déclarative découverte par l'entry point
`forge_mvc.commands`. `fixtures:load`, `fixtures:purge` et `fixtures:generate`
déclarent `config: True` (config projet amorcée avant le handler, ADR-072) ;
`fixtures:make-factory` non (il ne lit qu'un contrat JSON).

## `cli/load.py` : `fixtures:load`

| Fonction | Rôle |
|---|---|
| `active_env()` | Nom de l'environnement actif (`APP_ENV`, défaut `dev`). |
| `collect_fixture_files(root)` | Fichiers `mvc/fixtures/*.sql`, triés par nom. |
| `split_sql_statements(sql)` | Découpe un script en instructions, en respectant les chaînes `'...'`. |
| `load_fixtures(root, *, run, force, env)` | Affiche puis (si `run`) exécute les fixtures. Codes : 0, 2 (refus prod), 1 (erreur SQL). |
| `main(args)` | Point d'entrée ; lit `--run` et `--force`. |

## `cli/purge.py` : `fixtures:purge`

| Fonction | Rôle |
|---|---|
| `collect_target_tables(files)` | Tables peuplées par les fixtures, par ordre de première apparition. |
| `purge_fixtures(root, *, run, force, env)` | Affiche puis (si `run`) exécute les `DELETE FROM` en ordre inverse. |
| `main(args)` | Point d'entrée ; lit `--run` et `--force`. |

## `cli/generate.py` : `fixtures:generate`

| Fonction | Rôle |
|---|---|
| `load_factory(root, entity)` | Importe et instancie la factory de l'entité. |
| `render_inserts(table, rows, dialect)` | Rend les lignes en `INSERT INTO` via `dialect.render_literal` (ADR-075). |
| `generate_fixtures(root, entity, *, rows, seed, force, dialect)` | Affiche puis écrit `mvc/fixtures/<table>.sql` (write-if-new). Codes : 0, 2 (erreur), 1 (fichier existant). |
| `main(args)` | Point d'entrée ; lit `<entity>`, `--rows`, `--seed`, `--force`. |

## `cli/make_factory.py` : `fixtures:make-factory`

| Fonction | Rôle |
|---|---|
| `provider_for_field(field)` | Provider Faker deviné pour un champ (par type, puis par nom pour les champs textuels). |
| `render_factory(contract)` | Rend le code Python d'une factory riche depuis un contrat d'entité. |
| `make_factory(root, entity, *, force)` | Affiche puis écrit `mvc/fixtures/factories/<entity>_factory.py` (write-if-new). |
| `main(args)` | Point d'entrée ; lit `<entity>` et `--force`. |

## Contrat commun des commandes

- affichage par défaut, `--run` pour exécuter (`load`/`purge`, charte §7) ; `generate`/`make-factory` affichent puis écrivent un fichier (write-if-new, §9) ;
- `-h` / `--help` intercepté sans effet (ADR-072) ;
- exécution SQL via `core.database.db` (connexion applicative), jamais la connexion d'administration.
