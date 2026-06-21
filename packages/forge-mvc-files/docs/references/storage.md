# Les primitives de stockage dans Forge

Ce document décrit les primitives bas niveau de `forge_mvc_files` : écrire un fichier sur le disque et garantir la sûreté des chemins.

Le fichier de code correspondant est `forge_mvc_files/storage.py`.

## 1. À quoi sert ce module ?

Là où le [manager](manager.md) orchestre l'upload, le `storage` fait le travail concret : écrire des octets, supprimer un fichier, et surtout **valider les chemins** pour qu'un nom de fichier malveillant ne puisse pas sortir du dossier de stockage.

C'est le module le plus sensible côté sécurité : tout passe par lui pour fermer le *path traversal*.

## 2. Écrire et supprimer

| Fonction | Rôle |
|---|---|
| `save_bytes(data, *, original_name, category, root)` | écrit `data` sous `category/`, avec un nom sûr et unique ; retourne le `Path` écrit |
| `delete_file(path, *, root)` | supprime un fichier sous `root` ; retourne `True` s'il existait |

Le nom de stockage est dérivé d'un identifiant unique (`uuid`), jamais directement du nom fourni par l'utilisateur.

## 3. La sûreté des chemins

C'est le cœur sécurité du module :

| Fonction | Rôle |
|---|---|
| `secure_filename(filename)` | nettoie un nom de fichier (retire chemins, caractères dangereux) |
| `normalize_media_path(path)` | retourne un chemin media relatif, normalisé et sûr |
| `is_safe_media_path(path)` | indique si un chemin media est sûr (pas de traversal) |
| `media_path_to_storage_path(path, *, root)` | convertit un chemin media en chemin disque sous `root` |

Un chemin contenant `..`, une racine absolue ou des séparateurs suspects est rejeté ou neutralisé : impossible de lire ou d'écrire hors du dossier de stockage.

## 4. La séparation chemin media / chemin disque

Forge distingue deux notions :

- le **chemin media** : relatif, stable, exposé dans les URLs et stocké en base (`contracts/<uuid>.pdf`) ;
- le **chemin disque** : absolu, sous `root`, jamais exposé.

`media_path_to_storage_path` fait le pont de l'un vers l'autre, en validant au passage.

## 5. Les erreurs

`save_bytes` / `delete_file` lèvent `UploadStorageError` (du cœur, `core.forms.upload_exceptions`) si l'écriture ou la suppression échoue.

## 6. Contextes d'utilisation

- **Usage courant** : passez par le [manager](manager.md), pas par `storage` directement.
- **Usage avancé** : `save_bytes` pour écrire un contenu généré (et non téléversé).
- **Validation** : `is_safe_media_path` avant de servir un chemin reçu d'une source externe.

## 7. Voir aussi

- [L'upload générique](manager.md) : la façade qui appelle ces primitives.
- [Le rate-limit d'upload](rate_limit.md).
