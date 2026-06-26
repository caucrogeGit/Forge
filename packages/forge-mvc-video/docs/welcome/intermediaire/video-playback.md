# Lire une vidéo

Objectif : **servir** une vidéo en streaming HTTP, sans écrire de code métier.

**Ce que vous allez apprendre :** `register_video_routes(router)`. Une seule
ligne branche la route de lecture officielle `GET /videos/{uuid}`, qui sert le
fichier en **streaming HTTP avec support des requêtes Range** (un lecteur peut se
positionner dans la vidéo). Le code vit dans le paquet `forge-mvc-video` ; votre
application ne fait que le **brancher** : principe « lock + delegate ».

Palier 2 du **niveau intermédiaire** de la progression vidéo, après
[Téléverser une vidéo](video-upload.md).

## Ce que ce starter montre

- le branchement de la lecture officielle avec `register_video_routes(router)` ;
- la route `GET /videos/{uuid}` en **streaming Range** ;
- aucun contrôleur à écrire : on délègue au paquet.

Aucun contrôleur à créer ici : la lecture vient entièrement du paquet
`forge-mvc-video`, branché par `register_video_routes`. La table `videos` est
garantie par la migration fournie plus bas.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_video.register_video_routes` | Brancher la route de lecture officielle sur le routeur. | [Parcours vidéo](../../parcours.md) |

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

## La route

Branchez la route de lecture officielle dans `mvc/routes.py`. Le code métier
vit dans le paquet `forge-mvc-video` ; on ne fait que le brancher.

```python
# mvc/routes.py
from forge_mvc_video import register_video_routes

register_video_routes(router)
```

### Comprendre ce code

- `register_video_routes(router)` enregistre la route officielle d'un coup. Vous
  n'écrivez **aucun** contrôleur : le code métier appartient au paquet,
  l'application le **branche** explicitement (pas de découverte automatique,
  principe « refuser la magie cachée »).
- La lecture gère le **streaming Range** : indispensable pour qu'un lecteur
  vidéo charge progressivement et se positionne sans tout télécharger.
- La route sert le fichier référencé par la ligne `videos` : l'UUID, jamais le
  nom de fichier d'origine.

## La migration

La route de lecture sert les fichiers référencés par la table `videos`. Créez
donc cette table si elle n'existe pas déjà. `CREATE TABLE IF NOT EXISTS` reste
sûr même si le palier upload l'a déjà créée.

```sql
-- mvc/migrations/20260601210000_create_videos.sql
CREATE TABLE IF NOT EXISTS videos (
    id               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    uuid             CHAR(36)        NOT NULL,
    title            VARCHAR(255)    NULL,
    original_path    VARCHAR(500)    NOT NULL,
    mp4_path         VARCHAR(500)    NULL,
    poster_path      VARCHAR(500)    NULL,
    mime_type        VARCHAR(120)    NULL,
    size_bytes       BIGINT UNSIGNED NOT NULL,
    duration_seconds INT UNSIGNED    NULL,
    width            INT UNSIGNED    NULL,
    height           INT UNSIGNED    NULL,
    status           VARCHAR(30)     NOT NULL,
    error_message    TEXT            NULL,
    created_at       DATETIME(6)     NOT NULL,
    updated_at       DATETIME(6)     NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_videos_uuid (uuid),
    INDEX idx_videos_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## À retenir

- `register_video_routes(router)` branche la lecture officielle en une ligne.
- Le streaming **Range** permet de se positionner dans la vidéo.
- L'application **délègue** au paquet au lieu de réécrire le service de fichiers.

## Après ce starter

Vous savez servir une vidéo. La suite : suivre son **cycle de vie**.

[Suivre l'état d'une vidéo](video-status.md)
