# La lecture audio HTTP dans Forge

Ce document explique comment `forge_mvc_audio` sert un fichier audio en streaming, et comment brancher cette route dans une application.

Le fichier de code correspondant est `forge_mvc_audio/http.py`.

## 1. À quoi sert ce module ?

Une fois un audio ingéré et transcodé, il faut pouvoir le **lire** depuis le navigateur.
Ce module branche une route de **lecture en streaming**, avec support du *seek* (HTTP Range), pour qu'un lecteur audio puisse avancer dans la piste sans tout télécharger.

Le module est **sans état** et reste **opt-in** : c'est l'application qui appelle `register_audio_routes` explicitement.
Aucune écriture dans `mvc/routes/__init__.py` (charte §9).

## 2. Brancher la route dans Forge

```python
from forge_mvc_audio import register_audio_routes

def register_routes(router):
    register_audio_routes(router)   # ajoute GET /audio/{uuid}
    return router
```

`register_audio_routes(router, *, config=None)` ajoute la route et retourne le `router` (chaînable).
Sans `config`, la configuration est chargée depuis l'environnement.

## 3. La route exposée

| Élément | Valeur |
|---|---|
| Méthode et chemin | `GET /audio/{uuid}` (constante `ROUTE_PLAYBACK`) |
| Nom de route | `audio_stream` |
| Réponse | le fichier audio en streaming, avec support HTTP **Range** |
| Caractéristiques | `public=True`, `csrf=False`, `api=False` |

Le streaming et le Range sont délégués à la primitive cœur `Response.file`.

## 4. Pourquoi c'est sûr

Le chemin servi n'est **jamais** construit depuis l'URL : il est **retrouvé sur le disque** à partir de l'`uuid` (le MP3 transcodé de préférence, sinon la source).
L'`uuid` est validé comme UUID canonique → aucun *path traversal* possible.

Si le fichier est introuvable, la route répond `404` avec un corps JSON `{"error": …}`, sans divulguer de chemin.

## 5. La protection par jeton (facultative)

La lecture peut être protégée, sur le modèle des modules Vidéo et IoT :

- si `FORGE_AUDIO_API_TOKEN` est défini, la route exige `Authorization: Bearer <token>` (comparaison en temps constant) ; à défaut, elle répond `401` ;
- s'il est absent, la route est **ouverte** : mode local / pédagogique.

L'authentification vit **dans ce module**, jamais dans Forge Core.

## 6. Le contrôleur (`AudioHttpController`)

`register_audio_routes` instancie `AudioHttpController`, dont la méthode `stream(request)` porte la logique : autorisation, résolution du chemin par `uuid`, réponse fichier ou erreur.
Vous l'utilisez rarement en direct ; il est exposé pour les tests et les usages avancés.

## 7. Contextes d'utilisation

- **Application** : `register_audio_routes(router)` au câblage des routes.
- **Déploiement protégé** : positionner `FORGE_AUDIO_API_TOKEN` pour exiger un Bearer.
- **Tests** : appeler `AudioHttpController.stream` avec une requête simulée.

## 8. Voir aussi

- [Le transcodage en MP3](transcode.md) : produit le fichier que cette route sert.
- [La configuration audio](config.md) : `storage_root` et `api_token`.
- [L'ingestion d'un fichier audio](ingest.md) : l'entrée du pipeline.
