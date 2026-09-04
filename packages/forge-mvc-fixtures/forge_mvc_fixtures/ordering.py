# pyright: strict
"""Ordre de chargement des fixtures, et ce qu'il n'a pas pu déduire.

`FIXTURES-FK-ORDER-ROBUST-001`. Le tri topologique existait
(`order_fixture_files`), et il se rabattait **en silence** sur l'ordre
alphabétique dans trois cas : `relations.json` absent, cycle dans le graphe, ou
table inconnue.

Le repli lui même est raisonnable, le préfixe numérique `01_` restant un ordre
déclaratif de secours. Ce qui ne l'est pas est le silence : le chargement
échouait alors sur une violation de clé étrangère, et rien ne reliait cette
erreur à l'ordre qui l'avait causée. L'exploitant cherchait dans ses données un
défaut qui était dans son graphe.

## Deux durcissements

**Un fichier peut écrire dans plusieurs tables.** L'ordre ne regardait que le
**premier** `INSERT INTO` de chaque fichier. Un fichier qui insère dans
`articles` puis `commentaires` était classé comme s'il ne touchait
qu'`articles`, et pouvait passer avant le fichier dont `commentaires` dépend.
Toutes les tables écrites sont maintenant lues, et le fichier est classé après
la plus tardive de leurs dépendances.

**Le diagnostic est rendu, pas jeté.** `plan_fixture_order` rend l'ordre **et**
la raison de chaque repli, que la commande affiche.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

__all__ = [
    "FixtureOrderPlan",
    "tables_written_by",
    "fk_dependencies",
    "topological_order",
    "plan_fixture_order",
]

#: Toutes les tables écrites par un fichier, pas seulement la première.
_INSERT_INTO = re.compile(
    r"\binsert\s+into\s+[`\"\[]?([A-Za-z_][A-Za-z0-9_]*)[`\"\]]?", re.IGNORECASE
)


@dataclass(frozen=True)
class FixtureOrderPlan:
    """Ordre retenu, et ce qui a empêché de le déduire.

    `warnings` est vide quand le graphe a suffi. Chaque entrée dit ce qui
    manque et ce que l'exploitant doit regarder : une violation de clé
    étrangère au chargement se relie alors à sa cause.
    """

    files: "tuple[Path, ...]"
    used_graph: bool
    warnings: "tuple[str, ...]" = ()
    self_referencing: "tuple[str, ...]" = field(default=())

    @property
    def ok(self) -> bool:
        return self.used_graph and not self.warnings


def tables_written_by(path: Path) -> "tuple[str, ...]":
    """Tables visées par les `INSERT INTO` d'un fichier, dans l'ordre d'apparition.

    Le nom de fichier sert de repli quand aucun `INSERT` n'est trouvé, ce qui
    couvre les fichiers de fixtures nommés d'après leur table.

    Les noms sont rendus en minuscules : `Articles` et `articles` désignent la
    même table sur les quatre backends, et les distinguer casserait le
    rapprochement avec `relations.json`.
    """
    try:
        texte = path.read_text(encoding="utf-8")
    except OSError:
        return ()
    trouvees: list[str] = []
    for correspondance in _INSERT_INTO.finditer(texte):
        table = correspondance.group(1).lower()
        if table not in trouvees:
            trouvees.append(table)
    if trouvees:
        return tuple(trouvees)
    return (path.stem.lower(),)


def fk_dependencies(root: Path) -> "tuple[dict[str, set[str]] | None, tuple[str, ...], tuple[str, ...]]":
    """Graphe des dépendances `many_to_one`, les avertissements, les auto-références.

    Rend `None` pour le graphe quand `relations.json` est absent ou illisible,
    en disant **lequel des deux** : un fichier absent est une situation normale
    dans un projet sans relation, un fichier illisible est un défaut à corriger.
    """
    chemin = root / "mvc" / "entities" / "relations.json"
    if not chemin.is_file():
        return (
            None,
            (
                "relations.json est absent : l'ordre des fixtures suit les noms "
                "de fichiers. Préfixez les d'un numéro si une clé étrangère "
                "impose un ordre.",
            ),
            (),
        )
    try:
        donnees: object = json.loads(chemin.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return (
            None,
            (
                f"relations.json est illisible ({exc}) : l'ordre des fixtures "
                "suit les noms de fichiers. Corrigez le fichier, l'ordre déduit "
                "des clés étrangères ne peut pas être calculé sans lui.",
            ),
            (),
        )
    if not isinstance(donnees, dict):
        return (None, ("relations.json ne contient pas un objet JSON.",), ())

    # `json.loads` rend `Any` : on nomme le type une fois, plutôt que d'empiler
    # des `pyright: ignore` à chaque accès. Trois d'entre eux masquaient une
    # erreur que la configuration ne voyait pas, ce paquet ayant été oublié de
    # la liste vérifiée (`PKG-PYRIGHT-FIXTURES-001`).
    contenu = cast("dict[str, Any]", donnees)
    relations = contenu.get("relations")
    if not isinstance(relations, list):
        return (None, ("relations.json ne déclare aucune liste « relations ».",), ())

    deps: dict[str, set[str]] = {}
    auto: list[str] = []
    for brut in cast("list[Any]", relations):
        if not isinstance(brut, dict):
            continue
        relation = cast("dict[str, Any]", brut)
        if relation.get("type") != "many_to_one":
            continue
        source = relation.get("from")
        cible = relation.get("to")
        if not isinstance(source, str) or not isinstance(cible, str):
            continue
        if source == cible:
            # Une table qui se référence elle même ne peut pas être ordonnée
            # par un tri de fichiers : l'ordre doit être respecté LIGNE À LIGNE
            # dans le fichier, ce qu'aucun classement de fichiers ne peut faire.
            if source not in auto:
                auto.append(source)
            deps.setdefault(source, set())
            continue
        deps.setdefault(source, set()).add(cible)
        deps.setdefault(cible, set())
    return (deps, (), tuple(auto))


def topological_order(deps: "dict[str, set[str]]") -> "tuple[list[str] | None, tuple[str, ...]]":
    """Ordre topologique, et le cycle qui l'a empêché.

    Le cycle est **nommé** : « cycle entre Article, Auteur » se corrige, « ordre
    non déduit » ne se corrige pas.
    """
    restantes = {noeud: set(aretes) for noeud, aretes in deps.items()}
    ordonnees: list[str] = []
    while restantes:
        pretes = sorted(noeud for noeud, aretes in restantes.items() if not aretes)
        if not pretes:
            impliquees = ", ".join(sorted(restantes))
            return (
                None,
                (
                    f"cycle de clés étrangères entre {impliquees} : aucun ordre "
                    "ne satisfait toutes les dépendances. L'ordre suit les noms "
                    "de fichiers, préfixez les d'un numéro pour trancher.",
                ),
            )
        for noeud in pretes:
            ordonnees.append(noeud)
            del restantes[noeud]
        for aretes in restantes.values():
            aretes.difference_update(pretes)
    return (ordonnees, ())


def plan_fixture_order(
    root: Path,
    files: "list[Path]",
    entity_tables: "dict[str, str]",
) -> FixtureOrderPlan:
    """Ordre de chargement, et le diagnostic de ce qui n'a pas pu être déduit.

    `entity_tables` associe le nom d'entité à sa table, tel que le projet le
    déclare. Il sert à rapprocher un fichier de fixtures, qui nomme des tables,
    et le graphe, qui nomme des entités.

    Un fichier écrivant dans plusieurs tables est classé après **toutes** les
    dépendances de toutes ses tables : le classer sur la première seule le
    faisait passer avant un fichier dont sa seconde table dépendait.
    """
    par_nom = sorted(files, key=lambda chemin: chemin.name)
    deps, avertissements, auto = fk_dependencies(root)
    if deps is None:
        return FixtureOrderPlan(tuple(par_nom), False, avertissements, auto)

    topo, cycle = topological_order(deps)
    if topo is None:
        return FixtureOrderPlan(tuple(par_nom), False, cycle, auto)

    rang = {entite: index for index, entite in enumerate(topo)}
    table_vers_entite = {
        table.lower(): entite for entite, table in entity_tables.items()
    }
    rang_inconnu = len(topo)

    inconnues: list[str] = []

    def cle(chemin: Path) -> "tuple[int, str]":
        rangs: list[int] = []
        for table in tables_written_by(chemin):
            entite = table_vers_entite.get(table)
            if entite is None:
                if table not in inconnues:
                    inconnues.append(table)
                rangs.append(rang_inconnu)
            else:
                rangs.append(rang.get(entite, rang_inconnu))
        # Le rang le plus TARDIF gouverne : le fichier doit venir après tout ce
        # dont chacune de ses tables dépend.
        return (max(rangs) if rangs else rang_inconnu, chemin.name)

    ordonnes = sorted(par_nom, key=cle)

    messages: list[str] = []
    if inconnues:
        messages.append(
            "table(s) sans entité déclarée, placée(s) en dernier : "
            f"{', '.join(sorted(inconnues))}. Si une autre table en dépend, "
            "préfixez les fichiers d'un numéro."
        )
    if auto:
        messages.append(
            "table(s) se référençant elle(s) même(s) : "
            f"{', '.join(sorted(auto))}. L'ordre des lignes DANS le fichier "
            "compte, aucun classement de fichiers ne peut le garantir."
        )

    return FixtureOrderPlan(tuple(ordonnes), True, tuple(messages), auto)
