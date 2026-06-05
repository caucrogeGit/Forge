"""Starter Sonder un audio — palier 1 du niveau avancé (progression welcome-audio).

Ticket : STARTER-AUDIO-PROBE-001.

``probe_audio`` lance ``ffprobe`` (lecture seule) sur un fichier audio stocké et
retourne ses métadonnées : durée, codec, bitrate, fréquence d'échantillonnage,
canaux, conteneur. Il valide aussi que la durée reste sous la limite configurée.

  ``index`` — `GET /audio-probe?path=...` : sonde le fichier (chemin relatif au
              stockage audio) et affiche ses métadonnées, ou une erreur si
              ``ffprobe`` est absent ou le flux invalide.

``ffprobe`` (binaire système) est requis. Aucune base de données, aucune écriture.
"""
import os

from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_audio import AudioProbeError, load_audio_config, probe_audio


def _probe_view(rel_path: str) -> dict:
    if not rel_path:
        return {"path": ""}
    cfg = load_audio_config()
    abs_path = os.path.join(cfg.storage_root, rel_path)
    try:
        meta = probe_audio(abs_path)
    except AudioProbeError as exc:
        return {"path": rel_path, "error": str(exc)}
    except Exception as exc:  # ffprobe absent, fichier introuvable…
        return {"path": rel_path, "error": f"Sondage impossible : {exc}"}
    return {
        "path": rel_path,
        "meta": {
            "duration_seconds": meta.duration_seconds,
            "audio_codec": meta.audio_codec,
            "bitrate_kbps": meta.bitrate_kbps,
            "sample_rate_hz": meta.sample_rate_hz,
            "channels": meta.channels,
            "container": meta.container,
        },
    }


class AudioProbeController(BaseController):
    """Starter pédagogique : extraire les métadonnées d'un audio via ffprobe."""

    @staticmethod
    def index(request: Request) -> Response:
        rel = request.param("path") or ""
        return BaseController.render(
            "audio_probe/index.html", context=_probe_view(rel), request=request
        )
