# forge-mvc-images

Module **opt-in** propriétaire de tout l'image dans Forge MVC : traitement
(variantes, miniatures, validation de contenu — Pillow) **et** couche médias
applicative (repository, galerie, couverture).

## Statut : Beta (extraction terminée, ADR-018)

`forge-mvc-images` est désormais l'unique propriétaire de tout l'image dans
Forge. Le traitement (Pillow) et la couche applicative médias ont été rapatriés
du core et de l'ancien `forge-mvc-media`, qui est supprimé. Le paquet expose une
API publique stable :

- **Traitement** : `save_image`, `save_image_upload`, `generate_image_variants`,
  `image_variant_paths`, `image_variant_relative_paths`, `verify_image_content`,
  plus les constantes `ALLOWED_IMAGE_EXTENSIONS`, `ALLOWED_IMAGE_MIME_TYPES`,
  `variant_presets()`, déclarés par `IMAGE_VARIANTS`.
- **Couche applicative médias** : `MediaRecord`, `create_media_record`,
  `get_media_record`, `delete_media`, `delete_media_record`,
  `attach_media_to_entity`, `list_media_for_entity`, `get_media_gallery`,
  `get_cover_media`, `media_url`, `update_media_alt_text`,
  `update_media_position`.

Ce paquet dépend de `forge-mvc-files` (upload générique) et de Pillow.

## Pourquoi ce module (ADR-018)

`forge-mvc-images` **remplace** `forge-mvc-media`. Le nom « media » était
trompeur depuis l'arrivée de `forge-mvc-video` (un développeur attendait que
`forge-mvc-media` gère aussi la vidéo). Par ailleurs, embarquer Pillow et le
traitement d'image dans le core contredit le principe de **noyau minimal**
(charte principe 8, ADR-004).

Décision (option B, « renommer puis rapatrier ») :

- le **core** ne garde aucune logique d'upload ni d'image : l'upload générique
  vit dans `forge-mvc-files`, l'image dans `forge-mvc-images` ;
- `forge-mvc-images` devient l'**unique** propriétaire de tout l'image,
  traitement **et** couche applicative.

Conformément à la **convention pré-1.0** (pas d'utilisateurs externes), le
renommage s'est fait **sans alias déprécié ni guide de migration** :
`forge-mvc-media` a été supprimé une fois le rapatriement terminé.

## Plan d'exécution (ADR-018, terminé)

| Ticket | Description | État |
|---|---|---|
| `IMAGES-PKG-SCAFFOLD-001` | Squelette du paquet (`pyproject.toml` + Pillow, `__init__`) | livré |
| `IMAGES-MOVE-PROCESSING-001` | Déplacer le traitement image du core ; rendre `save_upload` générique | livré |
| `IMAGES-MOVE-APPLICATIVE-001` | Déplacer repository + galerie depuis `forge-mvc-media` | livré |
| `CORE-DROP-PILLOW-001` | Retrait de Pillow du core, inversion des garde-fous packaging | livré |
| `CLI-CRUD-IMAGES-RENAME-001` | Générateurs CLI vers `forge_mvc_images` | livré |
| `CI-DOCS-IMAGES-RENAME-001` | CI, README racine, docs, CONTRIBUTING | livré |
| `REMOVE-MEDIA-PKG-001` | Suppression de `packages/forge-mvc-media` | livré |

## Installation (mode éditable, depuis les sources)

```bash
git clone https://github.com/caucrogeGit/Forge.git
cd Forge
pip install -e packages/forge-mvc-images/
```

## Référence

- `docs/adr/018-image-module-extraction.md` — décision et périmètre figés.
- Charte principes 8 (noyau minimal), 11 (une seule façon officielle).
