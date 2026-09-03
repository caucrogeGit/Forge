# pyright: strict
"""Commandes CLI de forge-mvc-workflow, découvertes par le cœur (ADR-059).

Table déclarative légère exposée via l'entry point ``forge_mvc.commands`` ; le
cœur (dispatch_optin) importe le handler paresseusement à l'invocation.
"""
from __future__ import annotations

# workflow:init écrit la migration de l'historique (WORKFLOW-HISTORY-001). Il
# n'ouvre aucune connexion : il rend du SQL et l'écrit dans mvc/migrations/.
COMMANDS: dict[str, dict[str, str | bool]] = {
    "workflow:init": {"module": "forge_mvc_workflow.cli.init"},
}
