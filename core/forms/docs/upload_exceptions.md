# Les exceptions d'upload dans Forge

Ce document décrit la hiérarchie d'exceptions de validation et de service de fichier.

Le fichier de code correspondant est `core/forms/upload_exceptions.py`.

## 1. À quoi sert ce module ?

Ces exceptions, **restées dans le cœur** (ADR-019), signalent un upload refusé ou un échec de stockage.
Elles sont réexportées par l'opt-in d'upload pour confort.

## 2. La hiérarchie

| Exception | Cas |
|---|---|
| `UploadError` | erreur de base de validation / service d'upload |
| `UploadTooLargeError` | fichier au-delà de la taille maximale |
| `UploadInvalidExtensionError` | extension non autorisée |
| `UploadInvalidMimeTypeError` | type MIME non autorisé |
| `UploadStorageError` | écriture ou suppression impossible |

## 3. Contextes d'utilisation

- **Validation** : levées par [la validation d'upload](upload_validation.md).
- **Service** : `UploadStorageError` à l'écriture/suppression (opt-in d'upload).

## 4. Voir aussi

- [La validation d'upload](upload_validation.md).
