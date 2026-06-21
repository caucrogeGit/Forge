# L'upload générique dans Forge

Ce document explique l'API de haut niveau de `forge_mvc_files` : valider et écrire un fichier téléversé, le servir, le supprimer.

Le fichier de code correspondant est `forge_mvc_files/manager.py`.

## 1. À quoi sert ce module ?

`forge_mvc_files` porte l'**upload générique** de Forge (extrait du cœur, ADR-019) : recevoir un fichier, le valider, l'écrire à un emplacement sûr, puis le servir ou le supprimer.

Le `manager` est la **façade de haut niveau** : il enchaîne validation, stockage et service.
La validation *pure* (extension, MIME, taille) reste au cœur (`core/forms`) ; le stockage bas niveau est dans [storage](storage.md).

## 2. L'upload dans Forge

```python
from forge_mvc_files import save_upload, serve_media_file

saved = save_upload(request.file("document"), category="contracts")
print(saved.path, saved.size)
```

## 3. Stocker un upload (`save_upload`)

```python
def save_upload(file: object, category: str = "documents") -> SavedUpload
```

`save_upload` **valide** le fichier (extension, MIME, taille), l'**écrit** sous `category/`, et retourne un `SavedUpload`.
En cas de refus, une erreur d'upload du cœur est levée (voir §6).

L'objet `SavedUpload` décrit le fichier écrit :

| Attribut | Type | Contenu |
|---|---|---|
| `filename` | `str` | le nom de fichier généré (sûr) |
| `original_name` | `str` | le nom d'origine fourni par l'utilisateur |
| `path` | `str` | le chemin media relatif (sert d'identifiant et d'URL) |
| `category` | `str` | la catégorie de rangement |
| `size` | `int` | la taille en octets |
| `mime_type` | `str \| None` | le type MIME détecté |
| `variants` | `dict[str, str]` | les variantes éventuelles (rempli par l'opt-in images) |

## 4. Servir un fichier (`serve_media_file`)

```python
def serve_media_file(path: str, *, root=None, request=None) -> Response
```

`serve_media_file` renvoie une `Response` qui **diffuse** le fichier en streaming, avec support HTTP **Range** (seek), via la primitive cœur `Response.file`.
Passez `request` pour activer le Range.

## 5. Supprimer et localiser

| Fonction | Rôle |
|---|---|
| `delete_upload(path)` | supprime un fichier uploadé ; retourne `True` s'il existait |
| `delete_media_file(path, *, root=None, variants=False)` | supprime un média et, si `variants=True`, ses variantes |
| `get_upload_path(filename, category="documents")` | le chemin disque d'un fichier d'une catégorie |
| `upload_root()` | la racine de stockage configurée |

## 6. Les erreurs

La validation lève des erreurs définies **dans le cœur** (`core.forms.upload_exceptions`), réexportées pour confort : `UploadError` (base), `UploadInvalidExtensionError`, `UploadInvalidMimeTypeError`, `UploadTooLargeError`, `UploadStorageError`.

```python
from forge_mvc_files import save_upload, UploadError

try:
    saved = save_upload(request.file("doc"))
except UploadError as err:
    return Response.text(str(err), status=400)
```

## 7. Contextes d'utilisation

- **Contrôleur d'upload** : `save_upload(request.file(...))`.
- **Route de téléchargement** : `serve_media_file(path, request=request)`.
- **Suppression d'entité** : `delete_media_file(path, variants=True)`.

## 8. Voir aussi

- [Les primitives de stockage](storage.md) : écriture bas niveau et sécurité des chemins.
- [Le rate-limit d'upload](rate_limit.md) : limiter la fréquence des envois.
- [Progression pédagogique Files](../welcome/installation.md).
