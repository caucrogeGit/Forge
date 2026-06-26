# pyright: strict
"""Écriture programmatique de lignes en CSV, sans logique métier.

`to_csv` est l'inverse de :func:`parse_csv` : il prend des lignes (des
dictionnaires) et une liste de colonnes, et renvoie le texte CSV correspondant.

Frontière (principe 11) : pour télécharger une **entité** depuis une page web,
la route d'export générée par le CRUD du cœur reste la voie officielle. `to_csv`
sert l'export **programmatique** : un script, un rapport, une agrégation, ou des
données qui ne viennent pas d'une entité CRUD.
"""
from __future__ import annotations

import csv
import io
from collections.abc import Mapping, Sequence

from forge_mvc_import_export.errors import CsvImportError


def to_csv(
    rows: Sequence[Mapping[str, object]],
    columns: Sequence[str],
    *,
    delimiter: str = ",",
) -> str:
    """Rend `rows` en texte CSV, colonnes dans l'ordre de `columns`.

    La première ligne est l'en-tête (`columns`). Pour chaque ligne, les valeurs
    sont prises dans l'ordre des colonnes ; une valeur absente ou `None` devient
    une chaîne vide, les autres sont converties par `str`. Lève
    :class:`CsvImportError` si `columns` est vide.
    """
    if not columns:
        raise CsvImportError("Aucune colonne à exporter (columns vide).")

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\n")
    writer.writerow(list(columns))
    for row in rows:
        writer.writerow(["" if row.get(col) is None else str(row.get(col)) for col in columns])
    return buffer.getvalue()
