# Le traitement d'image dans Forge

Ce document explique comment `forge_mvc_images` valide, écrit et décline en variantes une image téléversée.

Le fichier de code correspondant est `forge_mvc_images/processing.py`.

## 1. À quoi sert ce module ?

Une image n'est pas un fichier comme un autre : il faut vérifier que c'est bien une image (pas un script déguisé), puis en produire des **variantes** (miniature, taille moyenne) pour l'affichage.

Ce module porte le traitement d'image (Pillow), extrait du cœur (ADR-018, principe 8).
Il s'appuie sur l'upload générique de [`forge-mvc-files`](../../files/references/manager.md) pour l'écriture, et y ajoute la couche **image-aware** : validation de contenu et variantes.

## 2. Le traitement dans Forge

```python
from forge_mvc_images import save_image_upload

saved = save_image_upload(request.file("photo"), category="avatars")
print(saved.variants)   # {"medium": "...", "thumbnail": "..."}
```

## 3. Téléverser une image

| Fonction | Rôle |
|---|---|
| `save_image_upload(file, category="images", *, variants=True)` | chemin image-aware : vérifie le contenu, écrit, génère les variantes ; retourne un `SavedUpload` |
| `save_image(file, *, category="images", entity_name=None, entity_id=None, …)` | upload et sauvegarde, en retournant un `MediaRecord` (association à une entité) |
| `verify_image_content(data)` | vérifie que `data` est bien une image raster d'un format autorisé ; lève sinon |

`verify_image_content` regarde le **contenu réel** (via Pillow), pas l'extension : un `.png` qui n'est pas une image est rejeté.

## 4. Les variantes

| Fonction | Rôle |
|---|---|
| `generate_image_variants(path, *, root=None)` | génère les variantes `medium` et `thumbnail` d'une image stockée |
| `image_variant_paths(path, *, root=None)` | les chemins **physiques** des variantes |
| `image_variant_relative_paths(path)` | les chemins **media relatifs** des variantes |

Les tailles sont fixées par la constante `IMAGE_VARIANT_SIZES`.
Les formats acceptés sont décrits par `ALLOWED_IMAGE_EXTENSIONS` et `ALLOWED_IMAGE_MIME_TYPES`.

## 5. L'enregistrement (`MediaRecord`)

`MediaRecord` est l'association générique entre un fichier média et une entité Forge :

| Attribut | Contenu |
|---|---|
| `filename`, `original_name`, `path` | l'identité du fichier |
| `category`, `size`, `mime_type` | ses métadonnées |
| `entity_name`, `entity_id` | l'entité à laquelle il est rattaché |
| `usage`, `position`, `is_main` | son rôle dans la galerie |

## 6. Contextes d'utilisation

- **Upload d'avatar / photo** : `save_image_upload(...)`.
- **Image rattachée à une entité** : `save_image(..., entity_name="article", entity_id=42)`.
- **Affichage responsive** : servir la variante `thumbnail` ou `medium` selon le contexte.

## 7. Voir aussi

- [Le dépôt de médias](media_repository.md) : enregistrer et lister les médias en base.
- [La galerie](media_gallery.md) : couverture et galerie d'une entité.
- [L'upload générique (forge-mvc-files)](../../files/references/manager.md) : la brique d'écriture sous-jacente.
