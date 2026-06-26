# Aide-mémoire de la progression Pivot

Récapitulatif des paliers de la progression *Bonjour Forge Pivot* et des API du
module opt-in `forge-mvc-pivot` introduites à chaque étape.

!!! note "Module opt-in : SQL visible"
    `forge-mvc-pivot` est **publié sur PyPI** : `pip install --pre forge-mvc-pivot`. Il
    expose le **SQL réel** (insert, update, select, delete), aucun ORM (charte
    principe 5), et s'appuie sur des **exécuteurs injectables** (`execute`,
    `fetch_all`, `fetch_one`), donc testable sans base réelle.

## Niveau débutant : comprendre le pivot enrichi

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Bonjour Forge Pivot](debutant/pivot-welcome.md) | Pivot ordinaire vs enrichi, construire le service | `PivotAdvancedService` |
| 2 | [Générer le sous-CRUD](debutant/pivot-make.md) | Produire le sous-CRUD pivot | `make:pivot-crud`, `--dry-run` |
| 3 | [Le schéma SQL](debutant/pivot-schema.md) | Clés composites + colonnes d'attributs | `CREATE TABLE article_tag` |

## Niveau intermédiaire : manipuler

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Attacher une association](intermediaire/pivot-attach.md) | Créer une association avec attributs | `attach` |
| 2 | [Modifier et détacher](intermediaire/pivot-update.md) | Mettre à jour / supprimer | `update`, `detach` |
| 3 | [Lister les associations](intermediaire/pivot-list.md) | Lire les `PivotRow` d'une source | `list_for_source`, `PivotRow` |

## Niveau avancé : contraintes et intégrité

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Contraintes de champ](avance/pivot-constraints.md) | Champs requis / non nullables | `PivotFieldConstraint`, `PivotConstraintError` |
| 2 | [Unicité de la paire](avance/pivot-unique.md) | Refuser un doublon avant l'`INSERT` | `unique_pair`, `get` |
| 3 | [Erreurs de formulaire](avance/pivot-form.md) | Erreur pivot → message de formulaire | `pivot_error_to_form_error`, `PivotFormError` |
