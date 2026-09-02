# pyright: strict
"""Commandes CLI de forge-mvc-audio, découvertes par le cœur (ADR-059).

Table déclarative légère exposée via l'entry point ``forge_mvc.commands`` ; le
cœur (dispatch_optin) importe le handler paresseusement à l'invocation.
"""
from __future__ import annotations

COMMANDS: dict[str, dict[str, str | bool]] = {
    "audio:doctor": {"module": "forge_mvc_audio.cli.doctor"},
    # audio:trim découpe un fichier sans toucher à la source. Le paquet est
    # sans état : aucune connexion, donc pas de `config: True`.
    "audio:trim": {"module": "forge_mvc_audio.cli.trim"},
}
