# Bilan : niveau avancé (Workflow)

Récapitulatif du **niveau avancé** de la progression *Welcome Workflow*. Ce
niveau couvre l'**affichage** des statuts.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1 : [Badge de statut](workflow-badge.md) | Rendre un statut en badge HTML sûr (`workflow_status_badge`). |
| 2 : [Couleur, libellé, classe](workflow-color.md) | Accéder aux pièces d'un badge (`_label`, `_color`, `_badge_class`). |
| 3 : [Helpers Workflow dans Jinja](workflow-jinja.md) | Injecter les helpers dans un template (`make_workflow_jinja_helpers`). |

Vous maîtrisez le workflow de bout en bout : statuts, transitions, affichage.

## Et ensuite

La progression *Welcome Workflow* est terminée. `forge-mvc-workflow` décrit la
machine à états ; l'application **stocke** le statut courant de ses objets (une colonne
suffit) et applique les transitions validées.

[Aide-mémoire de la progression Workflow](../recapitulatif.md)
