# Les profils de projet dans Forge

Ce document décrit le contrat des profils de projet officiels.

Le fichier de code correspondant est `cli/project/project_profiles.py`.

## 1. À quoi sert ce module ?

Il définit les profils de projet officiels et leur description.
L'option `--profile` de `forge new` s'appuie sur ce contrat.

Le profil choisi est enregistré dans `forge_profile.txt` à la racine du projet.
Ce module est la source de vérité des profils disponibles.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `SUPPORTED_PROJECT_PROFILES` | tuple des profils officiels reconnus |

## 3. Contextes d'utilisation

- **Création de projet** : valider la valeur de `--profile` à `forge new`.
- **Cohérence** : aucun profil n'existe en dehors de ce contrat.

## 4. Voir aussi

- [Le chargement de configuration projet](project_config.md) : configuration applicative.
