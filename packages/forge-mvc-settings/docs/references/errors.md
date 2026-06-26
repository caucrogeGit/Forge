# Les erreurs

Ce document décrit l'erreur levée par `forge_mvc_settings` en cas d'entrée
invalide.

Le fichier de code correspondant est `forge_mvc_settings/errors.py`.

## 1. `SettingsError`

```python
class SettingsError(ValueError):
    ...
```

`SettingsError` signale une entrée invalide pour un paramètre applicatif.
Elle hérite de `ValueError` : un appelant peut la rattraper comme une erreur
d'entrée ordinaire.

## 2. Quand est-elle levée ?

| Cause | Origine |
|---|---|
| Clé invalide (format ou longueur) | `set_setting`, `get_setting`, `delete_setting` |
| Type de valeur non supporté (hors `str`, `int`, `bool`, `float`) | `set_setting` |

Le message indique la cause de façon explicite.

## 3. Rattraper l'erreur

```python
from forge_mvc_settings import set_setting, SettingsError

try:
    set_setting(cle_utilisateur, valeur)
except SettingsError as exc:
    print(f"Paramètre refusé : {exc}")
```

## 4. Voir aussi

- [Les paramètres](store.md) : `set_setting`, `get_setting`.
