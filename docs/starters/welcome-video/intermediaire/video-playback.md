# Lire une vidéo

Objectif : **servir** une vidéo en streaming HTTP, sans écrire de code métier.

**Ce que vous allez apprendre :** `register_video_routes(router)`. Une seule
ligne branche la route de lecture officielle `GET /videos/{uuid}`, qui sert le
fichier en **streaming HTTP avec support des requêtes Range** (un lecteur peut se
positionner dans la vidéo). Le code vit dans le paquet `forge-mvc-video` ; votre
application ne fait que le **brancher** — principe « lock + delegate ».

Palier 2 du **niveau intermédiaire** de la progression vidéo, après
[Téléverser une vidéo](video-upload.md).

## Ce que ce starter montre

- le branchement de la lecture officielle avec `register_video_routes(router)` ;
- la route `GET /videos/{uuid}` en **streaming Range** ;
- aucun contrôleur à écrire : on délègue au paquet.

La table `videos` est garantie par la migration livrée.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_video.register_video_routes` | Brancher la route de lecture officielle sur le routeur. | [Parcours vidéo](../../../video/parcours.md) |

## Tester

```bash
forge db:init
forge run
```

Après avoir téléversé une vidéo (palier précédent), ouvrez son URL de lecture
avec son UUID :

```
https://localhost:8000/videos/<uuid>
```

Le fichier est servi en streaming ; un lecteur vidéo peut se positionner grâce au
support des requêtes **Range**.

## Le branchement

```python
# mvc/routes.py (extrait inséré par le starter)
from forge_mvc_video import register_video_routes

register_video_routes(router)
```

### Comprendre ce code

- `register_video_routes(router)` enregistre la route officielle d'un coup. Vous
  n'écrivez **aucun** contrôleur : le code métier appartient au paquet,
  l'application le **branche** explicitement (pas de découverte automatique —
  principe « refuser la magie cachée »).
- La lecture gère le **streaming Range** : indispensable pour qu'un lecteur
  vidéo charge progressivement et se positionne sans tout télécharger.
- La route sert le fichier référencé par la ligne `videos` — l'UUID, jamais le
  nom de fichier d'origine.

## À retenir

- `register_video_routes(router)` branche la lecture officielle en une ligne.
- Le streaming **Range** permet de se positionner dans la vidéo.
- L'application **délègue** au paquet au lieu de réécrire le service de fichiers.

## Après ce starter

Vous savez servir une vidéo. La suite : suivre son **cycle de vie**.

[Suivre l'état d'une vidéo](video-status.md)
