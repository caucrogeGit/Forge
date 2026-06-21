# Le sondage d'un audio dans Forge

Ce document explique comment `forge_mvc_audio` extrait les métadonnées d'un fichier audio et s'en sert pour le valider en profondeur.

Le fichier de code correspondant est `forge_mvc_audio/probe.py`.

## 1. À quoi sert le sondage ?

Une extension de fichier ne prouve rien : un `.mp3` peut être un fichier corrompu, ou pas un audio du tout.
Le **sondage** lance `ffprobe` (lecture seule) sur la source et en lit les vraies caractéristiques : durée, codec, bitrate, fréquence, canaux.

Il sert donc de **validation profonde** : un fichier sans flux audio, ou que `ffprobe` refuse, est rejeté, bien plus fiablement que l'extension vérifiée à l'ingestion.
Aucun `ffmpeg` n'est lancé : `ffprobe` lit, ne transcode pas.

## 2. Le sondage dans Forge

```python
from forge_mvc_audio import probe_audio, AudioProbeError

try:
    meta = probe_audio("storage/audio/<uuid>.wav")
except AudioProbeError as err:
    return Response.text(str(err), status=400)

print(meta.duration_seconds, meta.audio_codec)
```

## 3. Ce que le sondage retourne (`AudioMetadata`)

`AudioMetadata` est un objet **gelé** ; chaque champ vaut `None` si `ffprobe` ne l'a pas fourni :

| Attribut | Type | Contenu |
|---|---|---|
| `duration_seconds` | `int \| None` | la durée en secondes |
| `audio_codec` | `str \| None` | le codec audio (`mp3`, `aac`…) |
| `bitrate_kbps` | `int \| None` | le débit en kilobits par seconde |
| `sample_rate_hz` | `int \| None` | la fréquence d'échantillonnage |
| `channels` | `int \| None` | le nombre de canaux (1 = mono, 2 = stéréo) |
| `container` | `str \| None` | le format conteneur (`wav`, `ogg`…) |

## 4. La validation profonde

Au-delà de l'extraction, `probe_audio` applique deux règles :

- **flux audio obligatoire** : sans piste audio détectée, `AudioProbeError` est levée ;
- **durée bornée** : si la durée dépasse `max_duration_seconds` (2 h par défaut), le fichier est rejeté.

## 5. La signature

```python
def probe_audio(
    path: str,
    *,
    config: AudioConfig | None = None,
    runner: ProbeRunner | None = None,
) -> AudioMetadata
```

L'exécution de `ffprobe` est déléguée à un **runner injectable** (`runner`) : le parsing et la validation sont donc testables **sans `ffprobe` réel**.
L'invocation est sûre : arguments passés en **liste** (jamais `shell=True`), chemin en argument, délai borné.

## 6. Parser une sortie ffprobe (`parse_probe_json`)

`parse_probe_json(payload)` transforme une sortie `ffprobe -print_format json` (chaîne ou dict) en `AudioMetadata`, sans rien exécuter.
Utile pour tester le parsing à partir d'une sortie figée.

## 7. Les erreurs

`AudioProbeError` est levée si `ffprobe` est introuvable, dépasse le délai, échoue, ou si la source n'a aucun flux audio ou dépasse la durée maximale.

## 8. Contextes d'utilisation

- **Après ingestion** : valider la source réellement, avant de transcoder.
- **Affichage** : récupérer durée et codec pour les présenter à l'utilisateur.
- **Tests** : injecter un `runner` qui renvoie une sortie `ffprobe` figée.

## 9. Voir aussi

- [L'ingestion d'un fichier audio](ingest.md) : l'étape qui précède le sondage.
- [Le transcodage en MP3](transcode.md) : l'étape suivante.
- [La configuration audio](config.md) : `ffprobe_bin` et `max_duration_seconds`.
