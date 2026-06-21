# L'ingestion d'un fichier audio dans Forge

Ce document explique comment `forge_mvc_audio` reçoit un fichier audio téléversé, ce qu'il vérifie et ce qu'il range sur le disque.

Le fichier de code correspondant est `forge_mvc_audio/ingest.py`.

## 1. À quoi sert l'ingestion ?

Quand un utilisateur téléverse un audio, on ne veut pas l'enregistrer aveuglément.
L'**ingestion** est l'étape qui valide l'upload (taille, extension), lui attribue un identifiant et le range proprement.

Cette étape est **sans état** : aucune base de données, aucun `ffmpeg`.
Elle fait une validation **basique** ; la validation profonde (vrai flux audio, durée) appartient au [sondage](probe.md).

## 2. L'ingestion dans Forge

Une seule fonction, appelable depuis un contrôleur ou un script :

```python
from forge_mvc_audio import ingest_audio, AudioIngestError

try:
    record = ingest_audio(data, filename="chanson.wav", title="Ma chanson")
except AudioIngestError as err:
    return Response.text(str(err), status=400)
```

## 3. La signature

```python
def ingest_audio(
    data: bytes,
    filename: str,
    *,
    title: str | None = None,
    config: AudioConfig | None = None,
    uuid: str | None = None,
) -> dict[str, Any]
```

| Paramètre | Rôle |
|---|---|
| `data` | le contenu binaire du fichier téléversé |
| `filename` | le nom d'origine, utilisé pour l'extension et le type MIME |
| `title` | un titre facultatif (espaces seuls = `None`) |
| `config` | un `AudioConfig` ; à défaut, chargé depuis l'environnement |
| `uuid` | force l'identifiant (sinon un `uuid4` est généré) |

## 4. Ce qu'elle retourne

Un enregistrement, sous forme de dictionnaire :

| Clé | Type | Contenu |
|---|---|---|
| `uuid` | `str` | l'identifiant du fichier (sert de nom de stockage) |
| `title` | `str \| None` | le titre nettoyé |
| `original_path` | `str` | le chemin relatif où la source a été rangée |
| `size_bytes` | `int` | la taille reçue |
| `mime_type` | `str \| None` | le type MIME deviné depuis le nom |

Le stockage est **uuid-based** : le nom du fichier sur le disque vient de l'`uuid`, jamais du nom fourni par l'utilisateur (pas de *path traversal*).

## 5. Les validations

Deux contrôles, dans cet ordre :

- **taille** : un fichier vide est refusé ; au-delà de `max_upload_mb` (200 Mo par défaut), refusé ;
- **extension** : seules les extensions audio autorisées passent ; toute autre est refusée.

## 6. Les erreurs

`AudioIngestError` (sous-classe de `ValueError`) est levée quand l'upload est refusé : fichier vide, trop volumineux, ou extension non autorisée.
Le message précise la cause et la limite dépassée.

## 7. Contextes d'utilisation

- **Contrôleur d'upload** : `ingest_audio(request.file("audio").read(), filename)`.
- **Script d'import** : ingérer en masse depuis le disque.
- **Tests** : injecter un `config` (mapping) et un `uuid` fixe pour des résultats déterministes.

## 8. Voir aussi

- [La configuration audio](config.md) : `max_upload_mb` et le dossier de stockage.
- [Le sondage d'un audio](probe.md) : la validation profonde, après l'ingestion.
- [Le transcodage en MP3](transcode.md) : produire le fichier jouable.
- [La lecture HTTP](http.md) : servir le fichier ingéré.
