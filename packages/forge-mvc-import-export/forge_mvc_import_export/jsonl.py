# pyright: strict
"""Format JSONL, un enregistrement par ligne (`IMPEXP-JSONL-001`).

Le CSV a deux limites que rien ne contourne : il ne porte aucun type, tout y
étant du texte, et il ne sait pas représenter une valeur imbriquée. Un import
de données à structure, ou un export destiné à un autre programme, y perd la
différence entre le nombre `1`, le texte `"1"` et le booléen `true`.

JSONL les résout sans renoncer au traitement ligne à ligne : un objet JSON par
ligne, lisible en flux, découpable par `split`, et concaténable sans parseur.

## Pourquoi JSONL et non JSON

Un tableau JSON impose de tout charger avant de lire le premier enregistrement,
et de tout garder en mémoire pour en écrire un de plus. Un fichier de cent mille
lignes devient alors un objet de cent mille éléments là où JSONL n'en demande
qu'un à la fois.

Une ligne fautive n'y empêche pas non plus de lire les autres, alors qu'une
virgule manquante rend un tableau JSON entièrement illisible.

## Ce que le module ne fait pas

Il ne **convertit pas** entre CSV et JSONL. Les deux formats se lisent en
lignes de dictionnaires, et l'appelant passe de l'un à l'autre en changeant la
fonction qu'il appelle : ajouter un convertisseur donnerait deux façons de
faire la même chose, ce que le principe 11 refuse.
"""
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from forge_mvc_import_export.errors import CsvImportError

__all__ = [
    "JsonlError",
    "JSONL_MIME_TYPE",
    "to_jsonl",
    "parse_jsonl",
]

#: Type servi pour un téléchargement JSONL.
JSONL_MIME_TYPE = "application/x-ndjson; charset=utf-8"


class JsonlError(CsvImportError):
    """Ligne JSONL illisible ou de forme inattendue.

    Descend de `CsvImportError` : une application qui traite déjà les erreurs
    d'import n'a pas à distinguer le format pour rendre un message.
    """


def to_jsonl(
    rows: "Sequence[Mapping[str, Any]]",
    columns: "Sequence[str] | None" = None,
) -> str:
    """Rend `rows` en JSONL, un objet par ligne.

    Sans `columns`, chaque ligne est écrite telle quelle. Avec, les clés sont
    restreintes et **ordonnées** comme demandé, ce qui rend deux exports
    successifs comparables : un ordre de clés variable ferait apparaître des
    différences là où les données sont identiques.

    Une clé absente d'une ligne est écrite à `null`, et non omise : un
    consommateur qui lit un flux a besoin que toutes les lignes aient la même
    forme.

    Les caractères non ASCII sont écrits tels quels, en UTF-8, plutôt
    qu'échappés en `\\uXXXX` : un fichier destiné à être relu par un humain
    reste lisible, et JSON impose l'UTF-8 depuis longtemps.
    """
    lignes: list[str] = []
    for row in rows:
        charge = (
            dict(row) if columns is None else {col: row.get(col) for col in columns}
        )
        lignes.append(json.dumps(charge, ensure_ascii=False, separators=(",", ":")))
    # Saut de ligne final : la spécification le veut, et un `cat` de deux
    # fichiers sans lui collerait le dernier enregistrement du premier au
    # premier du second.
    return "".join(f"{ligne}\n" for ligne in lignes)


def parse_jsonl(text: str, *, strict: bool = True) -> "list[dict[str, Any]]":
    """Lit un texte JSONL et rend une ligne par enregistrement.

    Les lignes vides sont ignorées, un fichier concaténé ou terminé par un saut
    en portant souvent.

    Args:
        strict: à vrai, une ligne illisible **lève** en nommant son numéro. À
            faux, elle est ignorée, ce qui n'a de sens que pour récupérer ce
            qui est lisible d'un fichier abîmé, et perd des données en silence.

    Raises:
        JsonlError: en mode strict, ligne illisible ou qui n'est pas un objet.
    """
    enregistrements: list[dict[str, Any]] = []
    for numero, brut in enumerate(text.splitlines(), start=1):
        ligne = brut.strip()
        if not ligne:
            continue
        try:
            valeur: object = json.loads(ligne)
        except json.JSONDecodeError as exc:
            if strict:
                raise JsonlError(
                    f"ligne {numero} illisible : {exc.msg}. "
                    "Le JSONL attend un objet JSON complet par ligne."
                ) from exc
            continue
        if not isinstance(valeur, dict):
            if strict:
                raise JsonlError(
                    f"ligne {numero} : attendu un objet JSON, reçu "
                    f"{type(valeur).__name__}. Un tableau ou une valeur seule "
                    "ne sont pas des enregistrements."
                )
            continue
        enregistrements.append(dict(valeur))  # pyright: ignore[reportUnknownArgumentType]
    return enregistrements
