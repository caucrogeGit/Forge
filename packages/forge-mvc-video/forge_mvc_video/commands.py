# pyright: strict
"""Commandes CLI de forge-mvc-video, découvertes par le cœur (ADR-059).

Table déclarative légère exposée via l'entry point ``forge_mvc.commands`` ; le
cœur (dispatch_optin) importe le handler paresseusement à l'invocation.
"""
from __future__ import annotations

COMMANDS: dict[str, dict[str, str | bool]] = {
    "video:doctor": {"module": "forge_mvc_video.cli.doctor"},
    "video:init": {"module": "forge_mvc_video.cli.init"},
    "video:process": {"module": "forge_mvc_video.cli.process"},
    "video:upload": {"module": "forge_mvc_video.cli.upload"},
    "video:cleanup": {"module": "forge_mvc_video.cli.cleanup"},
}
