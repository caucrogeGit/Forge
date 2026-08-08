# pyright: strict
"""Commandes CLI de forge-mvc-mfa, découvertes par le cœur (ADR-059).

Table déclarative légère exposée via l'entry point ``forge_mvc.commands`` ; le
cœur (dispatch_optin) importe le handler paresseusement à l'invocation.
"""
from __future__ import annotations

# `mfa:init` reste SANS `config: True` : rendre le DDL exige l'identité du
# backend, résolue par entry point (ADR-054, un seul backend par projet), pas
# les identifiants de connexion. Aucune connexion n'est ouverte, le SQL est
# écrit et non exécuté (charte §7). Même raisonnement que `sessions:init`.
COMMANDS: dict[str, dict[str, str | bool]] = {
    "mfa:init": {"module": "forge_mvc_mfa.cli.init"},
}
