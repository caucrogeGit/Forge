# pyright: strict
"""Commandes CLI de forge-mvc-fixtures, découvertes par le cœur (ADR-059).

Table déclarative légère exposée via l'entry point ``forge_mvc.commands`` ; le
cœur (dispatch_optin) importe le handler paresseusement à l'invocation.

``config: True`` amorce la config projet (``env/dev`` via ``load_project_config``)
avant le handler : ``fixtures:load`` et ``fixtures:purge`` ouvrent une connexion
BDD applicative et ont besoin des identifiants (ADR-072), comme ``sessions:gc``.
"""
from __future__ import annotations

COMMANDS: dict[str, dict[str, str | bool]] = {
    "fixtures:load": {"module": "forge_mvc_fixtures.cli.load", "config": True},
    "fixtures:purge": {"module": "forge_mvc_fixtures.cli.purge", "config": True},
    "fixtures:generate": {"module": "forge_mvc_fixtures.cli.generate", "config": True},
    # make-factory ne lit qu'un contrat JSON et écrit un .py : pas de config BDD.
    "fixtures:make-factory": {"module": "forge_mvc_fixtures.cli.make_factory"},
}
