# La validation d'upload dans Forge

Ce document décrit la validation **pure** des métadonnées d'un fichier téléversé.

Le fichier de code correspondant est `core/forms/upload_validation.py`.

## 1. À quoi sert ce module ?

L'écriture et le stockage des uploads vivent dans l'opt-in d'upload (ADR-019), mais la **validation pure** (extension, MIME, taille) reste dans le **cœur** : elle ne dépend d'aucun opt-in.

## 2. L'API

| Fonction | Rôle |
|---|---|
| `normalize_extensions(...)` | normalise une liste d'extensions autorisées |
| `filename_extension(filename)` | extrait l'extension d'un nom de fichier |
| `validate_filename(...)` | valide le nom de fichier |
| `validate_extension(...)` | valide l'extension contre la liste autorisée |
| `validate_size(...)` | valide la taille contre la limite |
| `validate_mime_type(...)` | valide le type MIME |
| `validate_upload_metadata(...)` | valide l'ensemble des métadonnées et retourne l'extension |

## 3. Contextes d'utilisation

- **Cœur** : valider un upload sans dépendre de l'opt-in de stockage.
- **Opt-in d'upload** : s'appuie sur cette validation avant d'écrire.

## 4. Voir aussi

- [Les exceptions d'upload](upload_exceptions.md) : levées en cas de refus.
