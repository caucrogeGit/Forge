# pyright: strict
"""Forge MVC Audio — module opt-in pour la gestion audio.

Chaîne audio **complète et sans état** (aucune base de données) :

- ``config`` — contrat de configuration (`AudioConfig`, `load_audio_config`) ;
- ``storage`` — disposition uuid-based des fichiers (anti-traversal) ;
- ``probe`` — métadonnées via ``ffprobe`` (durée, codec, bitrate, canaux…) ;
- ``ingest`` — upload validé + stockage (``ingest_audio``) ;
- ``transcode`` — conversion MP3 via ``ffmpeg`` (``transcode_to_mp3``) ;
- ``http`` — lecture en streaming HTTP Range (``register_audio_routes``) ;
- ``cli.project.doctor`` — diagnostic ``forge audio:doctor``.

Volontairement **sobre** : pas de table SQL, pas de suivi de jobs, pas de file
de transcodage. Les opérations sont synchrones et le service de lecture
retrouve les fichiers par ``uuid`` sur le disque. ``ffmpeg``/``ffprobe`` sont
des binaires système (pas des dépendances pip).

Le module reste **opt-in** : l'application appelle ``register_audio_routes``
explicitement. Aucune écriture dans le code utilisateur (charte §9).
"""

from __future__ import annotations

__version__ = "1.0.0rc4"

from forge_mvc_audio.config import AudioConfig, load_audio_config
from forge_mvc_audio.http import register_audio_routes
from forge_mvc_audio.ingest import AudioIngestError, ingest_audio
from forge_mvc_audio.probe import AudioMetadata, AudioProbeError, probe_audio
from forge_mvc_audio.transcode import FfmpegError, transcode_to_mp3

__all__ = [
    "AudioConfig",
    "AudioIngestError",
    "AudioMetadata",
    "AudioProbeError",
    "FfmpegError",
    "ingest_audio",
    "load_audio_config",
    "probe_audio",
    "register_audio_routes",
    "transcode_to_mp3",
]
