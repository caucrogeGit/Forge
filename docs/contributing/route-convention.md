# Convention de route Forge

Cette page décrit la **règle unique** de déclaration des routes Forge : à partir du contrôleur et de la méthode visés, elle fixe **le chemin** (URL) et **le nom** (`name=`).
Décision : [ADR-029](../adr/029-route-naming-convention.md).

!!! info "Pourquoi une règle mécanique"
    Une route doit pouvoir se déduire du contrôleur et de la méthode qu'elle vise, et inversement.
    Cela rend les routes prévisibles, faciles à lire, à générer et à apprendre.
    Une seule façon officielle de faire (charte principe 11).

## La règle

Une route vise toujours une **méthode d'un contrôleur**.
On en tire deux jetons :

- **jeton contrôleur** : le nom de la classe **sans** le suffixe `Controller` ;
- **jeton méthode** : le nom de la méthode Python.

### Le chemin (URL)

- méthode `index` : **seulement** le jeton contrôleur, en kebab-case (`/welcome`, `/user-profile`) ;
- toute autre méthode : `/<contrôleur>/<méthode>` en kebab-case, suivi des éventuels paramètres de route (`/note/edit/{id}`).

### Le nom (`name=`)

- toujours `<contrôleur>-<méthode>`, séparateur **tiret** ; le jeton méthode garde ses underscores (`welcome-index`, `welcome-query_params`, `note-edit`).

## Exemples

```python
with router.group("", public=True) as public:
    # index : chemin = nom du contrôleur seul
    public.add("GET",  "/welcome",               WelcomeController.index,        name="welcome-index")
    # autre méthode : contrôleur / méthode
    public.add("GET",  "/welcome/query-params",  WelcomeController.query_params, name="welcome-query_params")
    # méthode avec paramètre de route
    public.add("GET",  "/note/edit/{id}",        NoteController.edit,            name="note-edit")
    public.add("POST", "/note/delete/{id}",      NoteController.delete,          name="note-delete")
```

| Contrôleur.méthode | Chemin | `name=` |
|---|---|---|
| `WelcomeController.index` | `/welcome` | `welcome-index` |
| `WelcomeController.query_params` | `/welcome/query-params` | `welcome-query_params` |
| `NoteController.index` | `/note` | `note-index` |
| `NoteController.edit` (id) | `/note/edit/{id}` | `note-edit` |
| `ArticleController.create` | `/article/create` | `article-create` |
| `ArticleController.api_index` | `/article/api-index` | `article-api_index` |

## Casse des jetons

| Jeton | Dans le chemin | Dans le nom |
|---|---|---|
| Contrôleur (`UserProfileController`) | kebab-case : `user-profile` | snake_case : `user_profile` |
| Méthode (`query_params`) | kebab-case : `query-params` | tel quel : `query_params` |

## Exception : la racine de l'application

Le point d'entrée de l'application reste la racine `/`.
`HomeController.index` est donc mappé sur `/` (et non `/home`), nommé `home-index`.
C'est la **seule** exception.

```python
public.add("GET", "/", HomeController.index, name="home-index")
```

## Portée

La convention s'applique partout où des routes Forge sont déclarées : squelette, starters (actuels et futurs), parcours welcome, et code généré par `make:crud`.
La mise en conformité de l'existant est suivie par des tickets dédiés (voir [ADR-029](../adr/029-route-naming-convention.md), section Migration).
