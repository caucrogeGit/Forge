# Le manifeste de module dans Forge

Ce document décrit le contrat et la validation du fichier `module.json`.

Le fichier de code correspondant est `core/modules/manifest.py`.

## 1. À quoi sert ce module ?

Un module Forge se décrit par un manifeste `module.json` (nom, version, fichiers, routes).
Ce module valide ce manifeste et le charge en un objet `ModuleManifest`.

## 2. L'API

| Élément | Rôle |
|---|---|
| `ModuleManifest` | manifeste validé d'un module |
| `load_module_manifest(path)` | lit un `module.json` et retourne un `ModuleManifest` validé |
| `validate_module_manifest(data)` | valide un dictionnaire en `ModuleManifest` |
| `validate_module_name(name)` | valide et retourne le nom d'un module |
| `validate_module_version(version)` | valide la version (`MAJOR.MINOR.PATCH`) |
| `ModuleManifestError` | erreur de validation du manifeste |

## 3. Contextes d'utilisation

- **Découverte / installation** : valider un manifeste avant de l'installer.

## 4. Voir aussi

- [La découverte de modules](discovery.md) et [le registre](registry.md).
