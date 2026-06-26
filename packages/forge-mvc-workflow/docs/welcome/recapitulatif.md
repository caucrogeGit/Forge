# Aide-mémoire de la progression Workflow

Récapitulatif des paliers de la progression *Bonjour Forge Workflow* et des API du
module opt-in `forge-mvc-workflow` introduites à chaque étape.

!!! note "Module opt-in : sans état"
    `forge-mvc-workflow` est **publié sur PyPI** : `pip install --pre forge-mvc-workflow`.
    Il fournit des **fonctions pures** (statuts, transitions, badges) ; l'application
    stocke le statut courant de ses objets. Les helpers Jinja **ne sont pas**
    auto-enregistrés (injection explicite).

## Niveau débutant : statuts

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Bonjour Forge Workflow](debutant/workflow-welcome.md) | Définir/valider un jeu de statuts | `make_status`, `validate_statuses` |
| 2 | [Nom de statut](debutant/workflow-status.md) | Normaliser/valider un nom | `normalize_status_name`, `validate_status_name` |
| 3 | [Retrouver un statut](debutant/workflow-find.md) | Localiser un statut par son nom | `find_status` |

## Niveau intermédiaire : transitions

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Déclarer les transitions](intermediaire/workflow-transition.md) | Définir les passages autorisés | `make_transition`, `validate_transitions` |
| 2 | [Vérifier une transition](intermediaire/workflow-check.md) | Tester un passage | `can_transition` |
| 3 | [Transitions disponibles](intermediaire/workflow-available.md) | Lister les actions d'un statut | `get_available_transitions` |

## Niveau avancé : affichage

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Badge de statut](avance/workflow-badge.md) | Badge HTML sûr | `workflow_status_badge` |
| 2 | [Couleur, libellé, classe](avance/workflow-color.md) | Pièces d'un badge | `workflow_status_label`, `workflow_status_color`, `workflow_status_badge_class` |
| 3 | [Helpers Workflow dans Jinja](avance/workflow-jinja.md) | Injecter les helpers | `make_workflow_jinja_helpers` |
