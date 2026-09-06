# Avancé 4 : Agir sur *cet* objet

Objectif : laisser un auteur modifier son article, et un modérateur modifier tous les articles.

## Ce qu'une permission globale ne dit pas

`article.editer` répond « cette personne peut modifier des articles ».
Elle ne répond pas « celui-ci ».

La règle réelle tient en deux permissions et une question de propriété.

```python
from forge_mvc_rbac import has_contract_permission, require_instance_permission

def edit(request, article):
    require_instance_permission(
        request, article,
        can=lambda code: has_contract_permission(contrat, roles, code),
        any_permission="article.editer_tout",
        own_permission="article.editer_le_sien",
        is_owner=lambda a: a["auteur_id"] == utilisateur_courant(request),
    )
```

## L'ordre des contrôles, et pourquoi il est ainsi

1. `any_permission` accordée rend vrai **sans regarder la propriété**.
2. Sinon, `own_permission` accordée **et** `is_owner` vrai rend vrai.
3. Sinon, refus.

!!! info "Un modérateur n'a pas à être l'auteur"
    Vérifier la propriété avant la permission refuserait à un modérateur ce que « n'importe lequel » lui accorde, ce qui est un contresens.

    C'est aussi ce qui évite d'appeler `is_owner`, donc souvent la base, pour quelqu'un qui n'a de toute façon aucun droit.

!!! danger "Déclarer une propriété sans moyen de l'établir est refusé"
    `own_permission` sans `is_owner` rendrait toujours faux, et une faute de frappe se lirait comme un refus légitime.

    De même, n'en déclarer aucune des deux lève `ValueError` plutôt que de refuser tout le monde en silence.

!!! warning "La forme du refus vous appartient"
    `require_instance_permission` lève `InstancePermissionDenied` et ne rend aucune réponse HTTP.

    Une page d'erreur pour un écran, un JSON pour une API : c'est l'application qui sait, et Forge ne choisit pas à sa place.

## La variante qui ne lève pas

`has_instance_permission` prend les mêmes arguments et rend un booléen, pour un gabarit qui veut masquer un bouton plutôt que refuser une action.

## À retenir

- Deux permissions, « tout » et « le sien », et une fonction de propriété.
- La permission est examinée avant la propriété, et c'est délibéré.
- Une déclaration incomplète lève, plutôt que de refuser tout le monde sans dire pourquoi.

## Étape suivante

[Suivant : journaliser les refus](rbac-refus.md)
