# Migration ADR-029 — Specs des tickets de suivi

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Ce document détaille les tickets de mise en œuvre de la
[convention de route ADR-029](../adr/029-route-naming-convention.md), acceptée en
bêta.15 mais pas encore implémentée.
Chaque ticket respecte le principe 2 de la charte (une responsabilité) et la
phase bêta pré-1.0 (rupture sans alias ni guide de migration formel).

La cible mécanique rappelée :

- chemin : `index` donne le jeton contrôleur nu (`/note`), toute autre méthode
  donne `/<contrôleur>/<méthode>` (`/note/edit/{id}`) ;
- nom : toujours `<contrôleur>-<méthode>`, séparateur tiret (`note-edit`) ;
- exception : `HomeController.index` reste mappé sur `/` avec le nom `home-index`.

L'ordre ci-dessous suit la section « Migration » de l'ADR-029 : le générateur
d'abord, puis les usages, puis le squelette, enfin les garde-fous.

---

## Ticket 1 — `ROUTE-029-MAKECRUD-001`

**Ce qu'il fait.** Aligne le générateur `make:crud` sur ADR-029.
Les routes produites passent des chemins REST (`/notes`, `/notes/{id}/edit`) et
noms underscore (`notes_index`, `notes_edit`) à la convention cible
(`/note`, `/note/edit/{id}` ; `note-index`, `note-edit`).

