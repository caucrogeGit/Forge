# Badge de statut

Objectif : afficher un statut sous forme de **badge HTML** prêt à l'emploi.

**Ce que vous allez apprendre :** `workflow_status_badge(status)` produit un badge
HTML **sûr** (`Markup` : Jinja ne le double-échappe pas), couleur et libellé inclus.

Premier palier du **niveau avancé** de la progression workflow.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-workflow` installé (palier « Installation »).

## Ce que ce starter montre

- `workflow_status_badge(status)` → un `<span>` HTML sûr ;
- l'affichage direct du badge dans la vue ;
- une transformation **pure**.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_workflow.workflow_status_badge` | Produire un badge HTML sûr pour un statut. | [Workflow](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/workflow-badge` : un badge coloré par statut.

## Le contrôleur et la vue

```python
# mvc/controllers/workflow_badge_controller.py
from forge_mvc_workflow import make_status, workflow_status_badge

badges = [(s.name, workflow_status_badge(s)) for s in _STATUSES]
```

```jinja
{# La vue affiche le badge directement : c'est un Markup sûr #}
{% for name, badge in badges %}
<li>{{ name }} : {{ badge }}</li>
{% endfor %}
```

### Comprendre ce code

- Le badge est un `Markup` : Jinja l'affiche **tel quel**, sans rééchapper le HTML —
  pas de `| safe` à risque, pas de HTML codé à la main.
- Couleur et libellé du statut sont déjà intégrés dans le badge.
- Centraliser le rendu d'un statut garantit la cohérence visuelle partout.

## À retenir

- `workflow_status_badge` rend un statut en un badge HTML sûr.
- `Markup` évite le double-échappement et le HTML manuel.
- Un seul endroit pour le rendu = cohérence garantie.

## Après ce starter

La suite : accéder aux **pièces** d'un badge pour un rendu sur mesure.

[Couleur, libellé, classe](workflow-color.md)
