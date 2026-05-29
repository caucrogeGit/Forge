"""Commande ``forge optin:enable <name>`` — OPTINS-CLI-ENABLE-IOT-001.

Branche **localement** un opt-in dans le projet courant en créant la
couche ``optins/`` documentée par
``docs/architecture/optins-project-structure.md`` et cadrée par
``docs/architecture/optins-cli-enable-audit.md``.

Premier (et seul) opt-in supporté par ce ticket : **iot**.

Contrat strict (audit ``OPTINS-CLI-ENABLE-AUDIT-001``) :

- **dry-run par défaut** : sans ``--apply``, rien n'est écrit ;
- **idempotence** : fichier absent → créé ; présent identique → ``[OK]
  déjà présent`` ; présent différent → ``[WARN]`` + **aucune écriture** ;
- **jamais d'écrasement silencieux** ;
- **pas de discovery magique** : le branchement reste explicite via
  ``optins/registry.py`` ;
- **``mvc/routes.py`` n'est PAS modifié automatiquement** : la commande
  affiche seulement l'instruction à ajouter ;
- Forge Core reste indépendant des opt-ins : ce module ne fait
  qu'**écrire des fichiers texte** et vérifie la présence du paquet via
  ``importlib.util.find_spec`` (aucun import de ``forge_mvc_iot`` ici).
"""

from __future__ import annotations

import importlib.util
from collections.abc import Callable
from pathlib import Path

__all__ = [
    "STATUS_OK",
    "STATUS_INFO",
    "STATUS_WARN",
    "STATUS_ERROR",
    "STATUS_DRYRUN",
    "SUPPORTED_OPTINS",
    "enable_optin",
    "main",
]

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_WARN = "[WARN]"
STATUS_ERROR = "[ERREUR]"
STATUS_DRYRUN = "[DRY-RUN]"


# ── Contenu généré pour l'opt-in IoT ────────────────────────────────────────
#
# Cohérent avec la structure produite par le starter `welcome-iot`
# (OPTINS-IOT-PROJECT-BRIDGE-001) : même branchement explicite, mêmes
# fichiers. Le code métier reste dans le paquet `forge-mvc-iot`.

_OPTINS_INIT = '''\
"""Couche de branchement local des opt-ins de ce projet Forge.

Les paquets opt-in restent distribués (`forge-mvc-*`) ; ce dossier ne
contient que le **câblage local** (routes, README, repères de migration).
Branchement explicite via `optins/registry.py` — aucune découverte
automatique. Contrat : docs/architecture/optins-project-structure.md.
"""
'''

_REGISTRY = '''\
"""Registre explicite des opt-ins branchés dans ce projet.

Pas de découverte automatique : chaque opt-in actif est importé et appelé
explicitement dans `register_optins`. Appelé depuis `mvc/routes.py` :

    from optins.registry import register_optins

    register_optins(router)
"""

from __future__ import annotations


def register_optins(router) -> None:
    """Branche les routes des opt-ins activés dans ce projet."""
    from optins.iot.routes import register as register_iot

    register_iot(router)
'''

_IOT_INIT = '''\
"""Branchement local de l'opt-in Forge IoT (paquet `forge-mvc-iot`).

Câblage uniquement : voir `routes.py` et `README.md`. Le code métier vit
dans le paquet ; la doc complète reste officielle (docs/iot/).
"""
'''

_IOT_ROUTES = '''\
"""Branchement local de l'opt-in Forge IoT.

Délègue à l'API publique du paquet `forge-mvc-iot` — ce fichier ne fait
que le câblage. Appelé par `optins/registry.py`.
"""

from __future__ import annotations

from forge_mvc_iot import register_iot_routes


def register(router) -> None:
    """Expose l'API HTTP IoT officielle (lecture seule) :

    - GET /api/iot/events
    - GET /api/iot/events/{site}/{device_id}
    - GET /api/iot/devices/{site}/{device_id}/count
    """
    register_iot_routes(router)
'''

_IOT_README = """\
# Opt-in Forge IoT

Ce dossier branche **localement** l'opt-in Forge IoT dans ce projet. Le
code métier vit dans le paquet `forge-mvc-iot` ; ici, uniquement le
câblage (voir `routes.py`).

Le branchement est **explicite** : `mvc/routes.py` appelle
`register_optins(router)` → `optins/registry.py` → `optins/iot/routes.py`.
Aucune découverte automatique.

## Paquet requis

```bash
pip install --pre forge-mvc-iot
```

## Routes exposées (lecture seule)

- `GET /api/iot/events`
- `GET /api/iot/events/{site}/{device_id}`
- `GET /api/iot/devices/{site}/{device_id}/count`

## Commandes utiles

```bash
forge iot:doctor
forge iot:init
forge migration:apply
forge iot:listen
forge iot:simulate
```

## Documentation complète

<https://forgemvc.com/docs/forge/iot/>
"""

