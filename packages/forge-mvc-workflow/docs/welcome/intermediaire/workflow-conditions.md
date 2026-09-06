# Intermédiaire 5 : Les conditions de transition

Objectif : « rien ne sort de brouillon sans relecture », écrit une fois.

## Ce que la déclaration des transitions ne dit pas

Le tableau des transitions dit quels passages **existent**.
Il ne dit pas à quelles conditions ils sont permis : une pièce jointe présente, un quota non dépassé, une relecture faite.

Sans registre, chaque contrôleur redit la règle, et deux chemins menant au même état s'oublient l'un l'autre.

```python
from forge_mvc_workflow import register_condition


def relecture_faite(depart, arrivee, contexte):
    if not contexte.get("relu_par"):
        return "L'article n'a pas été relu."
    return None


register_condition(relecture_faite, from_status="brouillon")
```

## Ce qu'une condition rend

| Retour | Sens |
|---|---|
| `None` | rien à signaler, ce passage est permis |
| une chaîne | le motif du refus, montré à l'utilisateur |

!!! danger "Ne rendez pas un `ConditionResult`"
    Ce type est ce que `check_conditions` vous **rend**, pas ce qu'une condition doit produire.

    Le rendre depuis une condition fait refuser la transition avec « une condition a rendu un verdict illisible » : la valeur n'est pas lisible comme un motif.

!!! warning "Une condition qui lève refuse la transition"
    Le jour où le service qu'elle interroge tombe, tout passerait sinon.

    Le motif dit alors « une condition n'a pas pu être évaluée », et la panne se voit au lieu de s'ouvrir.

!!! info "La portée se choisit à l'enregistrement"
    Sans `from_status` ni `to_status`, la condition s'applique à **toutes** les transitions.

    Avec l'un des deux, elle s'applique à celles qui le portent : « rien ne sort de brouillon » se déclare une fois, plutôt qu'une fois par transition sortante.

## Les consulter

```python
from forge_mvc_workflow import check_conditions, ensure_conditions

verdict = check_conditions("brouillon", "publie", contexte)
if not verdict.allowed:
    return render("article/form.html", erreurs=verdict.reasons)
```

`ensure_conditions` fait le même contrôle et **lève** au lieu de rendre un verdict, quand l'appelant préfère une exception.

`apply_transition` les consulte de lui même : vous n'avez pas à les appeler avant lui.

## À retenir

- Une condition rend `None` ou un motif ; jamais autre chose.
- Elle est enregistrée avec sa portée, et toutes les applicables doivent accepter.
- `apply_transition` les consulte, et un échec de condition refuse.

## Étape suivante

[Suivant : les statuts depuis le contrat d'entité](workflow-statuts-entite.md)
