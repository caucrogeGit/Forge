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

from core.security.csv_export import escape_csv_field
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

    Chaque cellule est rendue **inerte pour un tableur** par
    `core.security.csv_export.escape_csv_field` (IMPORT-EXPORT-CSV-ESCAPE-001).
    Sans cela, une cellule commençant par `=`, `+`, `-` ou `@` redevenait une
    formule vive à l'ouverture du fichier, et la donnée venait souvent d'un
    utilisateur. Le principe 7 demande de sécuriser par défaut, et le cœur
    portait déjà la primitive depuis `CRUD-CSV-ESCAPE-CORE-001`.

    Ce que cela change à la relecture : une telle cellule sort préfixée d'une
    apostrophe, ce qui se voit. Aucun caractère n'est retiré ni remplacé.
    """
    if not columns:
        raise CsvImportError("Aucune colonne à exporter (columns vide).")

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\n")
    writer.writerow([escape_csv_field(str(col)) for col in columns])
    for row in rows:
        writer.writerow([
            "" if row.get(col) is None else escape_csv_field(str(row.get(col)))
            for col in columns
        ])
    return buffer.getvalue()
