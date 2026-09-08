# pyright: strict
"""Lecture de CSV en lignes de dictionnaires, sans logique métier.

`parse_csv` enveloppe le module standard `csv` : il lit un texte CSV et renvoie
une ligne par enregistrement, sous forme de dictionnaire en-tête -> valeur. La
validation et l'insertion ne sont pas ici (voir `engine.py`).
"""
from __future__ import annotations

import csv
import io

from forge_mvc_import_export.errors import CsvImportError


def parse_csv(text: str, *, delimiter: str = ",") -> list[dict[str, str]]:
    """Lit `text` (contenu CSV) et renvoie une liste de lignes en dictionnaire.

    La première ligne fournit les en-têtes (clés). Chaque ligne de données
    devient un `dict` en-tête -> valeur (les valeurs sont des chaînes). Lève
    :class:`CsvImportError` si le CSV n'a pas d'en-tête ou contient un en-tête
    vide ou dupliqué.
    """
    if not text.strip():
        raise CsvImportError("Le contenu CSV est vide.")

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)
    if not rows:
        raise CsvImportError("Le contenu CSV est vide.")

    header = [cell.strip() for cell in rows[0]]
    if any(not name for name in header):
        raise CsvImportError("L'en-tête CSV contient une colonne sans nom.")
    if len(set(header)) != len(header):
        raise CsvImportError("L'en-tête CSV contient des colonnes en double.")

    records: list[dict[str, str]] = []
    for numero, cells in enumerate(rows[1:], start=2):
        if not any(cell.strip() for cell in cells):
            continue  # ligne entièrement vide ignorée
        if len(cells) > len(header):
            # `IMPEXP-CSV-LIGNE-TROP-LONGUE-001` : les cellules au-delà de la
            # largeur de l'en-tête étaient **ignorées sans un mot**.
            # `nom,note` puis `Alice,12,5` rendait `{"nom": "Alice",
            # "note": "12"}`, et le `5` disparaissait.
            #
            # Les trois causes ordinaires donnent toutes ce symptôme : un
            # séparateur mal choisi, une virgule décimale non protégée, un
            # export mal formé. Aucune ne se voit à la lecture du rapport,
            # puisque l'import se déclare réussi.
            #
            # Un import qui perd des données doit s'arrêter, pas se taire. Le
            # message nomme la ligne, ce qui était attendu et ce qui a été lu :
            # sans le numéro, il faut chercher dans un fichier de milliers de
            # lignes ce que la machine savait déjà.
            raise CsvImportError(
                f"Ligne {numero} : {len(cells)} cellules pour {len(header)} "
                f"colonnes déclarées. Vérifiez le séparateur (« {delimiter} »), "
                "les guillemets autour des valeurs qui le contiennent, et les "
                "virgules décimales."
            )
        record = {header[i]: (cells[i] if i < len(cells) else "") for i in range(len(header))}
        records.append(record)
    return records
