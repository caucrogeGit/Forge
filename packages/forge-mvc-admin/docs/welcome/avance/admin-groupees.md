# Avancé 2 : Agir sur plusieurs lignes

Objectif : nettoyer deux cents inscriptions de test sans deux cents confirmations.

## Ce que la ressource doit déclarer

Rien n'est groupé par défaut : une suppression de masse ne s'ouvre pas toute seule.

```python
registry.register(AdminResource(
    entity="Article",
    slug="articles",
    label="Article",
    plural_label="Articles",
    list_fields=("title", "status"),
    form_fields=("title", "body"),
    table="articles",
    bulk_delete=True,
    status_field="status",
    bulk_transitions=(("draft", "published"), ("published", "archived")),
))
```

| Attribut | Ce qu'il ouvre |
|---|---|
| `bulk_delete` | la suppression groupée des lignes cochées |
| `status_field` | la colonne que les transitions font changer |
| `bulk_transitions` | les couples **départ vers arrivée** autorisés, et eux seuls |

## Le parcours d'une action groupée

Cocher des lignes, choisir l'action, valider : une **page de confirmation** affiche les lignes visées avant tout effet.
L'action ne s'exécute qu'à la soumission du formulaire, en POST, protégée par CSRF.

Une transition absente de `bulk_transitions` répond 400, et une ressource sans `bulk_delete` répond 403 même si la requête est forgée à la main.
Le contrôle est refait à l'exécution : passer par la page de confirmation ne dispense de rien.

!!! danger "Une sélection vide est refusée"
    `DELETE FROM articles` sans clause `WHERE` viderait la table entière.

    La suppression groupée refuse donc une sélection vide plutôt que de construire une requête sans borne, et le message le dit.

!!! warning "Deux cents lignes au plus, par fournée"
    Au delà, l'action est refusée.

    Une sélection de cette taille vient rarement d'un clic : le plafond transforme une manœuvre en refus plutôt qu'en dégât.

!!! info "Une ligne disparue entre l'affichage et la validation n'est pas une erreur"
    Le compte rendu dit combien de lignes ont réellement été supprimées, qui peut être inférieur à la sélection.

    Refuser toute la fournée pour cela ferait échouer une action correcte.

## À retenir

- Rien n'est groupé sans déclaration explicite sur la ressource.
- Confirmation d'abord, effet en POST ensuite, et les contrôles sont refaits.
- Sélection vide refusée, plafond à deux cents.

## Étape suivante

[Suivant : surcharger un template](admin-override.md)
