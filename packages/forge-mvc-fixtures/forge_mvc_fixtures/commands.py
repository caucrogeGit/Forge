# pyright: strict
"""Commandes CLI de forge-mvc-fixtures, découvertes par le cœur (ADR-059).

Table déclarative légère exposée via l'entry point ``forge_mvc.commands`` ; le
cœur (dispatch_optin) importe le handler paresseusement à l'invocation.

**Vide au scaffold (ADR-074).** ``fixtures:load`` et ``fixtures:purge`` sont
livrées aux tickets suivants. Elles porteront ``config: True`` : chacune ouvre
une connexion BDD et a besoin des identifiants applicatifs amorcés depuis
``env/dev`` (ADR-072), comme ``sessions:gc``.
"""
from __future__ import annotations

COMMANDS: dict[str, dict[str, str | bool]] = {}
