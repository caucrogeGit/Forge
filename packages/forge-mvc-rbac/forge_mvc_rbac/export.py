# pyright: strict
"""Export du contrat RBAC (`RBAC-CONTRACT-EXPORT-001`).

`rbac:validate` dit si le contrat est valide, `rbac:audit` compare le contrat
et la base. Ni l'un ni l'autre ne rend le contrat **lisible** : « qui a le droit
de faire quoi dans cette application » demandait d'ouvrir `mvc/security/rbac.json`
et de le lire à l'œil, ce qui se fait mal dès la dizaine de rôles.

C'est pourtant la question que pose une revue de sécurité, un audit, ou
simplement un nouveau venu dans l'équipe.

## Deux sorties, deux usages

Le **Markdown** est fait pour être lu et versionné à côté du code : une
différence dans un journal de modifications montre alors qu'un rôle a gagné une
permission, ce qu'un diff de JSON montre mal.

Le **CSV** est fait pour un tableur, où une revue se mène ligne à ligne.

## Ce que l'export ne fait pas

Il ne lit **pas** la base. Il rend le contrat, c'est à dire ce qui est déclaré,
et non ce qui est provisionné. `rbac:audit` compare déjà les deux, et confondre
les deux sorties ferait prendre une intention pour un état.
"""
from __future__ import annotations

from typing import Any, cast

__all__ = [
    "RbacExportError",
    "MARKDOWN_COLUMNS",
    "CSV_COLUMNS",
    "contract_rows",
    "to_markdown",
    "to_csv",
]

#: Colonnes du tableau, dans l'ordre.
MARKDOWN_COLUMNS = ("Rôle", "Entité", "Actions")
CSV_COLUMNS = ("role", "entite", "action")


class RbacExportError(ValueError):
    """Contrat inexploitable."""


def contract_rows(data: "dict[str, Any] | None") -> "list[tuple[str, str, str]]":
    """Triplets `(rôle, entité, action)`, triés.

    Un triplet par action et non par entité : c'est la granularité d'une revue,
    qui se demande « ce rôle peut il supprimer », pas « ce rôle touche il à
    cette entité ».

    Le tri rend deux exports comparables. Sans lui, l'ordre suivrait celui du
    JSON, et un simple réarrangement du fichier ferait apparaître une
    différence là où rien n'a changé.
    """
    if not data:
        return []
    roles = data.get("roles")
    if not isinstance(roles, dict):
        raise RbacExportError(
            "le contrat ne déclare pas d'objet « roles » : il n'y a rien à exporter."
        )

    lignes: list[tuple[str, str, str]] = []
    par_role = cast("dict[str, Any]", roles)
    for role, contenu in sorted(par_role.items()):
        nom_role = str(role)
        if not isinstance(contenu, dict):
            continue
        par_entite = cast("dict[str, Any]", contenu)
        for entite, actions in sorted(par_entite.items()):
            nom_entite = str(entite)
            if isinstance(actions, list):
                liste = cast("list[Any]", actions)
                for action in sorted(str(a) for a in liste):
                    lignes.append((nom_role, nom_entite, action))
            elif isinstance(actions, bool) and actions:
                # Forme abrégée : toutes les actions de l'entité.
                lignes.append((nom_role, nom_entite, "*"))
            elif isinstance(actions, str):
                lignes.append((nom_role, nom_entite, actions))
    return lignes


def to_markdown(data: "dict[str, Any] | None", *, title: str = "Contrat RBAC") -> str:
    """Contrat rendu en tableau Markdown, une ligne par rôle et par entité.

    Les actions d'un même couple sont réunies sur une ligne : un tableau d'une
    ligne par action serait exact et illisible, et c'est la lisibilité qui est
    la raison d'être de cette sortie.
    """
    lignes = contract_rows(data)
    sortie = [f"# {title}", ""]
    if not lignes:
        sortie.append("Aucun rôle déclaré.")
        return "\n".join(sortie) + "\n"

    groupes: dict[tuple[str, str], list[str]] = {}
    for role, entite, action in lignes:
        groupes.setdefault((role, entite), []).append(action)

    sortie.append("| " + " | ".join(MARKDOWN_COLUMNS) + " |")
    sortie.append("|" + "---|" * len(MARKDOWN_COLUMNS))
    for (role, entite), actions in sorted(groupes.items()):
        sortie.append(f"| `{role}` | `{entite}` | {', '.join(actions)} |")

    roles = len({role for role, _, _ in lignes})
    sortie += [
        "",
        f"{roles} rôle(s), {len(groupes)} couple(s) rôle/entité, "
        f"{len(lignes)} permission(s).",
        "",
        "Ce tableau rend le **contrat**, c'est à dire ce qui est déclaré.",
        "Pour comparer au contenu réel de la base, voir `forge rbac:audit`.",
    ]
    return "\n".join(sortie) + "\n"


def to_csv(data: "dict[str, Any] | None", *, delimiter: str = ",") -> str:
    """Contrat rendu en CSV, un triplet par ligne.

    Chaque cellule passe par l'échappement de `forge-mvc-import-export` quand
    il est installé, et par celui du cœur sinon : un nom de rôle commençant par
    `=` redeviendrait une formule vive à l'ouverture du fichier.
    """
    import csv
    import io

    from core.security.csv_export import escape_csv_field

    tampon = io.StringIO()
    writer = csv.writer(tampon, delimiter=delimiter, lineterminator="\n")
    writer.writerow([escape_csv_field(col) for col in CSV_COLUMNS])
    for role, entite, action in contract_rows(data):
        writer.writerow([
            escape_csv_field(role), escape_csv_field(entite), escape_csv_field(action)
        ])
    return tampon.getvalue()
