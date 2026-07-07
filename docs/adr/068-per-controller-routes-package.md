# ADR-068 : Routes applicatives par contrôleur dans `mvc/routes/`

## Statut

Acceptée (2026-07-07).

## Contexte

Le routage applicatif tient aujourd'hui dans un unique fichier `mvc/routes.py`.
Chaque CRUD généré par `forge make:crud` y ajoute une dizaine de routes (`index`, `new`, `create`, `show`, `edit`, `update`, `destroy`, `bulk-delete`, `bulk-delete-confirm`, `export-csv`).
Extrapolé à une application réelle avec de nombreuses entités, `mvc/routes.py` atteint vite plusieurs centaines de lignes, difficiles à lire et à maintenir.

Forge dispose pourtant déjà d'une convention de regroupement des routes : `register_<module>_routes(router)`, utilisée par les opt-ins (branchés par `register_optins(router)`, ADR-061) et par les routes d'API (`register_api_routes(router)`).
Il manque son extension aux **contrôleurs applicatifs**.

## Décision

Les routes applicatives sont réparties par contrôleur dans un package `mvc/routes/`, chaque contrôleur exposant sa fonction de branchement, et la racine du package listant **explicitement** les branchements.

### Structure

- **`mvc/routes/__init__.py`** est la racine de composition : elle crée `router`, branche la route d'accueil, appelle `register_optins(router)`, puis appelle chaque `register_<controleur>_routes(router)`.
  Le module `mvc.routes` reste importable et expose toujours `router`, donc `APP_ROUTES_MODULE=mvc.routes` et `mvc.routes.router` ne changent pas (le passage de fichier à package est transparent pour le chargeur, `core/app/app_factory.py`).
- **`mvc/routes/<snake>_routes.py`** contient, pour un contrôleur, la fonction `register_<snake>_routes(router)` qui déclare ses routes (le bloc `router.group("/<snake>") as g: g.add(...)`).

Le package `mvc/routes/` remplace le fichier `mvc/routes.py` : les deux ne peuvent coexister (même nom de module `mvc.routes`), et le package est la forme retenue.

### Branchement explicite, pas d'auto-découverte

`mvc/routes/__init__.py` **liste** chaque `register_<controleur>_routes(router)`.
Forge n'introduit pas d'auto-découverte (scan de `mvc/routes/*.py` branché automatiquement) : ce serait de la magie cachée (principe 3) et cela contredirait l'injection de routes par commande explicite (ADR-030).
Le développeur voit d'un coup d'œil, dans un seul fichier, tout ce qui est branché.

### Impact sur les générateurs

- **`forge make:crud`** génère `mvc/routes/<snake>_routes.py` (write-if-new) avec `register_<snake>_routes(router)`, et **affiche** les deux lignes à ajouter dans `mvc/routes/__init__.py` (l'import et l'appel), au lieu d'afficher le bloc de dix routes.
  La racine grossit de deux lignes par contrôleur, pas de dix.
- **`forge make:auth`** suit le même modèle : `mvc/routes/auth_routes.py` + `register_auth_routes(router)` (routes `/login`, `/logout`).
- **`forge make:public-page`** (et la famille `public:*`) est harmonisé : il génère un fichier de routes du contrôleur des pages publiques et branche de la même façon, plutôt que d'injecter directement dans la racine (évolution de l'injection d'ADR-030/ADR-051 vers le package).

## Conséquences

- Le routage d'une application reste lisible quel que soit le nombre d'entités : un fichier par contrôleur, une racine qui ne fait que brancher.
- Réutilise et généralise la convention existante `register_<x>_routes(router)`.
- Le squelette livre `mvc/routes/` (package) au lieu de `mvc/routes.py`.
- Migration d'un projet existant (rupture interne assumée en phase bêta, pas d'utilisateurs externes à protéger) : renommer `mvc/routes.py` en `mvc/routes/__init__.py`, puis déplacer chaque bloc de routes vers un `mvc/routes/<snake>_routes.py` exposant `register_<snake>_routes(router)`.
  La procédure est documentée ; un assistant éventuel fera l'objet d'un ticket à part.
- `routes:list` et le chargeur d'application sont inchangés (ils lisent `mvc.routes.router`).

## Charte appliquée

- Principe 3 (refuser la magie cachée) et ADR-030 : branchement explicite, jamais d'auto-découverte.
- Principe 8 (noyau minimal) et principe 11 (une seule façon de faire) : une seule convention de branchement, `register_<x>_routes(router)`, pour les opt-ins, l'API et désormais les contrôleurs applicatifs.
- Principe 2 (petits tickets, une responsabilité) : un fichier de routes par contrôleur, une responsabilité par fichier.
