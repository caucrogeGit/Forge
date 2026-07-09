# pyright: strict
"""Commandes CLI de forge-mvc-entities, découvertes par le cœur (ADR-059/070).

Table déclarative légère exposée via l'entry point ``forge_mvc.commands``. Le
cœur la lit sans importer les handlers (résolus paresseusement à l'invocation par
``cli.commands.optin_dispatch``). Chaque entrée : ``module`` (importé à
l'invocation), ``attr`` (appelable, défaut ``main``), ``full`` (le handler reçoit
les arguments complets, commande incluse), ``exit_rc`` (``sys.exit`` si le handler
renvoie un code non nul).

Les handlers d'entités ne quittent pas sur leur code de retour (``exit_rc`` à
False), sauf ``db:config`` qui propage son code. ``db:init`` et ``db:apply``
gardent un traitement dédié dans le cœur (aide, arguments) et ne sont pas ici.
"""
from __future__ import annotations

_PKG = "forge_mvc_entities"

_MODEL: dict[str, object] = {"module": f"{_PKG}.model", "full": True, "exit_rc": False}
_MIGR: dict[str, object] = {"module": f"{_PKG}.migrations", "full": True, "exit_rc": False}

COMMANDS: dict[str, dict[str, object]] = {
    "make:entity": {"module": f"{_PKG}.make_entity", "exit_rc": False},
    "make:crud": {"module": f"{_PKG}.make_crud", "attr": "cmd_make_crud_main", "exit_rc": False},
    "make:relation": {"module": f"{_PKG}.make_relation", "exit_rc": False},
    "make:pivot-crud": {
        "module": f"{_PKG}.make_pivot_crud", "attr": "cmd_make_pivot_crud_main", "exit_rc": False,
    },
    "entity:validate": {"module": f"{_PKG}.entity_validate", "exit_rc": False},
    "entity:doc": {"module": f"{_PKG}.entity_doc", "exit_rc": False},
    "sync:entity": _MODEL,
    "sync:relations": _MODEL,
    "build:model": _MODEL,
    "check:model": _MODEL,
    "migration:status": _MIGR,
    "migration:apply": _MIGR,
    "migration:make": _MIGR,
    "migration:diff": _MIGR,
    "db:config": {"module": f"{_PKG}.db_config", "exit_rc": True},
}
