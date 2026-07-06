# Les paramètres

Ce document décrit l'API de lecture et d'écriture des paramètres applicatifs.

Le fichier de code correspondant est `forge_mvc_settings/store.py`.

## 1. Le modèle

Un paramètre est une paire clé/valeur typée, stockée dans la table `app_settings` (colonnes `setting_key`, `setting_value`, `value_type`, `updated_at`).
La valeur est sérialisée en texte et recoercée à la lecture selon son type.
Les types supportés sont `str`, `int`, `bool` et `float` (constante `SUPPORTED_TYPES`).

La clé commence par une lettre, suivie de lettres, chiffres, `_` ou `.`, sur 191 caractères au plus.
Le point autorise des clés hiérarchiques comme `qcm.session_duration`.

## 2. Écrire (`set_setting`)

```python
def set_setting(key: str, value: str | int | bool | float, *, db=None) -> None
```

`set_setting` crée ou met à jour le paramètre `key` (upsert `ON DUPLICATE KEY UPDATE`).
Le type est déduit de `value`.
Lève `SettingsError` si la clé est invalide ou si le type n'est pas supporté.

```python
from forge_mvc_settings import set_setting

set_setting("etablissement.nom", "Collège Victor Hugo")
set_setting("qcm.session_duration", 30)   # int
set_setting("maintenance", False)         # bool
```

## 3. Lire (`get_setting`)

```python
def get_setting(key: str, default=None, *, db=None) -> str | int | bool | float | None
```

`get_setting` renvoie la valeur recoercée selon le type stocké, ou `default` si le paramètre n'existe pas.

```python
from forge_mvc_settings import get_setting

nom = get_setting("etablissement.nom")          # "Collège Victor Hugo"
duree = get_setting("qcm.session_duration", 20) # 30 (int)
en_maintenance = get_setting("maintenance")     # False (bool)
```

## 4. Tout lire (`get_all_settings`)

```python
def get_all_settings(*, db=None) -> dict[str, str | int | bool | float]
```

Renvoie tous les paramètres, recoercés, triés par clé.

## 5. Supprimer (`delete_setting`)

```python
def delete_setting(key: str, *, db=None) -> bool
```

Supprime le paramètre `key`.
Renvoie `True` s'il existait, `False` sinon.

## 6. Le paramètre `db`

Toutes les fonctions acceptent un paramètre `db` injectable.
Par défaut, l'accès passe par `core.database.db` (le pool configuré par l'application).
En test, on peut injecter un adapter qui expose `fetch_one`, `fetch_all` et `execute`, ce qui rend le store vérifiable sans base réelle.

## 7. Voir aussi

- [L'initialisation](cli.md) : créer la table via `forge settings:init`.
- [Les erreurs](errors.md) : `SettingsError`.
