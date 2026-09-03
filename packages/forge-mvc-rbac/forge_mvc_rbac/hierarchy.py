# pyright: strict
"""Héritage entre rôles (`RBAC-ROLE-HIERARCHY-001`, ADR-095).

Le contrat associait un rôle à une liste plate de permissions. Un projet qui a
`lecteur`, `editeur` et `admin`, chacun reprenant les droits du précédent,
recopiait donc la liste du lecteur dans l'éditeur, puis les deux dans l'admin.

Trois copies de la même règle, qui divergent au premier ajout : on ajoute une
permission à l'éditeur, on oublie l'admin, et l'administrateur se retrouve avec
**moins** de droits qu'un éditeur. Le défaut est silencieux, personne ne teste
qu'un administrateur peut faire ce qu'un éditeur peut faire.

## L'héritage est déclaré, jamais deviné

    "role_inherits": {"admin": ["editeur"], "editeur": ["lecteur"]}

Forge ne déduit aucune hiérarchie d'un nom de rôle. « admin » ne domine pas
« editeur » parce qu'il s'appelle ainsi, et supposer le contraire donnerait des
droits que personne n'a écrits.

## Deux refus, et pourquoi ils ne sont pas négociables

**Un cycle est refusé.** `admin` héritant d'`editeur` héritant d'`admin` ne
décrit aucun ordre, et la résolution ne pourrait que boucler ou s'arrêter
arbitrairement. Un arrêt arbitraire donnerait des permissions différentes selon
l'ordre de lecture du JSON.

**Un rôle hérité inconnu est refusé.** `"admin": ["editur"]`, faute de frappe,
n'accorderait rien du tout : l'administrateur perdrait ses droits en silence, et
la cause serait introuvable dans un fichier de cinquante lignes.
"""
from __future__ import annotations

from typing import Any, cast

__all__ = [
    "RoleHierarchyError",
    "MAX_INHERITANCE_DEPTH",
    "inheritance_map",
    "detect_cycle",
    "expand_roles",
    "validate_hierarchy",
]

#: Profondeur au delà de laquelle la hiérarchie cesse d'être lisible. Un
#: héritage de plus de dix niveaux n'est plus un modèle de droits, c'est un
#: enchevêtrement que personne ne peut relire.
MAX_INHERITANCE_DEPTH = 10


class RoleHierarchyError(ValueError):
    """Hiérarchie de rôles inexploitable."""


def inheritance_map(data: "dict[str, Any] | None") -> "dict[str, tuple[str, ...]]":
    """Table `rôle -> rôles hérités`, telle que le contrat la déclare.

    Rend une table vide quand `role_inherits` est absent : un contrat sans
    héritage se comporte exactement comme avant ce ticket.
    """
    if not data:
        return {}
    brut = data.get("role_inherits")
    if not isinstance(brut, dict):
        return {}
    table: dict[str, tuple[str, ...]] = {}
    declaration = cast("dict[str, Any]", brut)
    for role, parents in declaration.items():
        if not isinstance(parents, list):
            continue
        noms = tuple(
            str(p).strip()
            for p in cast("list[Any]", parents)
            if isinstance(p, str) and p.strip()
        )
        if noms:
            table[str(role).strip()] = noms
    return table


def detect_cycle(table: "dict[str, tuple[str, ...]]") -> "tuple[str, ...] | None":
    """Rend le cycle trouvé, dans l'ordre, ou `None`.

    Le cycle est **rendu**, pas seulement signalé : « admin, editeur, admin »
    se corrige, « hiérarchie invalide » ne se corrige pas.
    """
    etat: dict[str, int] = {}
    chemin: list[str] = []

    def explorer(role: str) -> "tuple[str, ...] | None":
        if etat.get(role) == 1:
            depuis = chemin.index(role)
            return tuple(chemin[depuis:] + [role])
        if etat.get(role) == 2:
            return None
        etat[role] = 1
        chemin.append(role)
        for parent in table.get(role, ()):
            trouve = explorer(parent)
            if trouve is not None:
                return trouve
        chemin.pop()
        etat[role] = 2
        return None

    for role in sorted(table):
        cycle = explorer(role)
        if cycle is not None:
            return cycle
    return None


def validate_hierarchy(data: "dict[str, Any] | None") -> "list[str]":
    """Problèmes de la hiérarchie déclarée. Liste vide si elle est saine.

    Rend une liste plutôt que de lever : le contrat est validé en une passe, et
    un rapport complet vaut mieux qu'un premier problème suivi de l'inconnu.
    """
    table = inheritance_map(data)
    if not table:
        return []

    problemes: list[str] = []
    declares: set[str] = set()
    if data is not None:
        roles = data.get("roles")
        if isinstance(roles, dict):
            declares = {str(r) for r in cast("dict[str, Any]", roles)}

    for role, parents in sorted(table.items()):
        if declares and role not in declares:
            problemes.append(
                f"role_inherits déclare « {role} », absent de « roles »."
            )
        for parent in parents:
            if declares and parent not in declares:
                problemes.append(
                    f"« {role} » hérite de « {parent} », qui n'est pas déclaré "
                    "dans « roles ». Une faute de frappe n'accorderait rien du "
                    "tout, en silence."
                )
        if role in parents:
            problemes.append(f"« {role} » hérite de lui même.")

    cycle = detect_cycle(table)
    if cycle is not None:
        problemes.append(
            "cycle d'héritage : " + " puis ".join(cycle) + ". Aucun ordre ne "
            "satisfait cette déclaration, et s'arrêter arbitrairement donnerait "
            "des permissions différentes selon l'ordre de lecture du fichier."
        )
    return problemes


def expand_roles(
    roles: "list[str] | tuple[str, ...] | set[str] | frozenset[str]",
    table: "dict[str, tuple[str, ...]]",
) -> "frozenset[str]":
    """Rôles portés, héritages compris, transitivement.

    Raises:
        RoleHierarchyError: cycle, ou profondeur au delà de
            `MAX_INHERITANCE_DEPTH`. La résolution ne peut pas continuer sans
            l'un des deux, et rendre un résultat partiel donnerait des droits
            dépendant de l'ordre de lecture.
    """
    if not table:
        return frozenset(str(r) for r in roles)

    cycle = detect_cycle(table)
    if cycle is not None:
        raise RoleHierarchyError(
            "cycle d'héritage de rôles : " + " puis ".join(cycle)
        )

    resolus: set[str] = set()
    a_voir = [(str(r), 0) for r in roles]
    while a_voir:
        role, profondeur = a_voir.pop()
        if profondeur > MAX_INHERITANCE_DEPTH:
            raise RoleHierarchyError(
                f"héritage de rôles au delà de {MAX_INHERITANCE_DEPTH} niveaux, "
                f"depuis « {role} ». Une hiérarchie plus profonde n'est plus un "
                "modèle de droits mais un enchevêtrement que personne ne relit."
            )
        if role in resolus:
            continue
        resolus.add(role)
        a_voir.extend((parent, profondeur + 1) for parent in table.get(role, ()))
    return frozenset(resolus)
