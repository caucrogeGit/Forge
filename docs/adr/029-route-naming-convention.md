# ADR-029 — Convention de déclaration des routes (chemin et nom)

## Statut

Accepté — Forge 1.0.0-beta.15 (ticket `ROUTE-CONVENTION-ADR-029`).

Remplace la convention implicite jusqu'ici portée par le générateur `make:crud`
(`<ressource>_<action>`, chemins REST) et le ticket
`SKELETON-ROUTE-NAME-CONVENTION-001` (`home_index`).

---

## Date

2026-06-08

---

## Contexte

Les routes Forge étaient déclarées de façon **hétérogène** : le générateur
`make:crud` produit des noms `<ressource>_<action>` (underscore) avec des chemins
REST (`/notes`, `/notes/{id}/edit`), tandis que les parcours pédagogiques et le
squelette utilisaient des chemins et noms ad hoc. Aucune règle unique ne disait,
à partir d'un contrôleur et d'une méthode, **quel chemin** et **quel nom** une
route doit porter.

Le mainteneur fixe une convention **mécanique et prévisible**, dérivée du
contrôleur et de la méthode cibles, applicable aux starters (actuels et futurs),
au squelette, aux parcours welcome et au code généré par `make:crud`.

---

## Décision

Une route Forge dérive **mécaniquement** du contrôleur et de la méthode qu'elle
vise.

### Jetons

- **Jeton contrôleur** : nom de la classe sans le suffixe `Controller`.
  - dans le **chemin** : en kebab-case (`WelcomeController` → `welcome`,
    `UserProfileController` → `user-profile`) ;
  - dans le **nom** : en snake_case (`welcome`, `user_profile`).
- **Jeton méthode** : nom de la méthode Python.
  - dans le **chemin** : en kebab-case (`query_params` → `query-params`) ;
  - dans le **nom** : tel quel, underscore conservé (`query_params`).

### Chemin (URL)

- Méthode `index` : **uniquement le jeton contrôleur** (`/welcome`, `/user-profile`).
- Toute autre méthode : `/<contrôleur>/<méthode>`, suivi des paramètres de route
  s'il y en a (`/note/edit/{id}`).

### Nom (`name=`)

- Toujours `<contrôleur>-<méthode>`, séparateur **tiret** (`welcome-index`,
  `welcome-query_params`, `note-edit`).

### Exemples

| Contrôleur.méthode | Chemin | `name=` |
|---|---|---|
| `WelcomeController.index` | `/welcome` | `welcome-index` |
| `WelcomeController.query_params` | `/welcome/query-params` | `welcome-query_params` |
| `NoteController.index` | `/note` | `note-index` |
| `NoteController.edit` (id) | `/note/edit/{id}` | `note-edit` |
| `ArticleController.create` | `/article/create` | `article-create` |

### Exception : la racine de l'application

Le point d'entrée de l'application reste la racine `/`. `HomeController.index`
est donc mappé sur `/` (et non `/home`), avec le nom `home-index`. C'est la
**seule** exception au « chemin = jeton contrôleur » pour un index.

---

## Conséquences

### Positives

- **Une seule façon officielle** de nommer et router (charte principe 11).
- Mapping **bidirectionnel** et mécanique : d'une URL on déduit le
  contrôleur et la méthode, et inversement. Aide la lecture, la génération de
  code et l'apprentissage.
- L'index « nu » et le nom dérivé sont déjà l'intuition du générateur ; la
  convention l'étend et la fige.

### Limites / Risques

- **Rupture franche** avec la convention `make:crud` actuelle (chemins REST,
  noms underscore) et avec `home_index`. Pré-1.0, cette rupture se fait **sans
  alias ni guide de migration formel** (phase bêta).
- Les chemins sont **singuliers** (`/note`, `/article`) et exposent le nom de
  méthode (`/note/edit/{id}`) plutôt que la forme REST plurielle
  (`/notes/{id}/edit`). C'est assumé : la prévisibilité prime ici sur la
  convention REST.
- Le nom mêle deux séparateurs (`welcome-query_params` : tiret entre jetons,
  underscore dans la méthode). C'est intentionnel et documenté.

---

## Migration (tickets de suivi)

Cette convention est la cible. Sa mise en œuvre passe par des tickets dédiés,
dans cet ordre suggéré :

1. **Générateur `make:crud`** : produire chemins `/<contrôleur>/<méthode>` et
   noms `<contrôleur>-<méthode>` (index nu, racine exceptée).
2. **Parcours welcome-forge** (débutant, intermédiaire, avancé) : réaligner les
   routes des trois mini-projets.
3. **Parcours opt-in et starters restants** : réalignement.
4. **Squelette** : `home_index` devient `home-index` (racine `/` conservée).
5. **Garde-fous** : tests asservissant des noms de route mis à jour.

---

## Alternatives écartées

### A — Conserver la convention `make:crud` (REST, underscore)

Garder `<ressource>_<action>` et les chemins REST (`/notes/{id}/edit`). Écartée
par le mainteneur : la convention REST n'expose pas mécaniquement la méthode
cible, et le pluriel diverge du nom de contrôleur.

### B — Aligner uniquement les starters sur `make:crud`

Laisser `make:crud` tel quel et n'aligner que les starters. Écartée : créerait
deux conventions parallèles (principe 11).

---

## Référence

- Page de convention : [Convention de route](../contributing/route-convention.md).
- Générateur concerné : `forge_cli/entities/make_crud.py`.
- ADR-024 Bootstrap squelette dédié : [ADR-024](024-skeleton-bootstrap.md).
- Charte : `CHARTE_DOC.md` (principe 11 ; règle C, dérogation bêta pré-1.0).
