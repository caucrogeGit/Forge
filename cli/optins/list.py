# pyright: strict
"""Commande ``forge opt-in:list`` — OPTINS-CLI-LIST-001 (renommée OPTIN-CLI-REMOVE-LEGACY-001).

Affiche l'**état local** des opt-ins connus dans un projet Forge.
Commande **strictement lecture seule** : elle ne crée, ne modifie et
n'installe rien. Elle se contente d'inspecter le **texte** de quelques
fichiers du projet (``optins/`` et ``mvc/routes/__init__.py``).

Contrat strict (chantier opt-ins) :

- **aucune écriture** (ni ``optins/``, ni ``registry.py``, ni
  ``mvc/routes/__init__.py``) ;
- **aucun import** de paquet opt-in (``forge_mvc_*``) ; seul le catalogue
  statique ``cli.optins.catalog`` est lu ;
- **pas de discovery magique** : seuls les opt-ins de type ``route``
  (``iot``, ``video``, ``audio``) reçoivent une couche ``optins/<name>/`` ;
  leur état projet est analysé par lecture de fichiers connus ;
- **pas de scan global** des paquets Python installés.

États distingués pour chaque opt-in ``route`` :

- ``absent``  : ``optins/<name>/`` absent ;
- ``partiel`` : ``optins/<name>/`` présent mais ``register_optins(router)``
  absent de ``mvc/routes/__init__.py`` ;
- ``activé``  : ``optins/<name>/`` présent **et** ``register_optins(router)``
  présent dans ``mvc/routes/__init__.py``.

Les opt-ins ``library`` et ``crosscutting`` n'ont pas de couche projet :
ils sont listés avec leur kind (sans état projet).
"""

from __future__ import annotations

from pathlib import Path

from cli.optins.catalog import (
    CATEGORY_DATABASE,
    CATEGORY_LABELS,
    DB_BACKENDS,
    KIND_CLI,
    KIND_CROSSCUTTING,
    KIND_LIBRARY,
    KIND_ROUTE,
    OFFICIAL_OPTINS,
    optins_by_category,
)
from cli.optins.registry_format import read_backend, read_enabled_optins

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
    appel dans ``mvc/routes/__init__.py``) ; la distinction par opt-in porte sur la
    présence de ``optins/<name>/``.
    """
    routes_py = project_root / "optins" / name / "routes.py"
    registry_py = project_root / "optins" / "registry.py"
    mvc_routes = project_root / "mvc" / "routes" / "__init__.py"

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
            "dans mvc/routes/__init__.py"
        )
    else:
        print(
            "            routes    : register_optins(router) absent "
            "de mvc/routes/__init__.py"
        )
        print(f"            conseil   : forge opt-in:enable {name} --apply")


_KIND_LABELS = {
    KIND_LIBRARY: "bibliothèque",
    KIND_CROSSCUTTING: "transversal",
    KIND_CLI: "outil CLI",
}


def _read_registry(project_root: Path) -> tuple[dict[str, str], str | None]:
    """Lit `ENABLED_OPTINS` et `BACKEND` du registre du projet (texte, sans import).

    Registre absent ou illisible : projet sans opt-in inscrit (dict vide, None).
    """
    registry_py = project_root / "optins" / "registry.py"
    if not registry_py.exists():
        return {}, None
    try:
        text = registry_py.read_text(encoding="utf-8", errors="replace")
        return read_enabled_optins(text), read_backend(text)
    except (OSError, SyntaxError, ValueError):
        return {}, None


def _print_kind_optin(name: str, kind: str, *, registered: bool) -> None:
    """Ligne d'un opt-in non-routier (bibliothèque / transversal / CLI).

    ADR-061 : l'état est lu dans `optins/registry.py` (inscrit / absent).
    """
    label = _KIND_LABELS.get(kind, kind)
    state = "inscrit" if registered else STATE_ABSENT
    print(f"  {name:<13} {label:<12} {state}")
    if not registered:
        print(f"            conseil   : forge opt-in:enable {name} --apply")


def _print_db_backends(active: str | None) -> None:
    """Section dédiée aux backends BDD (famille exclusive, ADR-054/055).

    Lecture seule, aucun import de paquet : catalogue statique + `BACKEND` du
    registre (ADR-060/061) pour marquer le backend choisi.
    """
    print(CATEGORY_LABELS[CATEGORY_DATABASE])
    print("            un seul backend par projet ; piloté par forge db:*")
    for backend in DB_BACKENDS:
        marker = "  <- choisi (registry)" if backend.name == active else ""
        print(f"  {backend.name:<13} backend{marker}")


def list_optins(*, project_root: Path) -> int:
    """Affiche l'état des opt-ins connus, groupés par destination (ADR-055).

    Toujours ``0`` (lecture seule). Les opt-ins de kind ``route`` reçoivent en
    plus leur état projet (couche ``optins/<name>/``).
    """
    enabled, backend = _read_registry(project_root)
    print("Forge opt-ins")
    print("")
    for category, opts in optins_by_category().items():
        print(CATEGORY_LABELS[category])
        for opt in opts:
            if opt.kind == KIND_ROUTE:
                _print_route_optin(opt.name, detect_optin_state(project_root, opt.name))
            else:
                _print_kind_optin(opt.name, opt.kind, registered=opt.name in enabled)
        print("")
    _print_db_backends(backend)
    print("")
    print("Aucune modification effectuée.")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge opt-in:list``.

    Aucune option pour ce ticket (``--help`` est intercepté en amont par
    le dispatcher central). Lecture seule.
    """
    return list_optins(project_root=Path.cwd())
