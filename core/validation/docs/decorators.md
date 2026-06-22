# Les décorateurs de validation dans Forge

Ce document décrit les décorateurs de validation des propriétés d'entité.

Le fichier de code correspondant est `core/validation/decorators.py`.

## 1. À quoi sert ce module ?

Les propriétés d'une entité doivent souvent respecter des contraintes (type, longueur, plage, format).
Ces décorateurs posent ces contraintes sur les *setters* de propriété, **sans transformation implicite** : la valeur est validée, jamais convertie en douce.

## 2. L'API

| Décorateur | Contrainte |
|---|---|
| `typed(expected_type)` | valide le type Python attendu |
| `nullable` | marque explicitement la propriété comme acceptant `None` |
| `not_empty` | refuse les chaînes vides ou blanches |
| `min_length(size)` / `max_length(size)` | longueur minimale / maximale d'une chaîne |
| `min_value(limit)` / `max_value(limit)` | valeur numérique minimale / maximale |
| `pattern(regex)` | impose une expression régulière |

```python
from core.validation.decorators import typed, not_empty, max_length

@property
def title(self): ...

@title.setter
@typed(str)
@not_empty
@max_length(120)
def title(self, value): ...
```

## 3. Le principe

La validation **lève** `ValidationError` plutôt que de corriger silencieusement : le comportement reste explicite (refuser la magie cachée).

## 4. Contextes d'utilisation

- **Modèles d'entité** : poser les contraintes sur les setters générés.

## 5. Voir aussi

- [L'erreur de validation](exceptions.md) : `ValidationError`.
