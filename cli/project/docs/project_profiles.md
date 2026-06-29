# Les profils de projet dans Forge

Ce module définit le contrat des profils de projet officiels et leur description.

L'option `--profile` de `forge new` s'appuie sur ce contrat.
Le profil choisi est enregistré dans `forge_profile.txt` à la racine du projet.

## 1. Rôle

Le module est la source de vérité des profils de projet disponibles.

Il déclare le tuple des profils officiels, le profil par défaut, et une description par profil.
Aucun profil n'existe en dehors de ce contrat : `forge new` valide la valeur de `--profile` contre ce tuple.

## 2. Vue d'ensemble rapide

| Élément | Valeur |
|---|---|
| Commande forge | consommé par `forge new <Nom> [--profile <profil>]` |
| Module Python | `cli.project.project_profiles` |
| Catégorie | contrat CLI (profils de création de projet) |
| Rôle | définir les profils officiels et leurs descriptions |
| Entrées | aucune (constantes statiques) |
| Sorties | tuple de profils, profil par défaut, descriptions |
| Fichiers touchés | aucun ; `forge new` écrit `forge_profile.txt` (write-if-new) |
| Mode Forge | lit |

Le module ne réalise aucune action : il fournit des constantes lues par le dispatcher CLI et par `forge new`.

## 3. Profils officiels

| Profil | Description résumée |
|---|---|
| `minimal` | projet le plus simple, structure MVC de base, sans composants avancés ni exemple métier |
| `standard` | profil recommandé, layout public et admin, formulaires, flash, pagination (défaut) |
| `dynamic` | base standard enrichie d'interactions front légères (HTMX, Alpine.js optionnel) |
| `multilingual` | base standard avec i18n initialisée et `translations/fr.json` |
| `auth-mfa` | base standard avec authentification MFA (TOTP) ; voir la progression welcome-mfa |

Le profil par défaut est `standard`.

## 4. API publique

| Symbole | Type | Rôle |
|---|---|---|
| `SUPPORTED_PROJECT_PROFILES` | `tuple[str, ...]` | profils officiels reconnus |
| `DEFAULT_PROJECT_PROFILE` | `str` | profil appliqué sans `--profile` (`standard`) |
| `PROJECT_PROFILE_DESCRIPTIONS` | `dict[str, str]` | description de chaque profil |

## 5. Contextes d'utilisation

| Besoin | Élément |
|---|---|
| Valider la valeur de `--profile` à `forge new` | `SUPPORTED_PROJECT_PROFILES` |
| Connaître le profil par défaut | `DEFAULT_PROJECT_PROFILE` |
| Afficher la description d'un profil | `PROJECT_PROFILE_DESCRIPTIONS` |

## 6. Exemples d'utilisation

Créer un projet avec un profil explicite :

```bash
forge new MonProjet --profile minimal
```

Lire le contrat depuis du code Python :

```python
from cli.project.project_profiles import (
    SUPPORTED_PROJECT_PROFILES,
    DEFAULT_PROJECT_PROFILE,
    PROJECT_PROFILE_DESCRIPTIONS,
)

print(DEFAULT_PROJECT_PROFILE)            # standard
print("auth-mfa" in SUPPORTED_PROJECT_PROFILES)  # True
print(PROJECT_PROFILE_DESCRIPTIONS["minimal"])
```

## 7. Détails et limites

!!! note "Source de vérité unique"
    Tout ajout ou retrait de profil passe par ce module.
    `forge new` ne reconnaît aucune valeur de `--profile` absente de `SUPPORTED_PROJECT_PROFILES`.

## Voir aussi

- [Le chargement de configuration projet](project_config.md) : lecture de la configuration applicative.
- [La commande doctor](doctor.md) : diagnostic du projet créé.
