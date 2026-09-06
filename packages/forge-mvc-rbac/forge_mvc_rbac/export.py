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

from forge_mvc_rbac.hierarchy import (
    RoleHierarchyError,
    expand_roles,
    inheritance_map,
)

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


#: Entité affichée pour une permission qu'aucune entité ne réclame.
SANS_ENTITE = "—"


def _actions_par_permission(data: "dict[str, Any]") -> "dict[str, list[tuple[str, str]]]":
    """Code de permission -> couples (entité, action) qui l'exigent.

    Le contrat déclare les rôles par **codes de permission**, et les entités
    par action. Joindre les deux est ce qui rend l'export lisible : « éditeur
    peut publier un Article » plutôt que « éditeur a article.publier ».
    """
    index: "dict[str, list[tuple[str, str]]]" = {}
    entites = data.get("entities")
    if not isinstance(entites, dict):
        return index
    for entite, bloc in cast("dict[str, Any]", entites).items():
        if not isinstance(bloc, dict):
            continue
        permissions = cast("dict[str, Any]", bloc).get("permissions")
        if not isinstance(permissions, dict):
            continue
        for action, code in cast("dict[str, Any]", permissions).items():
            if isinstance(code, str):
                index.setdefault(code, []).append((str(entite), str(action)))
    return index


def contract_rows(data: "dict[str, Any] | None") -> "list[tuple[str, str, str]]":
    """Triplets `(rôle, entité, action)`, triés.

    Un triplet par action et non par entité : c'est la granularité d'une revue,
    qui se demande « ce rôle peut il supprimer », pas « ce rôle touche il à
    cette entité ».

    Le tri rend deux exports comparables. Sans lui, l'ordre suivrait celui du
    JSON, et un simple réarrangement du fichier ferait apparaître une
    différence là où rien n'a changé.

    ## La forme lue est celle du schéma

    `RBAC-EXPORT-FORME-CONTRAT-001`. Cette fonction lisait `roles` comme une
    table `rôle -> entité -> actions`. Le schéma, qui fait autorité et que
    `rbac:audit` applique, déclare `rôle -> liste de codes de permission`. Les
    deux ne se rencontraient jamais : chaque rôle était écarté, et
    `forge rbac:export` rendait « Aucun rôle déclaré » sur **tout** contrat
    valide. Le test de l'export employait la forme que le schéma interdit, ce
    qui laissait la fonction verte et inerte.

    Les entités et leurs actions viennent donc du bloc `entities`, joint par
    code de permission.

    Une permission accordée à un rôle et réclamée par aucune entité est rendue
    quand même, sous l'entité « — » : la taire ferait disparaître d'une revue
    de sécurité un droit pourtant accordé.
    """
    if not data:
        return []
    roles = data.get("roles")
    if not isinstance(roles, dict):
        raise RbacExportError(
            "le contrat ne déclare pas d'objet « roles » : il n'y a rien à exporter."
        )

    # RBAC-ROLE-HIERARCHY-001 : l'export rend les permissions EFFECTIVES,
    # héritées comprises. Rendre les seules permissions directes ferait croire
    # à un administrateur privé de droits qu'il possède, et c'est exactement ce
    # qu'une revue de sécurité ne doit pas conclure.
    table = inheritance_map(data)
    index = _actions_par_permission(data)

    lignes: "list[tuple[str, str, str]]" = []
    par_role = cast("dict[str, Any]", roles)
    for role in sorted(par_role):
        nom_role = str(role)
        try:
            portes = sorted(expand_roles([nom_role], table))
        except RoleHierarchyError as exc:
            raise RbacExportError(
                f"hiérarchie de rôles inexploitable : {exc}"
            ) from exc

        couples: "set[tuple[str, str]]" = set()
        for herite in portes:
            codes = par_role.get(herite)
            if not isinstance(codes, list):
                continue
            for code in cast("list[Any]", codes):
                nom_code = str(code)
                cibles = index.get(nom_code)
                if cibles:
                    couples.update(cibles)
                else:
                    couples.add((SANS_ENTITE, nom_code))

        for entite, action in sorted(couples):
            lignes.append((nom_role, entite, action))
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
