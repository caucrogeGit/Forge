# pyright: strict
"""Commandes CLI de forge-mvc-images, découvertes par le cœur (ADR-059).

Table déclarative légère exposée via l'entry point ``forge_mvc.commands`` ; le
cœur (dispatch_optin) importe le handler paresseusement à l'invocation.
"""
from __future__ import annotations

COMMANDS: dict[str, dict[str, str | bool]] = {
    "images:init": {"module": "forge_mvc_images.cli.init"},
    # images:orphans ne se connecte pas : une variante est orpheline si son
    # original manque sur le disque, ce qui se lit sans base (donc pas de
    # `config: True`). Affiche par defaut, supprime sur --delete.
    "images:orphans": {"module": "forge_mvc_images.cli.orphans"},
}
