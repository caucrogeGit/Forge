# forge-mvc-media

Module opt-in pour la gestion applicative des médias dans Forge MVC.

## Statut : Pre-Alpha — source-only

`forge-mvc-media` est en cours d'extraction depuis `core/uploads/`.

**Non publié sur PyPI dans cette phase.**

Il s'installe uniquement depuis les sources du dépôt Forge :

```bash
git clone https://github.com/caucrogeGit/Forge.git
cd Forge
pip install -e packages/forge-mvc-media/
```

## Ce que contient ce module

Depuis `MEDIA-REPOSITORY-MOVE-001`, le package contient :

- `media_repository` — persistance SQL des métadonnées médias (table `media`) :
  `create_media_record`, `attach_media_to_entity`, `get_media_record`,
  `list_media_for_entity`, `update_media_alt_text`, `update_media_position`,
  `delete_media_record`, `delete_media`

- `media_gallery` — galerie, couverture, URL des médias par entité :
  `get_media_gallery`, `get_cover_media`, `media_url`

## Ce qui reste dans le core (définitif)

Les briques génériques restent dans `core/uploads/` et ne bougent pas :

- `exceptions.py` — hiérarchie UploadError
- `validators.py` — validation extension, MIME type, taille
- `storage.py` — filesystem, protection anti-traversal
- `manager.py` — SavedUpload, save_upload, serve_media_file
- `image.py` — save_image, generate_image_variants (Pillow)
- `rate_limit.py` — rate limiting in-memory

## Note sur les générateurs CLI

À partir de `MEDIA-CRUD-INTEGRATION-OPTIN-001`, les nouveaux générateurs média
applicatifs (`forge make:crud --media`, `forge make:public:list`, `forge make:public:show`)
ciblent `forge_mvc_media` pour les helpers applicatifs :

```python
from core.uploads import save_upload          # générique — reste dans core
from forge_mvc_media import attach_media_to_entity, delete_media, get_cover_media, ...
```

Les anciens imports `from core.uploads import attach_media_to_entity` restent
compatibles temporairement via les shims de compatibilité.
Le package reste source-only et non publié sur PyPI.

## Shims de compatibilité dans core

Les fichiers `core/uploads/media_repository.py` et `core/uploads/media_gallery.py`
sont des shims de compatibilité qui re-exportent depuis ce module.
Ils émettent un `DeprecationWarning` et seront supprimés dans une version future.

## Tickets de référence

| Ticket | Description | État |
|---|---|---|
| `MEDIA-CORE-BOUNDARY-AUDIT-001` | Audit de la frontière core/opt-in | livré |
| `MEDIA-EXTRACT-PACKAGE-SCAFFOLD-001` | Création du squelette source-only | livré |
| `MEDIA-REPOSITORY-MOVE-001` | Déplacement du code applicatif | livré |
| `MEDIA-CRUD-INTEGRATION-OPTIN-001` | Mise à jour des générateurs CLI | livré |
| `MEDIA-DOCS-MIGRATION-001` | Mise à jour de la documentation | à venir |
