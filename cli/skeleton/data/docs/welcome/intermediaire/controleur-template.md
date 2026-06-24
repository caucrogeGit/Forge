# Intermédiaire 2 — Contrôleur et template à la main

Objectif : comprendre la route, le contrôleur et le template, sans générateur.

Une route déclarée dans `mvc/routes.py` associe un chemin à une méthode de
contrôleur ; le contrôleur rend un template via `BaseController.render(...)`.

Inspectez `mvc/controllers/home_controller.py` et `mvc/views/home/index.html` :
c'est le schéma à reproduire pour vos propres pages.

Convention de route : chemin `/<controleur>/<methode>`, nom
`<controleur>-<methode>`.

## Pour approfondir

La convention HTTP inspectable :
https://forgemvc.com/docs/forge/reference/http/

## Étape suivante

[Bilan du niveau intermédiaire](bilan.md)
