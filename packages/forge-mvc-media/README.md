# forge-mvc-media

Module opt-in pour la gestion applicative des médias dans Forge MVC.

## Statut : Alpha — opt-in officiel publié sur PyPI depuis 1.0.0-beta.9

`forge-mvc-media` est en statut `3 - Alpha` depuis `MEDIA-PYPI-READY-002`.
L'extraction depuis `core/uploads/` est complète. La documentation et les shims
de compatibilité ont été livrés.

**Publié sur PyPI** depuis `1.0.0-beta.9` (forme PEP 440 : `1.0.0b9`). L'API
applicative reste bêta — voir `docs/production-limits.md` avant déploiement.

Installation :

```bash
pip install --pre forge-mvc-media
```

Pour développer le paquet en mode éditable depuis les sources du dépôt Forge :

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

Les anciens imports `from core.uploads import attach_media_to_entity` ne sont plus
supportés depuis `MEDIA-SHIMS-REMOVE-001`.
Ce package est publié sur PyPI depuis `1.0.0-beta.9` : `pip install --pre forge-mvc-media`.

## Shims de compatibilité dans core

Les fichiers `core/uploads/media_repository.py` et `core/uploads/media_gallery.py`
étaient des shims de compatibilité qui re-exportaient depuis ce module.
Ils ont été supprimés dans `MEDIA-SHIMS-REMOVE-001`.

## Conditions avant publication sur PyPI

Toutes les conditions préparatoires sont remplies depuis `MEDIA-PYPI-READY-002`.
La publication PyPI sera déclenchée par un ticket dédié lors d'une prochaine release.

Les critères étaient :

1. ~~**`MEDIA-DOCS-MIGRATION-001` livré**~~ ✓ livré — documentation technique à jour dans `docs/`.
2. ~~**Shims supprimés**~~ ✓ livré (`MEDIA-SHIMS-REMOVE-001`) — `core/uploads/media_repository.py` et
   `core/uploads/media_gallery.py` retirés du core.
3. ~~**`Development Status` ajusté**~~ ✓ livré (`MEDIA-PYPI-READY-002`) — statut `3 - Alpha` actif.
4. ~~**Classifier retiré**~~ ✓ livré (`MEDIA-PYPI-READY-002`) — `"Private :: Do Not Upload"` supprimé du `pyproject.toml`.

Le ticket de publication PyPI sera `PYPI-PUBLISH-MEDIA-001` (ou `PYPI-PUBLISH-B8-MEDIA-001`
selon la version cible).

## Tickets de référence

| Ticket | Description | État |
|---|---|---|
| `MEDIA-CORE-BOUNDARY-AUDIT-001` | Audit de la frontière core/opt-in | livré |
| `MEDIA-EXTRACT-PACKAGE-SCAFFOLD-001` | Création du squelette source-only | livré |
| `MEDIA-REPOSITORY-MOVE-001` | Déplacement du code applicatif | livré |
| `MEDIA-CRUD-INTEGRATION-OPTIN-001` | Mise à jour des générateurs CLI | livré |
| `MEDIA-DOCS-MIGRATION-001` | Mise à jour de la documentation | livré |
| `MEDIA-SHIMS-REMOVE-001` | Suppression des shims core/uploads | livré |
| `MEDIA-PYPI-READY-001` | Décision source-only confirmée | livré |
| `MEDIA-PYPI-READY-002` | Requalification Alpha, retrait classifier privé | livré |
