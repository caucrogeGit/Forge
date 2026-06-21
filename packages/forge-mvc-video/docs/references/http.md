# La lecture vidéo HTTP dans Forge

Ce document décrit la route de lecture vidéo en streaming et son branchement.

Le fichier de code correspondant est `forge_mvc_video/http.py`.

## 1. À quoi sert ce module ?

Une fois la vidéo traitée, il faut la **lire** depuis le navigateur.
Ce module branche une route de lecture en streaming avec support HTTP **Range** (seek), pour qu'un lecteur vidéo puisse avancer sans tout télécharger.

Le module reste **opt-in** : l'application appelle `register_video_routes` explicitement, sans écriture dans `mvc/routes.py`.

## 2. Brancher la route

```python
from forge_mvc_video import register_video_routes

def register_routes(router):
    register_video_routes(router)
    return router
```

`register_video_routes(router, *, repository=None, config=None)` ajoute la route et retourne le `router` (chaînable).

## 3. La sécurité

Le chemin servi est **retrouvé** à partir de l'identifiant de la vidéo, jamais construit depuis l'URL : aucun *path traversal*.
Si `api_token` est défini (`FORGE_VIDEO_API_TOKEN`), la lecture exige `Authorization: Bearer <token>` ; sinon elle est ouverte (mode local).

## 4. Le contrôleur (`VideoHttpController`)

`register_video_routes` instancie `VideoHttpController(repository, config, *, api_token=None)`, dont les handlers portent l'autorisation, la résolution du chemin et la réponse fichier (streaming + Range via la primitive cœur).

## 5. Contextes d'utilisation

- **Application** : `register_video_routes(router)` au câblage des routes.
- **Déploiement protégé** : `FORGE_VIDEO_API_TOKEN` pour exiger un Bearer.

## 6. Voir aussi

- [Le traitement](process.md) : produit le MP4 que cette route sert.
- [La configuration](config.md) : `storage_root`, `api_token`.
- [L'ingestion](ingest.md) : l'entrée du pipeline.
