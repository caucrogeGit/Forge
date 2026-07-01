# pyright: strict
"""Table de dispatch des commandes CLI livrées par les opt-ins (ADR-059).

`forge.py` délègue ici la résolution des commandes opt-in : import paresseux
du handler, échec propre « module … non installé » si l'opt-in n'est pas
installé, puis appel avec le bon mode de passage des arguments et de gestion
du code de retour.

La table est explicite (pas de scan d'imports caché, principe 3 de la charte) :
ajouter une commande opt-in se fait par une ligne, sans toucher la chaîne de
dispatch du cœur.
"""
from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import Any, Callable, cast

from cli._support.errors import cli_fail

# ADR-059 (entry points) : les opt-ins déclarent leurs commandes CLI via ce
# groupe d'entry points (comme les backends BDD, ADR-054). Le cœur les découvre
# à l'exécution ; il n'a donc plus besoin de les lister lui-même.
_ENTRY_POINT_GROUP = "forge_mvc.commands"


@dataclass(frozen=True)
class OptinCommand:
    """Descripteur d'une commande livrée par un paquet opt-in."""

    module: str                   # module à importer paresseusement
    package: str                  # nom PyPI (pour le message « non installé »)
    attr: str = "main"            # attribut appelable dans le module
    pip_pre: bool = False         # `pip install --pre` (paquets non encore stables)
    pass_full_args: bool = False  # le handler reçoit les args complets (commande incluse)
    exit_on_rc: bool = True       # sys.exit(rc) si le handler renvoie un code non nul
    hint: str | None = None       # message d'aide personnalisé (sinon généré)

    def install_hint(self) -> str:
        if self.hint is not None:
            return self.hint
        pre = "--pre " if self.pip_pre else ""
        return f"installe le module opt-in : pip install {pre}{self.package}"


def _group(commands: tuple[str, ...], spec: OptinCommand) -> dict[str, OptinCommand]:
    """Associe plusieurs noms de commande à un même descripteur (namespace)."""
    return {name: spec for name in commands}


OPTIN_COMMANDS: dict[str, OptinCommand] = {
    **_group(
        ("upload:init", "media:init"),
        OptinCommand(
            "cli.assets.uploads", "forge-mvc-files",
            pass_full_args=True, exit_on_rc=False,
            hint="installe l'opt-in upload : pip install forge-mvc-files",
        ),
    ),
    **_group(
        ("mail:init", "mail:test", "mail:render", "mail:doctor", "mail:logs"),
        OptinCommand("forge_mvc_mail.cli", "forge-mvc-mail",
                     pip_pre=True, pass_full_args=True, exit_on_rc=False),
    ),
    "settings:init": OptinCommand("forge_mvc_settings.cli.init", "forge-mvc-settings", pip_pre=True),
    "audit:init": OptinCommand("forge_mvc_audit.cli.init", "forge-mvc-audit", pip_pre=True),
    "jobs:init": OptinCommand("forge_mvc_jobs.cli.init", "forge-mvc-jobs", pip_pre=True),
    "notifications:init": OptinCommand(
        "forge_mvc_notifications.cli.init", "forge-mvc-notifications", pip_pre=True
    ),
    "audio:doctor": OptinCommand("forge_mvc_audio.cli.doctor", "forge-mvc-audio"),
    "video:doctor": OptinCommand("forge_mvc_video.cli.doctor", "forge-mvc-video"),
    "video:init": OptinCommand("forge_mvc_video.cli.init", "forge-mvc-video"),
    "video:process": OptinCommand("forge_mvc_video.cli.process", "forge-mvc-video"),
    "video:upload": OptinCommand("forge_mvc_video.cli.upload", "forge-mvc-video"),
    "video:cleanup": OptinCommand("forge_mvc_video.cli.cleanup", "forge-mvc-video"),
    "admin:init": OptinCommand("forge_mvc_admin.cli.init", "forge-mvc-admin"),
    "admin:doctor": OptinCommand("forge_mvc_admin.cli.doctor", "forge-mvc-admin"),
    **_group(
        ("deploy:init", "deploy:check"),
        OptinCommand("forge_mvc_deploy.cli.deploy", "forge-mvc-deploy",
                     pip_pre=True, pass_full_args=True, exit_on_rc=False),
    ),
    **_group(
        ("rbac:validate", "rbac:audit"),
        OptinCommand("forge_mvc_rbac.cli", "forge-mvc-rbac",
                     pip_pre=True, pass_full_args=True, exit_on_rc=False),
    ),
}


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
    """Toutes les commandes opt-in connues : table statique + découverte.

    Source unique pour les garde-fous (« telle commande est-elle dispatchée ? »)
    quel que soit le mode d'enregistrement de l'opt-in (statique ou entry point).
    """
    return {**_discovered_commands(), **OPTIN_COMMANDS}


def dispatch_optin(command: str, args: list[str]) -> bool:
    """Exécute une commande opt-in si elle est connue.

    Résolution : table statique (opt-ins pas encore migrés), puis découverte par
    entry points (ADR-059). Renvoie True si la commande a été prise en charge,
    False sinon. Échoue proprement (cli_fail) si l'opt-in n'est pas installé.
    """
    spec = OPTIN_COMMANDS.get(command) or _discovered_commands().get(command)
    if spec is None:
        return False
    try:
        module = importlib.import_module(spec.module)
    except ImportError:
        cli_fail(f"module {spec.package} non installé.", hint=spec.install_hint())
    handler: Callable[[list[str]], Any] = getattr(module, spec.attr)
    rc = handler(args if spec.pass_full_args else args[1:])
    if spec.exit_on_rc and rc:
        sys.exit(rc)
    return True
