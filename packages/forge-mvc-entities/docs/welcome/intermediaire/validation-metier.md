# Intermédiaire 5 : La validation métier

Objectif : refuser une séance qui finit avant de commencer.

## Ce que le contrat ne sait pas dire

Le contrat d'entité décrit des **types** : une chaîne de 120 caractères, un entier, une date obligatoire.
Il ne sait pas dire qu'une fin doit suivre un début, qu'un total doit rester sous un plafond, ou qu'un statut ne se change que dans un sens.

Ces règles se déclarent en Python, et Forge les tient dans un registre par entité.

```python
from forge_mvc_entities import register_entity_validator
from forge_mvc_entities.validators import ValidationIssue


def dates_coherentes(donnees, contexte=None):
    debut, fin = donnees.get("debut"), donnees.get("fin")
    if debut and fin and fin < debut:
        return [ValidationIssue(field="fin", message="La fin précède le début.")]
    return []


register_entity_validator("Seance", dates_coherentes)
```

Un validateur reçoit les données et rend la liste de ce qui ne va pas.
Une liste vide vaut « rien à signaler ».

## Les employer

```python
from forge_mvc_entities import validate_entity_data

rapport = validate_entity_data("Seance", donnees)
if not rapport.ok:
    return render("seance/form.html", erreurs=rapport.by_field())
```

| Ce que le rapport porte | Usage |
|---|---|
| `ok` | vrai quand rien n'a été signalé |
| `by_field()` | les messages groupés par champ, pour un formulaire |
| `summary` | une ligne, pour un journal |

`ensure_entity_data` fait la même chose et **lève** `EntityValidationError` au lieu de rendre un rapport, quand l'appelant préfère une exception.

!!! warning "Forge n'appelle pas vos validateurs à votre place"
    Le contrôleur engendré par `make:crud` ne les consulte pas : Forge n'écrit jamais dans votre code (principe 9).

    C'est à vous d'appeler `validate_entity_data` là où vous validez déjà le formulaire, juste avant l'écriture.

!!! danger "Un validateur qui lève refuse l'écriture"
    Si votre règle plante, le rapport n'est pas vide : il porte « une règle n'a pas pu être évaluée ».

    L'inverse laisserait passer une écriture parce qu'une garde est cassée, ce qui est exactement le moment où il faut refuser.

!!! info "Enregistrez au câblage, pas à l'import d'un contrôleur"
    Le registre vit dans le processus. `bootstrap.py` est l'endroit prévu, lu par les deux points d'entrée.

    Enregistrer depuis un module importé au hasard rendrait la règle active ou non selon l'ordre des imports.

## À retenir

- Le contrat décrit des types ; les règles métier vivent dans un registre Python.
- Le rapport se rend par champ, prêt pour un formulaire.
- Forge ne les appelle pas seul : appelez-les avant l'écriture, depuis votre contrôleur.

## Étape suivante

[Continuer : bilan du niveau intermédiaire](bilan.md)
