# La génération des routes de module dans Forge

Ce document décrit la génération explicite du fichier de routes d'un module.

Le fichier de code correspondant est `core/modules/routes.py`.

## 1. À quoi sert ce module ?

Brancher les routes d'un module se fait par génération d'un fichier dédié `mvc/routes_<module>.py`, **explicitement** (jamais d'injection silencieuse dans `mvc/routes.py`).

## 2. L'API

| Élément | Rôle |
|---|---|
| `generate_module_routes(...)` | génère `mvc/routes_<module>.py` |
| `ModuleRouteGenerationResult` | résultat de la génération |
| `ModuleRoutesAlreadyGeneratedError` | un fichier de routes existe déjà pour ce module |
| `ModuleRouteInjectionError` | erreur lors de la génération |

## 3. Le contrat

Conforme au principe « pas d'écriture invisible » : les routes sont générées dans un fichier dédié, que le développeur branche, jamais injectées en douce.

## 4. Contextes d'utilisation

- **Activation d'un module** : générer puis brancher ses routes.

## 5. Voir aussi

- [Le registre](registry.md) et [l'installation des fichiers](files.md).
- [Le routeur (core/http)](../core-http/router.md).
