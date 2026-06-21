"""Commande ``forge opt-in:list`` — OPTINS-CLI-LIST-001 (renommée OPTIN-CLI-REMOVE-LEGACY-001).

Affiche l'**état local** des opt-ins connus dans un projet Forge.
Commande **strictement lecture seule** : elle ne crée, ne modifie et
n'installe rien. Elle se contente d'inspecter le **texte** de quelques
fichiers du projet (``optins/`` et ``mvc/routes.py``).

Contrat strict (chantier opt-ins) :

- **aucune écriture** (ni ``optins/``, ni ``registry.py``, ni
  ``mvc/routes.py``) ;
- **aucun import** de paquet opt-in (``forge_mvc_*``) ; seul le catalogue
  statique ``forge_cli.optins.catalog`` est lu ;
- **pas de discovery magique** : seuls les opt-ins de type ``route``
  (``iot``, ``video``, ``audio``) reçoivent une couche ``optins/<name>/`` ;
  leur état projet est analysé par lecture de fichiers connus ;
- **pas de scan global** des paquets Python installés.

États distingués pour chaque opt-in ``route`` :

- ``absent``  : ``optins/<name>/`` absent ;
- ``partiel`` : ``optins/<name>/`` présent mais ``register_optins(router)``
  absent de ``mvc/routes.py`` ;
- ``activé``  : ``optins/<name>/`` présent **et** ``register_optins(router)``
  présent dans ``mvc/routes.py``.

Les opt-ins ``library`` et ``crosscutting`` n'ont pas de couche projet :
ils sont listés avec leur kind (sans état projet).
"""

from __future__ import annotations

from pathlib import Path

from forge_cli.optins.catalog import (
    KIND_CROSSCUTTING,
    KIND_LIBRARY,
    KIND_ROUTE,
    OFFICIAL_OPTINS,
)

__all__ = [
    "STATE_ABSENT",
    "STATE_PARTIAL",
    "STATE_ACTIVE",
    "KNOWN_OPTINS",
    "detect_optin_state",
    "detect_iot_state",
    "list_optins",
    "main",
]

STATE_ABSENT = "absent"
STATE_PARTIAL = "partiel"
STATE_ACTIVE = "activé"

# Opt-ins de type ``route`` dont cette commande sait analyser l'état projet
# (couche ``optins/<name>/``). Dérivé du catalogue, dans l'ordre de déclaration.
KNOWN_OPTINS: tuple[str, ...] = tuple(
    name for name, opt in OFFICIAL_OPTINS.items() if opt.kind == KIND_ROUTE
)

_ROUTES_CALL = "register_optins(router)"


def detect_optin_state(project_root: Path, name: str) -> dict[str, object]:
    """Inspecte (lecture seule) l'état d'un opt-in ``route`` dans le projet.

    Retourne un dict avec ``state`` et quelques indicateurs de présence,
    sans jamais importer ni écrire quoi que ce soit. Le branchement
    ``register_optins(router)`` est partagé par tous les opt-ins (un seul
    appel dans ``mvc/routes.py``) ; la distinction par opt-in porte sur la
    présence de ``optins/<name>/``.
    """
    routes_py = project_root / "optins" / name / "routes.py"
    registry_py = project_root / "optins" / "registry.py"
    mvc_routes = project_root / "mvc" / "routes.py"

    structure_present = routes_py.exists()
    registry_present = registry_py.exists()

    routes_branched = False
    if mvc_routes.exists():
        routes_branched = _ROUTES_CALL in mvc_routes.read_text(
            encoding="utf-8", errors="replace"
        )

    if not structure_present:
        state = STATE_ABSENT
    elif routes_branched:
        state = STATE_ACTIVE
    else:
        state = STATE_PARTIAL

    return {
        "state": state,
        "structure_present": structure_present,
        "registry_present": registry_present,
        "routes_branched": routes_branched,
    }


def detect_iot_state(project_root: Path) -> dict[str, object]:
    """Compat : état de l'opt-in IoT. Voir :func:`detect_optin_state`."""
    return detect_optin_state(project_root, "iot")


def _print_route_optin(name: str, info: dict[str, object]) -> None:
    state = info["state"]
    print(f"  {name:<9} {state}")

    if state == STATE_ABSENT:
        print(f"            conseil   : forge opt-in:enable {name} --apply")
        return

    print(f"            structure : optins/{name}/")
    if info["registry_present"]:
        print("            registry  : optins/registry.py")

    if info["routes_branched"]:
        print(
            "            routes    : register_optins(router) présent "
            "dans mvc/routes.py"
        )
    else:
        print(
            "            routes    : register_optins(router) absent "
            "de mvc/routes.py"
        )
        print(f"            conseil   : forge opt-in:enable {name} --apply")


def _print_other_optins() -> None:
    """Liste les opt-ins non-routiers avec leur kind (OPTIN-KIND-ADAPTER-001).

    Lecture seule, aucun import de paquet opt-in : on ne lit que le catalogue
    statique (forge_cli), pas les paquets ``forge_mvc_*``.
    """
    labels = {
        KIND_LIBRARY: "bibliothèque",
        KIND_CROSSCUTTING: "transversal",
    }
    for opt in OFFICIAL_OPTINS.values():
        if opt.kind == KIND_ROUTE:
            continue  # détaillés à part (état projet détecté ci-dessus)
        label = labels.get(opt.kind, opt.kind)
        print(f"  {opt.name:<9} {label}")


def list_optins(*, project_root: Path) -> int:
    """Affiche l'état des opt-ins connus. Toujours ``0`` (lecture seule)."""
    print("Forge opt-ins")
    print("")
    for name in KNOWN_OPTINS:
        _print_route_optin(name, detect_optin_state(project_root, name))
        print("")
    _print_other_optins()
    print("")
    print("Aucune modification effectuée.")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge opt-in:list``.

    Aucune option pour ce ticket (``--help`` est intercepté en amont par
    le dispatcher central). Lecture seule.
    """
    return list_optins(project_root=Path.cwd())
