# L'installation des fichiers de module dans Forge

Ce document décrit la copie contrôlée des fichiers déclarés par un module.

Le fichier de code correspondant est `core/modules/files.py`.

## 1. À quoi sert ce module ?

Installer un module copie ses fichiers dans le projet.
Cette copie est **contrôlée** : elle refuse d'écraser un fichier existant (conflit) et peut s'exécuter en *dry-run*.

## 2. L'API

| Élément | Rôle |
|---|---|
| `prepare_module_file_installation(...)` | calcule ce qui serait copié (dry-run) et détecte les conflits |
| `install_module_files(...)` | copie réellement les fichiers du module |
| `ModuleFileInstallResult` | résultat (fichiers copiés, dry-run) |
| `ModuleFileConflictError` | au moins une cible existe déjà |
| `ModuleFileInstallError` | erreur de préparation ou de copie |

## 3. Le contrat

Préservation du code utilisateur : un fichier existant n'est **jamais écrasé** silencieusement ; le conflit est signalé.

## 4. Contextes d'utilisation

- **`module:install`** : copier les fichiers après enregistrement au registre.

## 5. Voir aussi

- [Le registre](registry.md) et [la suppression](remove.md).