_IOT_MIGRATIONS_README = """\
# Migrations de l'opt-in Forge IoT

La migration `iot_events` est **packagée** dans `forge-mvc-iot` et copiée
dans `mvc/migrations/` par la commande dédiée :

```bash
forge iot:init          # copie *_create_iot_events.sql vers mvc/migrations/
forge migration:apply   # applique la migration (crée la table iot_events)
```

Ce dossier sert de **repère** : `forge optin:enable iot` n'applique
aucune migration automatiquement. Le SQL reste visible et appliqué
explicitement.
"""


# Liste ordonnée (chemin relatif au projet, contenu). L'ordre fixe la
# sortie de la commande.
_IOT_FILES: tuple[tuple[str, str], ...] = (
    ("optins/__init__.py", _OPTINS_INIT),
    ("optins/registry.py", _REGISTRY),
    ("optins/iot/__init__.py", _IOT_INIT),
    ("optins/iot/routes.py", _IOT_ROUTES),
    ("optins/iot/README.md", _IOT_README),
    ("optins/iot/migrations/README.md", _IOT_MIGRATIONS_README),
)


SUPPORTED_OPTINS: dict[str, dict] = {
    "iot": {
        "package_dist": "forge-mvc-iot",
        "package_import": "forge_mvc_iot",
        "files": _IOT_FILES,
    },
}


# ── Branchement mvc/routes.py (affiché, jamais appliqué) ─────────────────────

_ROUTES_INSTRUCTION = (
    "    from optins.registry import register_optins\n"
    "\n"
    "    register_optins(router)"
)


def _print_routes_instruction() -> None:
    print("")
    print(
        f"{STATUS_INFO} Branche les opt-ins dans mvc/routes.py "
        "(non modifié automatiquement) :"
    )
    print("")
    for line in _ROUTES_INSTRUCTION.splitlines():
        print(f"    {line}")


def _is_package_available(import_name: str) -> bool:
    return importlib.util.find_spec(import_name) is not None


def enable_optin(
    name: str,
    *,
    apply: bool = False,
    project_root: Path,
    package_check: Callable[[str], bool] | None = None,
) -> int:
    """Active l'opt-in ``name`` dans ``project_root`` (dry-run par défaut).

    Retourne le code de sortie :

    - ``2`` : opt-in inconnu ;
    - ``1`` : paquet requis absent, ou (en ``--apply``) conflit bloquant ;
    - ``0`` : succès (création, idempotent, ou dry-run).
    """
    spec = SUPPORTED_OPTINS.get(name)
    if spec is None:
        print(f"{STATUS_ERROR} opt-in inconnu : {name}")
        available = ", ".join(sorted(SUPPORTED_OPTINS))
        print(f"Opt-ins disponibles : {available}")
        return 2

    print(f"Forge opt-in enable — {name}")
    print("")

    # Vérification du paquet (même en dry-run : on ne propose pas un
    # branchement vers un paquet absent).
    check = package_check or _is_package_available
    if not check(spec["package_import"]):
        print(
            f"{STATUS_ERROR} Le package {spec['package_dist']} "
            "n'est pas installé."
        )
        print(f"Conseil : pip install --pre {spec['package_dist']}")
        return 1

    conflict = False
    for rel, content in spec["files"]:
        target = project_root / rel
        encoded = content.encode("utf-8")

        if target.exists():
            if target.read_bytes() == encoded:
                print(f"{STATUS_OK} {rel} déjà présent")
            else:
                conflict = True
                print(
                    f"{STATUS_WARN} {rel} existe déjà avec un contenu "
                    "différent."
                )
                print("       Aucune modification. Vérifie le fichier "
                      "manuellement.")
            continue

        if apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            print(f"{STATUS_OK} {rel} créé")
        else:
            print(f"{STATUS_DRYRUN} {rel} serait créé")

    _print_routes_instruction()

    print("")
    if not apply:
        print(f"{STATUS_INFO} Aucune modification écrite.")
        print(f"{STATUS_INFO} Relance avec --apply pour appliquer.")
        return 0

    if conflict:
        print(
            f"{STATUS_WARN} Des fichiers existants diffèrent — "
            "rien n'a été écrasé."
        )
        return 1

    return 0


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge optin:enable``.

    Usage : ``forge optin:enable <name> [--apply | --dry-run]``. Le
    dry-run est le **comportement par défaut**.
    """
    if args is None:
        args = []

    apply = "--apply" in args
    # ``--dry-run`` est explicite mais redondant avec le défaut ; il est
    # accepté et l'emporte jamais sur l'absence de --apply.
    positionals = [
        a for a in args if not a.startswith("-")
    ]

    if not positionals:
        print(f"{STATUS_ERROR} nom d'opt-in manquant.")
        print("Usage : forge optin:enable <name> [--apply]")
        print(f"Opt-ins disponibles : {', '.join(sorted(SUPPORTED_OPTINS))}")
        return 2

    name = positionals[0]
    return enable_optin(name, apply=apply, project_root=Path.cwd())
