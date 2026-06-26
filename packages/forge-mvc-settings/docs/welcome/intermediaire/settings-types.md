# Valeurs typées

Objectif : enregistrer et relire des valeurs entières, booléennes et décimales.

**Ce que vous allez apprendre :** `set_setting` déduit le type de la valeur
fournie (`str`, `int`, `bool` ou `float`).
À la lecture, `get_setting` recoerce la valeur dans ce même type.
Un entier ressort entier, un booléen ressort booléen.

Premier palier du **niveau intermédiaire** de la progression Settings.

!!! note "Module opt-in"
    Si `forge-mvc-settings` n'est pas installé, l'import échoue.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet.

## Ce que ce starter montre

- enregistrer un entier, un booléen et un décimal ;
- relire chaque valeur dans son type d'origine.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `set_setting(key, value)` | Déduit le type de `value` et l'enregistre. | Opt-ins |
| `get_setting(key, default)` | Recoerce la valeur selon le type stocké. | Opt-ins |

## 1. Enregistrer des valeurs typées

```python
from forge_mvc_settings import set_setting

set_setting("qcm.session_duration", 30)     # int
set_setting("maintenance", False)           # bool
set_setting("note.coefficient", 1.5)        # float
```

### Comprendre ce code

- Le type est déduit de la valeur : `30` est un `int`, `False` un `bool`, `1.5` un `float`.
- Les types supportés sont `str`, `int`, `bool` et `float` (constante `SUPPORTED_TYPES`).
- La valeur est sérialisée en texte, mais son type est mémorisé à part.

## 2. Relire chaque valeur dans son type

```python
from forge_mvc_settings import get_setting

duree = get_setting("qcm.session_duration")   # 30 (int)
en_maintenance = get_setting("maintenance")   # False (bool)
coefficient = get_setting("note.coefficient") # 1.5 (float)

print(duree + 5)                # 35, addition d'entiers
print(not en_maintenance)       # True, opération booléenne
```

### Comprendre ce code

- `get_setting` recoerce la valeur dans le type enregistré.
- `duree` est un vrai entier : on peut l'additionner sans conversion.
- `en_maintenance` est un vrai booléen : il s'utilise directement dans un test.

## À retenir

- `set_setting` déduit le type à partir de la valeur fournie.
- Les types supportés sont `str`, `int`, `bool` et `float`.
- `get_setting` rend la valeur dans son type d'origine, prête à l'emploi.

## Après ce starter

Vous savez stocker des valeurs typées.
Voyons comment lister tous les paramètres et en supprimer un.

[Lister et supprimer](settings-all.md)
