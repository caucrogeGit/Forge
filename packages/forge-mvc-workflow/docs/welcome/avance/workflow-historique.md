# Avancé 4 : L'historique des transitions

Objectif : répondre à « qui a publié cet article, et quand ».

## Ce que le statut courant ne dit pas

Une colonne `statut` porte l'état, jamais le chemin.
Un article passé de brouillon à publié puis archivé ressemble, dans la table, à un article créé archivé.

L'historique est une **table** : il lui faut donc une base, et de quoi la faire évoluer.

```bash
pip install forge-mvc-sqlite forge-mvc-entities
forge db:config
forge db:init
forge workflow:init
forge migration:apply
```

Un projet qui a déjà une base saute les trois premières commandes.
La table `workflow_history` garde ensuite une ligne par passage.

```python
from forge_mvc_workflow import record_transition

record_transition(
    "Article", article_id, "publie",
    from_status="brouillon",
    actor_kind="user", actor_id=utilisateur.id,
    comment="Relu par la rédaction",
)
```

## Le relire

```python
from forge_mvc_workflow import history_for, last_transition

for passage in history_for("Article", article_id):
    print(passage.from_status, "vers", passage.to_status, passage.created_at)

dernier = last_transition("Article", article_id)
```

`history_for` rend la suite complète, du plus ancien au plus récent.
`last_transition` rend le dernier passage, ou `None` si l'entité n'en a aucun.

!!! warning "Forge n'enregistre pas à votre place"
    `apply_transition` ne consulte pas l'historique et n'y écrit pas.

    C'est délibéré : Forge n'écrit jamais dans votre code, et toutes les applications ne veulent pas d'une trace. Appelez `record_transition` dans votre `commit`, là où l'écriture a lieu.

!!! danger "Écrivez la trace dans la même transaction que le statut"
    Sinon la trace ment : le statut change et l'historique reste en arrière, ou l'inverse.

    Le `commit` d'`apply_transition` est l'endroit prévu pour que les deux écritures aillent ensemble.

!!! info "L'acteur est en deux parties, et peut manquer"
    `actor_kind` et `actor_id` disent qui a agi, un utilisateur, une tâche de fond, un import.

    Les laisser vides est licite : un passage automatique n'a pas d'auteur, et inventer « system » masquerait la différence.

## À retenir

- L'historique est une table à part, provisionnée par `workflow:init`.
- L'écriture est explicite, et doit accompagner celle du statut.
- L'acteur peut légitimement manquer.

## Étape suivante

[Bilan du niveau avancé](bilan.md)
