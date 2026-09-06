# Intermédiaire 6 : Les statuts depuis le contrat d'entité

Objectif : ne pas écrire deux fois la liste des statuts.

## Le problème que cela retire

Le contrat d'entité déclare déjà le champ `statut` et ses valeurs permises.
Redéclarer les mêmes statuts pour le workflow crée deux listes, et elles divergent : un statut ajouté au contrat n'existe pas pour le workflow, et le passage vers lui échoue sans que rien ne désigne la cause.

```json
{
  "name": "statut",
  "type": "string",
  "choices": [
    {"value": "brouillon", "label": "Brouillon"},
    {"value": "publie",    "label": "Publié"},
    {"value": "archive",   "label": "Archivé"}
  ]
}
```

```python
from forge_mvc_workflow import statuses_from_entity_field

statuts = statuses_from_entity_field(
    contrat_article, "statut",
    initial="brouillon",
    final=["archive"],
)
```

| Statut | `is_initial` | `is_final` |
|---|---|---|
| `brouillon` | vrai | faux |
| `publie` | faux | faux |
| `archive` | faux | vrai |

Les libellés viennent du contrat : l'écran du workflow et le formulaire de l'entité disent le même mot.

!!! warning "Les choix doivent porter `value` et `label`"
    Une liste de chaînes nues est refusée, en nommant l'indice fautif.

    Sans libellé, le workflow n'aurait rien à afficher, et le déduire de la valeur donnerait « publie » là où le contrat dit « Publié ».

!!! info "`initial` et `final` restent des décisions du workflow"
    Le contrat d'entité ne les connaît pas : il déclare des valeurs permises, pas un cycle de vie.

    C'est le workflow qui dit par où l'on entre et où l'on s'arrête.

!!! danger "Un statut final n'est pas une suppression"
    Rien n'empêche de déclarer une transition sortant d'un statut final.

    `is_final` décrit une intention, que les transitions déclarées font respecter ou non : c'est votre tableau qui ferme la porte, pas ce drapeau.

## À retenir

- Une seule liste de statuts, celle du contrat d'entité.
- Les libellés suivent, donc l'écran et le formulaire s'accordent.
- `initial` et `final` restent déclarés côté workflow.

## Étape suivante

[Bilan du niveau intermédiaire](bilan.md)
