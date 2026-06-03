# Opt-in Forge Video — branchement local

Ce dossier **branche** le paquet opt-in `forge-mvc-video` dans ce projet.
Le code métier vit dans le paquet ; ici, uniquement le câblage local.

## Ce que branche cet opt-in

`optins/video/routes.py` appelle `register_video_routes(router)`, qui expose
la **route de lecture vidéo officielle** (streaming HTTP Range) :

- `GET /videos/{uuid}`

Le branchement est **explicite** : `mvc/routes.py` appelle
`register_optins(router)` → `optins/registry.py` → `optins/video/routes.py`.
Aucune découverte automatique.

## Migration à installer

La table `videos` est nécessaire pour stocker les vidéos et leur statut :

```bash
forge video:init        # copie la migration vers mvc/migrations/
forge migration:apply   # crée la table videos
```

## Parcours type

```bash
forge video:upload film.mp4 --title "Ma vidéo"   # → statut uploaded
forge video:process --pending                    # transcodage MP4 + poster
# puis lecture : GET /videos/{uuid}
```

`ffmpeg`/`ffprobe` sont requis pour le traitement (vérifier avec
`forge video:doctor`). Voir aussi `forge video:cleanup` pour la purge.

## Documentation complète

La doc de référence reste **officielle** (pas dupliquée ici) :
<https://forgemvc.com/docs/forge/video/>.
