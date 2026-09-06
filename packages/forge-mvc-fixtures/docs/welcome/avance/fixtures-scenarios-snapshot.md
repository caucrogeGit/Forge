# Avancé 4 : Scénarios et instantanés

Objectif : plusieurs jeux de données, et un jeu tiré de la base plutôt qu'écrit à la main.

## Les scénarios

Un sous-dossier de `mvc/fixtures/` est un scénario.

```bash
forge fixtures:load --scenario demo
```

Le jeu **commun**, à la racine, est chargé d'abord ; le scénario vient ensuite.
Un scénario ne remplace donc pas les fixtures communes, il s'y ajoute.

!!! danger "Un scénario inconnu est refusé, et nomme ceux qui existent"
    Charger zéro fichier en annonçant un succès ferait croire les données en place.

    Le message dit « Scénarios présents : demo », ce qui suffit à corriger une faute de frappe.

## Les instantanés

Écrire des fixtures à la main coûte cher et vieillit mal, alors que la base contient déjà un jeu cohérent.

```bash
forge fixtures:snapshot eleves
forge fixtures:snapshot eleves --limit 50 --out mvc/fixtures/eleves.sql
```

Sans `--out`, la commande **affiche** seulement.

!!! danger "Relisez avant de versionner"
    L'instantané vient d'une base réelle et peut contenir des données personnelles.

    La commande le dit à chaque exécution, et refuse en environnement de production sans `--force`.

!!! info "L'aller-retour est fidèle"
    Apostrophes, valeurs nulles, décimales et sauts de ligne à l'intérieur d'un texte repassent identiques.

    Un instantané se recharge donc par `fixtures:load`, sans retouche.

!!! warning "Un fichier existant n'est jamais écrasé"
    `--out` refuse si le fichier est là.

    Deux instantanés de la même table se ressemblent assez pour qu'on ne voie pas lequel a remplacé l'autre.

## À retenir

- Un scénario s'ajoute au jeu commun, il ne le remplace pas.
- L'instantané affiche par défaut, écrit avec `--out`, et n'écrase rien.
- Ce qu'il produit vient de vraies données : relisez-le.

## Étape suivante

[Bilan du niveau avancé](bilan.md)
