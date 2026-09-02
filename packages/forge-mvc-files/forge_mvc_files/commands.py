# pyright: strict
"""Commandes CLI de forge-mvc-files (upload), découvertes par le cœur (ADR-059).

Table déclarative légère exposée via l'entry point ``forge_mvc.commands``. La
glue CLI vit dans le cœur (``cli.assets.uploads``), qui tire ``forge_mvc_files``
paresseusement ; le handler dispatche lui-même, il reçoit donc les arguments
complets (``full``).
"""
from __future__ import annotations

_UPLOAD: dict[str, str | bool] = {
    "module": "cli.assets.uploads",
    "full": True,
    "exit_rc": False,
}

COMMANDS: dict[str, dict[str, str | bool]] = {
    "upload:init": _UPLOAD,
    "media:init": _UPLOAD,
    # files:init écrit la migration du registre (ADR-094). Il n'ouvre aucune
    # connexion : il rend du SQL et l'écrit dans mvc/migrations/.
    "files:init": {"module": "forge_mvc_files.cli_init"},
    # files:orphans rapproche le disque et le registre. Affiche par défaut,
    # ne supprime que sur --delete (charte §7).
    "files:orphans": {"module": "forge_mvc_files.cli_orphans", "config": True},
}
