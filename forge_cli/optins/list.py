"""Commande ``forge opt-in:list`` — OPTINS-CLI-LIST-001 (renommée OPTIN-CLI-REMOVE-LEGACY-001).

Affiche l'**état local** des opt-ins connus dans un projet Forge.
Commande **strictement lecture seule** : elle ne crée, ne modifie et
n'installe rien. Elle se contente d'inspecter le **texte** de quelques
fichiers du projet (``optins/`` et ``mvc/routes.py``).

Contrat strict (chantier opt-ins) :

- **aucune écriture** (ni ``optins/``, ni ``registry.py``, ni
  ``mvc/routes.py``) ;
- **aucun import** de ``forge_mvc_iot`` ni d'aucun paquet opt-in ;
- **pas de discovery magique** : seul ``iot`` (le seul opt-in supporté
  par le chantier actuel) est analysé, par lecture de fichiers connus ;
- **pas de scan global** des paquets Python installés.

États distingués pour ``iot`` :

- ``absent``  : ``optins/iot/`` absent ;
- ``partiel`` : ``optins/iot/`` présent mais ``register_optins(router)``
  absent de ``mvc/routes.py`` ;
- ``activé``  : ``optins/iot/`` présent **et** ``register_optins(router)``
  présent dans ``mvc/routes.py``.
"""

from __future__ import annotations

from pathlib import Path

__all__ = [
    "STATE_ABSENT",
    "STATE_PARTIAL",
    "STATE_ACTIVE",
    "KNOWN_OPTINS",
    "detect_iot_state",
    "list_optins",
    "main",
]

STATE_ABSENT = "absent"
STATE_PARTIAL = "partiel"
STATE_ACTIVE = "activé"

# Opt-ins que cette commande sait réellement analyser (chantier actuel).
KNOWN_OPTINS: tuple[str, ...] = ("iot",)

_ROUTES_CALL = "register_optins(router)"


def detect_iot_state(project_root: Path) -> dict[str, object]:
    """Inspecte (lecture seule) l'état de l'opt-in IoT dans le projet.

    Retourne un dict avec ``state`` et quelques indicateurs de présence,
    sans jamais importer ni écrire quoi que ce soit.
    """
    routes_py = project_root / "optins" / "iot" / "routes.py"
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


def _print_iot(info: dict[str, object]) -> None:
    state = info["state"]
    print(f"  iot       {state}")

    if state == STATE_ABSENT:
        print("            conseil   : forge opt-in:enable iot --apply")
        return

    print("            structure : optins/iot/")
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
        print("            conseil   : forge opt-in:enable iot --apply")


def list_optins(*, project_root: Path) -> int:
    """Affiche l'état des opt-ins connus. Toujours ``0`` (lecture seule)."""
    print("Forge opt-ins")
    print("")
    _print_iot(detect_iot_state(project_root))
    print("")
    print("Aucune modification effectuée.")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge opt-in:list``.

    Aucune option pour ce ticket (``--help`` est intercepté en amont par
    le dispatcher central). Lecture seule.
    """
    return list_optins(project_root=Path.cwd())
