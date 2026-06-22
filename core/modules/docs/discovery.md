# La découverte de modules dans Forge

Ce document décrit la détection des modules Forge dans un dossier.

Le fichier de code correspondant est `core/modules/discovery.py`.

## 1. À quoi sert ce module ?

Avant d'installer ou de lister des modules, il faut les **trouver** : scanner un dossier et y repérer les manifestes valides.

## 2. L'API

| Fonction | Rôle |
|---|---|
| `discover_module_manifests(root_path)` | scanne `root_path` ; retourne (modules valides, modules invalides) |
| `list_module_manifests(root_path)` | retourne la liste des `ModuleManifest` valides trouvés |

## 3. Contextes d'utilisation

- **CLI** : alimenter `module:list` et l'installation déclarative.

## 4. Voir aussi

- [Le manifeste](manifest.md) : ce qui est découvert.
- [Le registre](registry.md) : ce qui est installé.
