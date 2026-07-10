# pyright: strict
"""Commandes CLI de forge-mvc-video, découvertes par le cœur (ADR-059).

Table déclarative légère exposée via l'entry point ``forge_mvc.commands`` ; le
cœur (dispatch_optin) importe le handler paresseusement à l'invocation.
"""
from __future__ import annotations

# `config: True` amorce la config projet (env/dev) avant le handler : upload/process/
# cleanup lisent et écrivent la table vidéo (VideoRepository -> core.database.db) et ont
# besoin des identifiants applicatifs (ADR-072, retour terrain 016 F39). video:doctor est
# un diagnostic statique et video:init copie une migration : aucun n'amorce.
COMMANDS: dict[str, dict[str, str | bool]] = {
    "video:doctor": {"module": "forge_mvc_video.cli.doctor"},
    "video:init": {"module": "forge_mvc_video.cli.init"},
    "video:process": {"module": "forge_mvc_video.cli.process", "config": True},
    "video:upload": {"module": "forge_mvc_video.cli.upload", "config": True},
    "video:cleanup": {"module": "forge_mvc_video.cli.cleanup", "config": True},
}
