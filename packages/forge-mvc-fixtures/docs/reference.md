# Référence

`forge-mvc-fixtures` est un opt-in **à CLI seule** (ADR-074), catégorie *exploitation et outillage*.
Il charge et purge des données de démonstration et de test à SQL visible.

## Les commandes

| Commande | Rôle |
|---|---|
| `forge fixtures:load` | Charge `mvc/fixtures/*.sql` dans la base de l'environnement actif. |
| `forge fixtures:purge` | Vide les tables ciblées par les fixtures pour repartir d'un état propre. |
| `forge fixtures:make-factory <entity>` | Échafaude une factory depuis le contrat d'entité (write-if-new). |
| `forge fixtures:generate <entity>` | Exécute la factory, affiche puis écrit `mvc/fixtures/<table>.sql`. |

`load` et `purge` suivent le même contrat.

- **Affichage par défaut** (charte §7, comme `db:init`) : sans option, la commande **montre** le SQL et n'exécute rien.
- **`--run`** exécute réellement (chargement ou purge) dans la base.
- **`--force`** est requis en plus de `--run` quand `APP_ENV=prod` : charger ou purger en production exige un geste explicite.
- **`-h` / `--help`** affiche l'aide sans aucun effet.

## Où vivent les fixtures

Les fixtures sont des fichiers `.sql` **relus** dans le projet, sous `mvc/fixtures/` :

```
mvc/
  fixtures/
    01_villes.sql
    02_contacts.sql
```

Le SQL reste visible (principe 5) : ce sont des `INSERT INTO` que vous écrivez et relisez, pas un format opaque.
Les fichiers sont chargés dans l'ordre de leur nom (préfixez par `01_`, `02_`, ...).

## Ce que fait `fixtures:load`

Il lit les fichiers dans l'ordre, affiche leur SQL, puis (avec `--run`) exécute chaque instruction via la connexion applicative `core.database.db`.
Un `;` à l'intérieur d'un littéral chaîne n'est pas un séparateur : une donnée peut contenir un point-virgule.

## Ce que fait `fixtures:purge`

Il **dérive** les tables cibles des `INSERT INTO` de vos fixtures, puis génère des `DELETE FROM` appliqués en **ordre inverse** (les tables référençantes avant les référencées, pour respecter les clés étrangères).
Il affiche ces `DELETE` avant de les exécuter : rien n'est caché (principe 3).
Il ne touche pas au schéma : c'est une remise à zéro des données, pas un `DROP`.

## Générer des fixtures avec une factory (ADR-076)

Plutôt que d'écrire les `INSERT` à la main, une **factory** décrit comment produire les lignes ; Forge en génère le `.sql`.

- `fixtures:make-factory <entity>` lit `mvc/entities/<entity>/<entity>.json` et écrit `mvc/fixtures/factories/<entity>_factory.py`, où chaque champ reçoit un provider Faker plausible deviné par type et par nom (scaffold riche).
- L'utilisateur possède ensuite ce fichier : il code sa génération dans `rows(count)` (boucles, conditions, tableaux) ou `definition()` (une ligne), avec `self.faker` disponible mais optionnel.
- `fixtures:generate <entity> --rows N --seed S` exécute la factory, rend chaque valeur via `dialect.render_literal` (correcte pour le backend installé), **affiche** le SQL puis l'écrit dans `mvc/fixtures/<table>.sql` (write-if-new).

La factory ne touche jamais la base et ne rend pas le SQL : elle produit des dicts. Le chargement reste `fixtures:load` (un seul mécanisme). `faker` est une dépendance de l'opt-in, utilisée uniquement à la génération.

## Cadrage par environnement

La commande vise la base de l'environnement actif, lu dans `APP_ENV` (défaut `dev`).
La production est protégée : `--run` seul y est refusé, il faut `--run --force`.

## Frontière avec la migration de seed (principe 11)

Une seule façon officielle par besoin :

| Besoin | Voie |
|---|---|
| Données de référence **permanentes** (partout, prod comprise) | Migration de seed écrite à la main, `forge migration:apply` |
| Données de démo/test **rejouables**, cadrées par environnement | Opt-in fixtures (`fixtures:load` / `fixtures:purge`) |

Les fixtures peuplent des tables **déjà provisionnées** : le schéma vient des migrations, les données de démo viennent des fixtures.

## Prérequis

- un backend BDD installé et configuré (par exemple `forge-mvc-sqlite` ou `forge-mvc-mariadb`) ;
- les tables ciblées déjà provisionnées (par les migrations) ;
- être à la racine d'un projet Forge (`config.py` + `env/<APP_ENV>`).
