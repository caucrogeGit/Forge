# Le transcodage MP3 dans Forge

Ce document explique comment `forge_mvc_audio` convertit un fichier audio source en MP3 standard avec `ffmpeg`.

Le fichier de code correspondant est `forge_mvc_audio/transcode.py`.

## 1. À quoi sert le transcodage ?

Les sources téléversées sont de formats variés (`wav`, `ogg`, `flac`…), pas toujours lisibles directement par un navigateur.
Le **transcodage** produit un MP3 standard, propre et jouable partout, à partir de la source.

Le constructeur de commande est **pur** (testable sans `ffmpeg`) ; seule l'exécution réelle appelle `ffmpeg`.

## 2. Le transcodage dans Forge

```python
from forge_mvc_audio import transcode_to_mp3, FfmpegError

try:
    transcode_to_mp3("storage/audio/<uuid>.wav", "storage/audio/<uuid>.mp3")
except FfmpegError as err:
    return Response.text(str(err), status=500)
```

## 3. La signature

```python
def transcode_to_mp3(
    input_path: str,
    output_path: str,
    *,
    ffmpeg_bin: str = "ffmpeg",
    bitrate_kbps: int = 192,
    runner: FfmpegRunner | None = None,
    timeout: int = DEFAULT_TRANSCODE_TIMEOUT,
) -> None
```

| Paramètre | Rôle |
|---|---|
| `input_path` | la source à transcoder |
| `output_path` | le MP3 à produire |
| `ffmpeg_bin` | le binaire `ffmpeg` à appeler |
| `bitrate_kbps` | le débit du MP3 (192 kb/s par défaut) |
| `runner` | runner injectable (tests sans `ffmpeg`) |
| `timeout` | délai maximal en secondes (`DEFAULT_TRANSCODE_TIMEOUT` = 1800, soit 30 min) |

La fonction ne retourne rien : elle écrit `output_path`, ou lève une erreur.

## 4. Le profil MP3 standard

Forge Audio applique un profil fixe, lisible dans la commande générée :

| Option `ffmpeg` | Effet |
|---|---|
| `-c:a libmp3lame -b:a 192k` | encodage MP3 à 192 kb/s |
| `-ac 2` | sortie stéréo (2 canaux) |
| `-map_metadata -1` | retire les métadonnées d'origine |
| `-vn` | ignore toute piste vidéo / pochette → audio pur |

## 5. Construire la commande sans l'exécuter (`build_transcode_command`)

`build_transcode_command(ffmpeg_bin, input_path, output_path, bitrate_kbps=192)` retourne la **liste d'arguments** `ffmpeg`, sans rien lancer.
C'est la partie pure : on peut vérifier la commande en test, à l'octet près.

## 6. Sécurité d'invocation

Trois garde-fous protègent l'appel à `ffmpeg` :

- arguments en **liste** (jamais `shell=True`) → aucune injection de commande ;
- un chemin commençant par `-` est préfixé par `./` pour ne pas être lu comme une option `ffmpeg` ;
- `timeout` obligatoire : un `ffmpeg` sans borne pourrait tourner indéfiniment.

## 7. Les erreurs

`FfmpegError` est levée si `ffmpeg` est introuvable, dépasse le délai, ou termine sur un code d'erreur.
Le message reprend le code de sortie et la sortie d'erreur de `ffmpeg`.

## 8. Contextes d'utilisation

- **Après sondage** : produire le MP3 jouable une fois la source validée.
- **Traitement asynchrone** : appeler depuis une tâche de fond (le transcodage peut être long).
- **Tests** : injecter un `runner` qui simule le code retour de `ffmpeg`.

## 9. Voir aussi

- [Le sondage d'un audio](probe.md) : l'étape de validation qui précède.
- [La lecture HTTP](http.md) : servir le MP3 produit.
- [La configuration audio](config.md) : `ffmpeg_bin`.
