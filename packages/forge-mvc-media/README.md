# forge-mvc-media

Module opt-in pour la gestion applicative des médias dans Forge MVC.

## Statut : squelette source-only (Pre-Alpha)

`forge-mvc-media` est en cours d'extraction depuis `core/uploads/`.

**Ce package ne contient pas encore de code fonctionnel.**

Il a été créé comme squelette source-only dans le cadre du ticket
`MEDIA-EXTRACT-PACKAGE-SCAFFOLD-001` (Phase 11).

Le code applicatif (`media_repository`, `media_gallery`) sera déplacé depuis
`core/uploads/` dans le ticket `MEDIA-REPOSITORY-MOVE-001`.

## Non publié sur PyPI

`forge-mvc-media` **n'est pas publié sur PyPI** dans cette phase.

Il s'installe uniquement depuis les sources du dépôt Forge :

```bash
git clone https://github.com/caucrogeGit/Forge.git
cd Forge
pip install -e packages/forge-mvc-media/
```

Sa publication coordonnée est prévue avec `OPTIN-PYPI-PUBLISH-001`,
après extraction complète et validation des tickets 11.3 à 11.5.

## Ce que contiendra ce module (après MEDIA-REPOSITORY-MOVE-001)

- `media_repository` — persistance SQL des métadonnées médias (table `media`)
- `media_gallery` — galerie, couverture, URL des médias par entité

## Ce qui reste dans le core (définitif)

Les briques génériques restent dans `core/uploads/` et ne bougent pas :

- `exceptions.py` — hiérarchie UploadError
- `validators.py` — validation extension, MIME type, taille
- `storage.py` — filesystem, protection anti-traversal
- `manager.py` — SavedUpload, save_upload, serve_media_file
- `image.py` — save_image, generate_image_variants (Pillow)
- `rate_limit.py` — rate limiting in-memory

## Tickets de référence

| Ticket | Description | État |
|---|---|---|
| `MEDIA-CORE-BOUNDARY-AUDIT-001` | Audit de la frontière core/opt-in | livré |
| `MEDIA-EXTRACT-PACKAGE-SCAFFOLD-001` | Création du squelette source-only | livré |
| `MEDIA-REPOSITORY-MOVE-001` | Déplacement du code applicatif | à venir |
| `MEDIA-CRUD-INTEGRATION-OPTIN-001` | Mise à jour des générateurs CLI | à venir |
| `MEDIA-DOCS-MIGRATION-001` | Mise à jour de la documentation | à venir |
