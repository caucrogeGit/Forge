# pyright: strict
"""Commandes CLI de forge-mvc-sessions-db, découvertes par le cœur (ADR-059).

Table déclarative légère exposée via l'entry point ``forge_mvc.commands`` ; le
cœur (dispatch_optin) importe le handler paresseusement à l'invocation.
"""
from __future__ import annotations

COMMANDS: dict[str, dict[str, str | bool]] = {
    "sessions:init": {"module": "forge_mvc_sessions_db.cli.init"},
    "sessions:gc": {"module": "forge_mvc_sessions_db.cli.gc"},
}
