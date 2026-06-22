# Le registre des modules dans Forge

Ce document décrit le registre des modules installés.

Le fichier de code correspondant est `core/modules/registry.py`.

## 1. À quoi sert ce module ?

Forge garde la trace des modules **installés** dans un registre JSON.
Ce module lit, écrit et met à jour ce registre, et installe déclarativement un manifeste.

## 2. L'API

| Élément | Rôle |
|---|---|
| `load_installed_modules_registry(path)` | charge le registre (`{"installed": {}}` si absent) |
| `save_installed_modules_registry(...)` | écrit le registre en JSON lisible |
| `is_module_installed(registry, name)` | `True` si le module est déjà présent |
| `prepare_module_installation(...)` | prépare l'entrée de registre d'un module |
| `install_module_manifest(...)` | installe déclarativement un module dans le registre |
| `ModuleInstallResult` | résultat d'une installation |
| `ModuleRegistryError`, `ModuleAlreadyInstalledError` | erreurs du registre |

## 3. Contextes d'utilisation

- **`module:install`** : enregistrer un module découvert.

## 4. Voir aussi

- [L'installation des fichiers](files.md) : la copie associée.
- [La génération des routes](routes.md) et [la suppression](remove.md).
