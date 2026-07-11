# Commandes `fixtures:*` (cli/load.py, cli/purge.py)

Les deux commandes sont découvertes par le cœur via l'entry point `forge_mvc.commands` (ADR-059) et dispatchées par `dispatch_optin`.
Elles déclarent `config: True` : la config du projet (`env/<APP_ENV>`) est amorcée avant le handler, comme pour `forge migration:apply` (ADR-072).

## `fixtures:load` (`forge_mvc_fixtures.cli.load`)

| Fonction | Rôle |
|---|---|
| `active_env()` | Nom de l'environnement actif (`APP_ENV`, défaut `dev`). |
| `collect_fixture_files(root)` | Fichiers `mvc/fixtures/*.sql`, triés par nom. |
| `split_sql_statements(sql)` | Découpe un script en instructions, en respectant les chaînes `'...'`. |
| `load_fixtures(root, *, run, force, env)` | Affiche puis (si `run`) exécute les fixtures. Codes : 0, 2 (refus prod), 1 (erreur SQL). |
| `main(args)` | Point d'entrée `forge fixtures:load` ; lit `--run` et `--force`. |

## `fixtures:purge` (`forge_mvc_fixtures.cli.purge`)

| Fonction | Rôle |
|---|---|
| `collect_target_tables(files)` | Tables peuplées par les fixtures, par ordre de première apparition. |
| `purge_fixtures(root, *, run, force, env)` | Affiche puis (si `run`) exécute les `DELETE FROM` en ordre inverse. |
| `main(args)` | Point d'entrée `forge fixtures:purge` ; lit `--run` et `--force`. |

## Contrat commun

- affichage par défaut, `--run` pour exécuter (charte §7) ;
- `--run --force` requis en `APP_ENV=prod` ;
- `-h` / `--help` intercepté sans effet (ADR-072) ;
- exécution via `core.database.db` (connexion applicative), jamais la connexion d'administration.
