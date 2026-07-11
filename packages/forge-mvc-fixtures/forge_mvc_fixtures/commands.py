# pyright: strict
"""Commandes CLI de forge-mvc-fixtures, découvertes par le cœur (ADR-059).

Table déclarative légère exposée via l'entry point ``forge_mvc.commands`` ; le
cœur (dispatch_optin) importe le handler paresseusement à l'invocation.

``config: True`` amorce la config projet (``env/dev`` via ``load_project_config``)
avant le handler : ``fixtures:load`` ouvre une connexion BDD applicative et a
besoin des identifiants (ADR-072), comme ``sessions:gc``. ``fixtures:purge`` est
livrée au ticket suivant.
"""
from __future__ import annotations

COMMANDS: dict[str, dict[str, str | bool]] = {
    "fixtures:load": {"module": "forge_mvc_fixtures.cli.load", "config": True},
}
