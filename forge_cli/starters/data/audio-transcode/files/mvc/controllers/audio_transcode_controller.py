"""Starter Transcoder en MP3 — palier 2 du niveau avancé (progression welcome-audio).

Ticket : STARTER-AUDIO-TRANSCODE-001.

``transcode_to_mp3`` convertit un fichier source en MP3 standard via ``ffmpeg``.
L'opération est **synchrone** et **sans état** : pas de file de jobs, pas de table
— Forge Audio reste sobre. Un échec ``ffmpeg`` lève ``FfmpegError``.

  ``index``     — `GET  /audio-transcode` : formulaire (CSRF).
  ``transcode`` — `POST /audio-transcode` : transcode le fichier indiqué vers
                  ``transcoded/sortie.mp3`` et confirme, ou montre l'erreur.

``ffmpeg`` (binaire système) est requis. Aucune base de données.
"""
import os

from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_audio import FfmpegError, load_audio_config, transcode_to_mp3

_OUTPUT_REL = "transcoded/sortie.mp3"


class AudioTranscodeController(BaseController):
    """Starter pédagogique : transcoder un audio en MP3 via ffmpeg."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "audio_transcode/index.html",
            context={"csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def transcode(request: Request) -> Response:
        rel = request.form("path")
        context = {"csrf_token": BaseController.csrf_token(request)}
        if not rel:
            context["error"] = "Indiquez le chemin source à transcoder."
            return BaseController.render(
                "audio_transcode/index.html", context=context, request=request
            )
        cfg = load_audio_config()
        abs_in = os.path.join(cfg.storage_root, rel)
        abs_out = os.path.join(cfg.storage_root, _OUTPUT_REL)
        os.makedirs(os.path.dirname(abs_out), exist_ok=True)
        try:
            transcode_to_mp3(abs_in, abs_out, ffmpeg_bin=cfg.ffmpeg_bin)
        except FfmpegError as exc:
            context["error"] = str(exc)
            return BaseController.render(
                "audio_transcode/index.html", context=context, request=request
            )
        except Exception as exc:  # ffmpeg absent, source introuvable…
            context["error"] = f"Transcodage impossible : {exc}"
            return BaseController.render(
                "audio_transcode/index.html", context=context, request=request
            )
        context["output"] = _OUTPUT_REL
        return BaseController.render(
            "audio_transcode/index.html", context=context, request=request
        )
