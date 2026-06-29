# L'ingestion d'une vidéo dans Forge

Ce document décrit comment `forge_mvc_video` reçoit et enregistre une vidéo téléversée.

Le fichier de code correspondant est `forge_mvc_video/ingest.py`.

## 1. À quoi sert ce module ?

L'**ingestion** valide un upload vidéo (taille, extension), stocke la source à un emplacement sûr, et enregistre la vidéo dans le dépôt.
La validation profonde (vrai conteneur, durée) appartient au [sondage](probe.md) ; aucun `ffmpeg` n'est lancé ici.

## 2. Ingérer une vidéo

```python
from forge_mvc_video.ingest import ingest_video, VideoIngestError

try:
    record = ingest_video(data, filename="clip.mov", title="Mon clip")
except VideoIngestError as err:
    return Response.text(str(err), status=400)
```

## 3. La signature

```python
def ingest_video(
    data: bytes,
    filename: str,
    *,
    title: str | None = None,
    config: VideoConfig | None = None,
    repository: VideoRepository | None = None,
    now: datetime | None = None,
) -> dict[str, Any]
```

Contrairement à l'audio, l'ingestion vidéo **enregistre** la vidéo dans un dépôt (`repository`) en plus de stocker la source : le traitement (transcodage) est ensuite asynchrone.

## 4. Les validations et erreurs

L'ingestion refuse un fichier vide, trop volumineux (`max_upload_mb`) ou d'extension non autorisée, en levant `VideoIngestError`.

## 5. Contextes d'utilisation

- **Contrôleur d'upload** : `ingest_video(data, filename)` puis déclencher le traitement.
- **Tests** : injecter `config` et `repository` pour des résultats déterministes.

## 6. Voir aussi

- [Le sondage](probe.md) : la validation profonde, après l'ingestion.
- [Le traitement](process.md) : orchestre sondage, poster et transcodage.
- [La configuration](config.md).
