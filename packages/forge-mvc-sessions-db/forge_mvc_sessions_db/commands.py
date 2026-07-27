# pyright: strict
"""Commandes CLI de forge-mvc-sessions-db, découvertes par le cœur (ADR-059).

Table déclarative légère exposée via l'entry point ``forge_mvc.commands`` ; le
cœur (dispatch_optin) importe le handler paresseusement à l'invocation.
"""
from __future__ import annotations

# `config: True` amorce la config projet (env/dev) avant le handler : sessions:gc
# ouvre une connexion BDD et a besoin des identifiants applicatifs (ADR-072,
# retour terrain 016 F39).
#
# sessions:init reste SANS config, y compris depuis OPTIN-DDL-SESSIONS-DB-001 où
# il rend son DDL au lieu de copier un fichier figé : rendre exige l'identité du
# backend, résolue par entry point (ADR-054, un seul backend par projet), pas les
# identifiants de connexion. Aucune connexion n'est ouverte, le SQL est écrit et
# non exécuté (charte §7).
COMMANDS: dict[str, dict[str, str | bool]] = {
    "sessions:init": {"module": "forge_mvc_sessions_db.cli.init"},
    "sessions:gc": {"module": "forge_mvc_sessions_db.cli.gc", "config": True},
}
