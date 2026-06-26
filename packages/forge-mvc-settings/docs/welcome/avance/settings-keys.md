# Les règles de clé

Objectif : connaître le format des clés et gérer les erreurs de validation.

**Ce que vous allez apprendre :** une clé commence par une lettre, suivie de
lettres, chiffres, `_` ou `.`, sur 191 caractères au plus.
Le point autorise des clés hiérarchiques comme `qcm.session_duration`.
Une clé invalide ou un type non supporté lève `SettingsError`.

Premier palier du **niveau avancé** de la progression Settings.

!!! note "Module opt-in"
    Si `forge-mvc-settings` n'est pas installé, l'import échoue.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet.

## Ce que ce starter montre

- former une clé hiérarchique valide ;
- rattraper `SettingsError` sur une clé ou un type invalide.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `set_setting(key, value)` | Valide la clé et le type avant d'écrire. | Opt-ins |
| `SettingsError` | Levée si la clé ou le type est invalide. | Opt-ins |

## 1. Des clés hiérarchiques

```python
from forge_mvc_settings import set_setting

set_setting("qcm.session_duration", 30)
set_setting("etablissement.nom", "Collège Victor Hugo")
set_setting("affichage.theme", "clair")
```

### Comprendre ce code

- Une clé commence par une lettre, puis des lettres, chiffres, `_` ou `.`.
- Le point n'a pas de magie cachée : il sert seulement à organiser les noms.
- La longueur d'une clé ne dépasse pas 191 caractères.

## 2. Rattraper SettingsError

```python
from forge_mvc_settings import set_setting, SettingsError

try:
    set_setting("2cles", "valeur")      # commence par un chiffre : invalide
except SettingsError as erreur:
    print("Clé refusée :", erreur)

try:
    set_setting("export.format", ["csv"])   # type non supporté
except SettingsError as erreur:
    print("Type refusé :", erreur)
```

### Comprendre ce code

- Une clé qui ne commence pas par une lettre est refusée par `SettingsError`.
- Une valeur dont le type n'est pas `str`, `int`, `bool` ou `float` est refusée.
- Le message d'erreur indique la cause, ce qui facilite la correction.

## À retenir

- Une clé commence par une lettre ; ensuite lettres, chiffres, `_` ou `.`, sur 191 caractères au plus.
- Le point permet des clés hiérarchiques, sans comportement caché.
- `SettingsError` couvre la clé invalide et le type non supporté.

## Après ce starter

Les clés et les erreurs sont sous contrôle.
Voyons l'indépendance du cœur et le paramètre `db` injectable.

[Indépendance du cœur](settings-independance.md)
