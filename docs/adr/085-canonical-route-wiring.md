# ADR-085 : Câblage de routes canonique, fichier plus affichage

## Statut

Acceptée.
Décision d'architecture ; relève du mainteneur.
Révise l'ADR-030 (injection de routes par commande explicite).

## Date

2026-07-14

## Contexte

Quand un générateur produit un contrôleur, ses routes doivent être branchées dans
l'application. Trois mécanismes coexistaient, hérités de chantiers successifs :

- `make:crud`, `make:auth`, `make:pivot-crud` génèrent un fichier
  `mvc/routes/<contrôleur>_routes.py` (ADR-068) et **affichent** les deux lignes
  de branchement à ajouter dans `mvc/routes/__init__.py`. Ils n'écrivent jamais
  dans un fichier de l'utilisateur.
- `make:public-page/list/show/form/contact` **injectent** directement imports et
  blocs de routes dans `mvc/routes/__init__.py`, par analyse AST (ADR-030).
- `opt-in:enable` **injecte** l'appel `register_optins(router)` par ancrage.

Trois façons de faire un même geste contredisent le principe 11 (une seule façon
officielle de faire chaque chose). Surtout, l'injection réécrit un fichier
possédé par l'utilisateur (`mvc/routes/__init__.py`), ce qui est en tension avec
la charte principe 9 (« pas d'écriture invisible dans le code utilisateur ») et
la règle §7 (Forge génère, affiche, lit ; ne réécrit jamais silencieusement).
L'ADR-030 avait autorisé l'injection sous conditions ; le retour d'expérience
montre qu'elle complique l'audit d'un projet généré (deux vitesses selon la
commande) sans bénéfice décisif : le branchement est deux lignes à copier.

## Décision

Le câblage de routes suit **une seule** convention, celle de l'ADR-068 :
**générer un fichier de routes dédié, puis afficher le branchement**. Aucun
générateur n'écrit dans `mvc/routes/__init__.py`.

- `make:public-*` génèrent leurs routes dans un fichier
  `mvc/routes/<nom>_routes.py` (fonction `register_<nom>_routes(router)`) et
  affichent les deux lignes de branchement, comme `make:crud`.
- `opt-in:enable` cesse d'injecter `register_optins(router)` : il affiche le
  branchement à ajouter (import et appel), l'utilisateur le colle.
- `make:crud`, `make:auth`, `make:pivot-crud` sont déjà conformes.

Le mode **affichage** devient donc l'unique geste de branchement. Forge reste
dans ses trois modes (génère, affiche, lit) sans jamais réécrire un fichier
utilisateur.

## Conséquences

- Révise l'ADR-030 : l'injection de routes par commande explicite n'est plus la
  voie retenue ; l'ADR-030 est conservé comme trace historique, sa décision est
  remplacée par celle-ci.
- Tickets dérivés : bascule de `make:public-*` (5 commandes) et d'`opt-in:enable`
  du mode injection au mode fichier + affichage.
- L'utilisateur a un geste manuel de plus (copier deux lignes) pour les pages
  publiques et l'activation d'opt-ins ; en contrepartie, `mvc/routes/__init__.py`
  n'est jamais modifié par Forge et reste entièrement sous son contrôle.
- L'analyse AST de détection de point d'injection (ADR-030) devient inutile pour
  ces commandes et peut être retirée avec la bascule.

## Limites

- Cet ADR ne change pas le format du fichier de routes par contrôleur (ADR-068)
  ni la convention de nommage des routes (ADR-029).
- Il ne couvre pas un éventuel outil futur d'aide au branchement (par exemple une
  commande qui vérifierait que tous les fichiers de routes sont bien branchés) :
  ce serait un ADR distinct.
