# pyright: strict
"""Commandes CLI de forge-mvc-mail, découvertes par le cœur (ADR-059).

Table déclarative légère exposée via l'entry point ``forge_mvc.commands``. Le
handler ``forge_mvc_mail.cli:main`` dispatche lui-même sur la sous-commande, il
reçoit donc les arguments complets (``full``) et ne renvoie pas de code.
"""
from __future__ import annotations

_MAIL: dict[str, str | bool] = {
    "module": "forge_mvc_mail.cli",
    "full": True,
    "exit_rc": False,
}

COMMANDS: dict[str, dict[str, str | bool]] = {
    "mail:init": _MAIL,
    "mail:test": _MAIL,
    "mail:render": _MAIL,
    "mail:doctor": _MAIL,
    "mail:logs": _MAIL,
}
