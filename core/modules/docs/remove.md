# La suppression de module dans Forge

Ce document décrit la désinstallation contrôlée d'un module.

Le fichier de code correspondant est `core/modules/remove.py`.

## 1. À quoi sert ce module ?

Désinstaller un module le retire du registre et supprime ses fichiers de façon **contrôlée** (décision par fichier, *dry-run* possible).

## 2. L'API

| Élément | Rôle |
|---|---|
| `remove_module(...)` | retire un module du registre et de ses fichiers copiés |
| `FileRemovalDecision` | décision par fichier (action, raison) |
| `ModuleRemoveResult` | résultat de la suppression |
| `ModuleNotInstalledError` | le module n'est pas dans le registre |
| `ModuleRemoveError` | erreur lors de la désinstallation |

## 3. Le contrat

La suppression décide fichier par fichier (supprimer, conserver si modifié…), pour ne pas détruire du travail utilisateur. Un *dry-run* montre ce qui serait fait.

## 4. Contextes d'utilisation

- **`module:remove`** : désinstaller proprement un module.

## 5. Voir aussi

- [Le registre](registry.md) et [l'installation des fichiers](files.md).
