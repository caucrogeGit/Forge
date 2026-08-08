# pyright: strict
"""Commandes CLI de forge-mvc-audit, découvertes par le cœur (ADR-059).

Table déclarative légère exposée via l'entry point ``forge_mvc.commands`` ; le
cœur (dispatch_optin) importe le handler paresseusement à l'invocation.
"""
from __future__ import annotations

# `config: True` amorce la config projet (env/dev) avant le handler : `audit:gc`
# ouvre une connexion BDD et a besoin des identifiants applicatifs (ADR-072).
# `audit:init` reste SANS config, il rend du SQL sans jamais se connecter.
COMMANDS: dict[str, dict[str, str | bool]] = {
    "audit:init": {"module": "forge_mvc_audit.cli.init"},
    "audit:gc": {"module": "forge_mvc_audit.cli.gc", "config": True},
}
