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

Les niveaux **intermédiaire** (couche médias en base) et **avancé** (couverture,
suppression, sécurité) compléteront cette aide-mémoire au fil de leur livraison.