**Ce qu'il ne fait pas.** Ne touche ni aux starters, ni au squelette, ni aux
parcours welcome (tickets suivants). Ne change pas le mode d'émission
(`make:crud` reste en **affichage**, pas d'injection, conforme ADR-030).

**Fichiers concernés.**

- `forge_cli/entities/make_crud.py` (génération des chemins et noms) ;
- `forge_cli/entities/crud/` (gabarits de routes si présents) ;
- tests de garde-fou `make:crud` sous `tests/`.

**Stratégie étape par étape.**

1. Repérer dans `make_crud.py` la construction des chemins et des `name=`.
2. Introduire un dérivateur unique « (contrôleur, méthode) vers (chemin, nom) »
   appliquant les jetons ADR-029 (kebab pour le chemin, snake pour le jeton
   contrôleur du nom, méthode conservée). Centraliser plutôt que disperser.
3. Brancher le dérivateur sur les cinq actions CRUD (`index`, `show`, `create`,
   `edit`, `delete`) avec leurs paramètres de route.
4. Mettre à jour les tests de garde-fou pour asservir la nouvelle convention.

**Validations attendues.**

- `pytest -x -q` vert ;
- `python -m compileall -q .` OK ;
- `ruff check .` OK ;
- vérifier à la main la sortie de `make:crud` sur une entité d'exemple.

**Limites restantes.** Les usages déjà générés (starters, welcome) restent à
l'ancienne convention tant que les tickets 2 et 3 ne sont pas faits.

**Charte appliquée.** Principe 11 (une seule façon), principe 2 (une
responsabilité), règle C dérogation bêta.

---

## Ticket 2 — `ROUTE-029-WELCOME-001`

**Ce qu'il fait.** Réaligne les routes des trois mini-projets welcome-forge
(débutant, intermédiaire, avancé) sur ADR-029.

**Ce qu'il ne fait pas.** Ne modifie pas la pédagogie ni le contenu des paliers,
seulement les chemins et noms de route et leurs références (templates, liens,
tests).

**Fichiers concernés.**

- starters welcome-forge figés (un jeu par niveau) ;
- templates et fragments référençant les noms de route (`url_for` / équivalent) ;
- tests de parcours welcome sous `tests/`.

**Stratégie étape par étape.**

1. Lister les routes actuelles de chaque palier et leur cible ADR-029.
2. Réécrire chemins et noms côté `routes.py` de chaque starter.
3. Propager les renommages dans les templates et les liens internes.
4. Mettre à jour les tests asservissant les noms de route.

**Validations attendues.** `pytest -x -q`, `compileall`, `ruff`,
`mkdocs build --strict` (la doc welcome cite des routes).

**Limites restantes.** Starters opt-in et autres restent au ticket 3.

**Charte appliquée.** Principes 11 et 2 ; §4 (starters distribués : écriture via
le flux de figeage des starters, pas d'édition in-place hors procédure).

---

## Ticket 3 — `ROUTE-029-STARTERS-001`

**Ce qu'il fait.** Réaligne les routes des starters et parcours opt-in restants
(welcome-files, welcome-images, welcome-iot, welcome-video, etc.).

**Ce qu'il ne fait pas.** Ne touche pas au squelette (ticket 4).

**Fichiers concernés.** Jeux de starters opt-in figés, leurs templates, et les
tests associés.

**Stratégie étape par étape.** Même méthode que le ticket 2, appliquée starter
par starter, un commit par famille pour garder des diffs lisibles.

**Validations attendues.** `pytest -x -q`, `compileall`, `ruff`,
`mkdocs build --strict`.

**Limites restantes.** Aucune au terme du ticket, hors squelette.

**Charte appliquée.** Principes 11 et 2 ; §4.

---

## Ticket 4 — `ROUTE-029-SKELETON-001`

**Ce qu'il fait.** Renomme la route d'accueil du squelette `forge new` de
`home_index` vers `home-index`, la racine `/` étant conservée (exception ADR-029).

**Ce qu'il ne fait pas.** Ne change pas le chemin racine, ni d'autres routes.

**Fichiers concernés.**

- squelette `forge_cli/skeleton/` (`routes.py` et templates citant le nom) ;
- tests de garde-fou du squelette.

**Stratégie étape par étape.**

1. Remplacer `name="home_index"` par `name="home-index"` dans le squelette.
2. Propager dans tout `url_for("home_index")` du squelette.
3. Mettre à jour le test asservissant ce nom (ex. garde-fou squelette).

**Validations attendues.** `pytest -x -q`, `compileall`, `ruff`, et un
`forge new` d'essai dans un dossier jetable.

**Limites restantes.** Aucune.

**Charte appliquée.** Principe 11 ; §12 règle 2 (fichiers `_base` régénérables).

---

## Ticket 5 — `ROUTE-029-GUARDS-001`

**Ce qu'il fait.** Pose ou consolide les garde-fous transverses : un test
unique vérifiant qu'aucune route active (starters, squelette, welcome) n'emploie
plus l'ancienne convention (underscore entre jetons, chemins REST pluriels), et
que le dérivateur ADR-029 est la source unique.

**Ce qu'il ne fait pas.** N'introduit pas de nouvelle route ni de nouveau
générateur.

**Fichiers concernés.** `tests/test_ROUTE_029_*` (garde-fous d'absence et de
conformité).

**Stratégie étape par étape.**

1. Test d'absence : aucun `name="<a>_<b>"` de style ancienne convention dans les
   `routes.py` distribués (hors méthodes à underscore légitimes type
   `query_params`).
2. Test de conformité : le dérivateur produit bien les exemples du tableau
   ADR-029.

**Validations attendues.** `pytest -x -q` vert sur l'ensemble.

**Limites restantes.** Le garde-fou couvre le code distribué, pas le code
applicatif des utilisateurs (hors périmètre Forge).

**Charte appliquée.** Principe 6 (tester avant d'élargir), convention de tests §6
(tests d'absence après renommage).

---

## Dépendance avec l'ADR-030

L'ADR-030 (injection de routes par commande explicite) est **indépendant** de
cette migration : il porte sur l'écriture dans `mvc/routes.py` par les
`make:public-*`, pas sur la convention de nommage. Sa révision
(`ADR-030-REVISION-001`, retrait de `starter:build` supprimé par l'ADR-035) est
déjà faite ; sa décision Accepté/Rejeté reste à la main du mainteneur.
