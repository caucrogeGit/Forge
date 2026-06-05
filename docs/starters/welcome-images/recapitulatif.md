# Aide-mémoire de la progression Images

Récapitulatif des paliers de la progression *Bonjour Forge Images* et des API du
module opt-in `forge-mvc-images` introduites à chaque étape.

!!! note "Module opt-in"
    Toute cette progression suppose `forge-mvc-images` installé. Le paquet
    dépend de `forge-mvc-files` et n'est pas encore publié sur PyPI : on
    l'installe depuis les sources (palier « Installation » en tête de parcours).
    Le cœur de Forge reste autonome.

## Niveau débutant — traitement (sans base de données)

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Bonjour Forge Images](debutant/images-welcome.md) | Vérifier le module, inspecter formats et tailles de variantes | `ALLOWED_IMAGE_EXTENSIONS`, `IMAGE_VARIANT_SIZES` |
| 2 | [Téléverser une image](debutant/image-upload.md) | Vérifier le contenu avant d'écrire, générer les variantes | `save_image_upload` |
| 3 | [Miniatures et variantes](debutant/image-variants.md) | Dériver les chemins des variantes et leurs URL | `image_variant_relative_paths`, `media_url` |

## Niveau intermédiaire — couche médias en base

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Rattacher une image à une entité](intermediaire/image-attach.md) | Créer une ligne `media` reliée à une entité | `attach_media_to_entity` |
| 2 | [Afficher la galerie](intermediaire/image-gallery.md) | Lire et afficher les images d'une entité avec variantes | `get_media_gallery` |
| 3 | [Texte alternatif et ordre](intermediaire/image-alt-order.md) | Éditer accessibilité et ordre d'affichage | `update_media_alt_text`, `update_media_position` |

Le niveau **avancé** (couverture, suppression, sécurité) complétera cette
aide-mémoire à sa livraison.
