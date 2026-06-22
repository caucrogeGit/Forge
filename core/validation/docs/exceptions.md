# L'erreur de validation dans Forge

Ce document décrit l'exception centrale de validation des entités.

Le fichier de code correspondant est `core/validation/exceptions.py`.

## 1. À quoi sert ce module ?

Quand une contrainte de propriété n'est pas respectée, la validation lève une erreur identifiable, portant le nom de la propriété fautive et un message.

## 2. L'objet

```python
class ValidationError(property_name: str, message: str)
```

| Attribut | Contenu |
|---|---|
| `property_name` | la propriété en cause |
| `message` | la raison du refus |

## 3. Contextes d'utilisation

- **Setters d'entité** : levée par les [décorateurs de validation](decorators.md).
- **Formulaires** : attrapée pour afficher l'erreur sur le bon champ.

## 4. Voir aussi

- [Les décorateurs de validation](decorators.md).
