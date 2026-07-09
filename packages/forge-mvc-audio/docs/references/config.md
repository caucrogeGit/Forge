# La configuration audio dans Forge

Ce document explique comment le module `forge_mvc_audio` lit sa configuration, ce qu'elle contient et comment l'obtenir dans votre code.

Le fichier de code correspondant est `forge_mvc_audio/config.py`.

## 1. À quoi sert la configuration ?

Le module audio a besoin de quelques réglages pour travailler : où trouver `ffmpeg`, où ranger les fichiers, quelle taille d'upload accepter.
La configuration rassemble ces réglages en un seul endroit, au lieu de les disperser dans le code.

Ce module est **pur** : il ne lit aucun fichier, ne lance aucun `ffmpeg` et n'écrit nulle part. Il fixe seulement le **contrat de configuration** ; ce sont les autres modules (ingestion, transcodage…) qui s'en servent.

## 2. La configuration dans Forge

La configuration est portée par l'objet `AudioConfig`.
Vous ne le remplissez pas à la main : la fonction `load_audio_config()` le construit pour vous depuis l'environnement.

```python
from forge_mvc_audio import load_audio_config

config = load_audio_config()
print(config.storage_root)   # "storage/audio" par défaut
```

`AudioConfig` est **gelé** (immuable) : une fois chargé, il ne change plus pendant la requête.

## 3. Ce qu'elle contient

L'objet `AudioConfig` rassemble les réglages du module :

| Attribut | Type | Défaut | Contenu |
|---|---|---|---|
| `ffmpeg_bin` | `str` | `ffmpeg` | le binaire `ffmpeg` à appeler pour le transcodage |
| `ffprobe_bin` | `str` | `ffprobe` | le binaire `ffprobe` à appeler pour le sondage |
| `storage_root` | `str` | `storage/audio` | le dossier racine où sont rangés les fichiers audio |
| `max_upload_mb` | `int` | `200` | la taille maximale d'un upload, en mégaoctets |
| `max_duration_seconds` | `int` | `7200` | la durée maximale d'un audio accepté, en secondes |
| `api_token` | `str \| None` | `None` | le jeton facultatif protégeant les routes de lecture (voir §6) |

## 4. Les variables d'environnement

Chaque réglage se surcharge par une variable d'environnement, sans toucher au code :

| Variable | Règle | Attribut |
|---|---|---|
| `FORGE_AUDIO_FFMPEG_BIN` | chemin du binaire | `ffmpeg_bin` |
| `FORGE_AUDIO_FFPROBE_BIN` | chemin du binaire | `ffprobe_bin` |
| `FORGE_AUDIO_STORAGE_ROOT` | dossier de stockage | `storage_root` |
| `FORGE_AUDIO_MAX_UPLOAD_MB` | entier positif | `max_upload_mb` |
| `FORGE_AUDIO_MAX_DURATION_SECONDS` | entier positif | `max_duration_seconds` |
| `FORGE_AUDIO_API_TOKEN` | jeton (chaîne) | `api_token` |

Les noms de ces variables sont eux-mêmes exposés comme constantes (`ENV_FFMPEG_BIN`, `ENV_STORAGE_ROOT`…) si vous devez les référencer dans vos tests.

## 5. Charger la configuration

```python
def load_audio_config(source: Mapping[str, str] | None = None) -> AudioConfig
```

`load_audio_config()` lit `os.environ` par défaut.
Pour les tests, vous pouvez injecter un dictionnaire à la place via `source` : le module ne touche alors jamais au véritable environnement.

```python
config = load_audio_config({"FORGE_AUDIO_MAX_UPLOAD_MB": "50"})
assert config.max_upload_mb == 50
```

Deux règles de lecture protègent contre les valeurs douteuses :

- une variable **absente ou vide** retombe sur la valeur par défaut ;
- pour les entiers, une valeur **non numérique ou négative** est ignorée et le défaut s'applique : impossible de configurer une taille d'upload de `-1` ou `abc`.

## 6. Le jeton d'API (`api_token`)

`api_token` est une protection **facultative** des routes de lecture audio.

- S'il est défini (`FORGE_AUDIO_API_TOKEN`), un en-tête `Authorization: Bearer <token>` est exigé pour lire un fichier.
- S'il est absent (`None`), les routes sont ouvertes : c'est le mode **local / pédagogique** par défaut.

## 7. Contextes d'utilisation

- **Démarrage du module** : `load_audio_config()` une fois, puis passez le `config` aux autres fonctions.
- **Tests** : `load_audio_config({...})` avec un mapping injecté, sans variable d'environnement réelle.
- **Déploiement** : positionnez les `FORGE_AUDIO_*` dans l'environnement du serveur.

## 8. Voir aussi

- [Ingestion d'un fichier audio](ingest.md) : le premier consommateur de `AudioConfig`.
- [Sondage d'un audio](probe.md) : utilise `ffprobe_bin` et `max_duration_seconds`.
- [Transcodage en MP3](transcode.md) : utilise `ffmpeg_bin`.
- [Progression pédagogique Audio](../welcome/debutant/audio-welcome.md) : apprendre le module pas à pas.
