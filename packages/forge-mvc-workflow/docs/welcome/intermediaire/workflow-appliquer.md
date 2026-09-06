# Intermédiaire 4 : Appliquer une transition

Objectif : passer un article de brouillon à publié, avec ce qui va avec.

## Vérifier ne suffit pas

`can_transition` répond « ce passage est-il déclaré ».
Il ne change rien, n'écrit rien, et ne prévient personne.

`apply_transition` mène la transition entière, dans un ordre où chaque étape conditionne la suivante.

```python
from forge_mvc_workflow import apply_transition

nouveau = apply_transition(
    transitions, "brouillon", "publie",
    before=lambda e: verifier_le_quota(e),
    commit=lambda e: db.execute(
        "UPDATE article SET statut = ? WHERE id = ?", (e.to_status, article_id)),
    after=lambda e: envoyer_la_notification(e),
    context={"article_id": article_id},
)
```

| Étape | Ce qui se passe |
|---|---|
| 1 | la transition est vérifiée contre celles déclarées |
| 2 | les **conditions enregistrées** applicables sont consultées |
| 3 | `before` est appelé ; s'il lève, tout s'arrête |
| 4 | `commit` écrit, c'est l'écriture de l'application |
| 5 | `after` est appelé |

Les trois crochets reçoivent le même `TransitionEvent`, qui porte le départ, l'arrivée et le contexte.

!!! danger "Sans `commit`, il n'y a aucune garantie d'écriture"
    `after` suit alors immédiatement `before`, et le paquet n'a aucun moyen de savoir si quelque chose a été écrit.

    Le dire vaut mieux que de laisser croire à une garantie qui n'existe pas : passez votre écriture en `commit`, pas en `after`.

!!! warning "Rien n'est appelé si la transition est refusée"
    Ni `before`, ni `commit`, ni `after`.

    Une notification envoyée pour un passage refusé serait pire qu'aucune notification.

!!! info "L'ordre protège de la double écriture"
    `before` sert aux contrôles qui peuvent encore tout annuler, `after` aux effets qui supposent l'écriture faite.

    Envoyer un courriel dans `before` l'enverrait même si `commit` échoue.

## À retenir

- `apply_transition` mène l'enchaînement complet et rend le statut atteint.
- L'écriture va dans `commit` ; sans lui, aucune garantie n'est donnée.
- Un refus n'appelle aucun crochet.

## Étape suivante

[Suivant : les conditions de transition](workflow-conditions.md)
