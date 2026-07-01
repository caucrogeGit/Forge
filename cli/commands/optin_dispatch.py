# pyright: strict
"""Dispatch des commandes CLI livrées par les opt-ins (ADR-059).

Les commandes sont **découvertes** via les entry points `forge_mvc.commands` :
chaque opt-in les déclare dans son propre `pyproject.toml` (pointant vers une
table déclarative légère `<pkg>.commands:COMMANDS`), le cœur ne les liste plus.
La déclaration reste explicite (pas de scan d'imports caché, principe 3 de la
charte). Le handler est importé paresseusement à l'invocation.
"""
from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import Any, Callable, cast

from cli._support.errors import cli_fail

# Groupe d'entry points par lequel les opt-ins déclarent leurs commandes CLI
# (à l'image des backends BDD, ADR-054).
_ENTRY_POINT_GROUP = "forge_mvc.commands"


@dataclass(frozen=True)
class OptinCommand:
    """Descripteur d'une commande livrée par un paquet opt-in."""

    module: str                   # module à importer paresseusement
    package: str                  # nom PyPI (pour le message « non installé »)
    attr: str = "main"            # attribut appelable dans le module
    pass_full_args: bool = False  # le handler reçoit les args complets (commande incluse)
    exit_on_rc: bool = True       # sys.exit(rc) si le handler renvoie un code non nul


_discovered_cache: dict[str, OptinCommand] | None = None


def _discovered_commands() -> dict[str, OptinCommand]:
    """Commandes découvertes via les entry points ``forge_mvc.commands``.

    Chaque opt-in installé expose une table déclarative légère (chaînes) ; on la
    charge sans importer le handler (résolu paresseusement à l'invocation).
    Résultat mémoïsé : la découverte ne lit les métadonnées qu'une fois.
    """
    global _discovered_cache
    if _discovered_cache is not None:
        return _discovered_cache
    discovered: dict[str, OptinCommand] = {}
    for ep in entry_points(group=_ENTRY_POINT_GROUP):
        table = cast("dict[str, dict[str, object]]", ep.load())
        for name, spec in table.items():
            module = str(spec["module"])
            # forge_mvc_iot.cli.doctor -> forge-mvc-iot (pour un éventuel message).
            package = "-".join(module.split(".", 1)[0].split("_"))
            discovered[name] = OptinCommand(
                module=module,
                package=package,
                attr=str(spec.get("attr", "main")),
                pass_full_args=bool(spec.get("full", False)),
                exit_on_rc=bool(spec.get("exit_rc", True)),
            )
    _discovered_cache = discovered
    return _discovered_cache


def all_optin_commands() -> dict[str, OptinCommand]:
    """Toutes les commandes opt-in connues (découvertes par entry points).

    Source unique pour les garde-fous (« telle commande est-elle dispatchée ? »).
    """
    return dict(_discovered_commands())


def dispatch_optin(command: str, args: list[str]) -> bool:
    """Exécute une commande opt-in si elle est découverte (ADR-059).

    Renvoie True si la commande a été prise en charge, False sinon. Échoue
    proprement (cli_fail) si le module de l'opt-in est introuvable.
    """
    spec = _discovered_commands().get(command)
    if spec is None:
        return False
    try:
        module = importlib.import_module(spec.module)
    except ImportError:
        cli_fail(
            f"module {spec.package} non installé.",
            hint=f"installe le module opt-in : pip install {spec.package}",
        )
    handler: Callable[[list[str]], Any] = getattr(module, spec.attr)
    rc = handler(args if spec.pass_full_args else args[1:])
    if spec.exit_on_rc and rc:
        sys.exit(rc)
    return True
