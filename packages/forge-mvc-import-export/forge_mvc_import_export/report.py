# pyright: strict
"""Rapport d'erreurs d'import, téléchargeable (`IMPEXP-ERROR-REPORT-001`).

`ImportReport` portait une liste d'erreurs exploitable en Python et inutilisable
par la personne qui a déposé le fichier. Un import de deux mille lignes avec
quarante erreurs ne pouvait se corriger qu'en lisant un écran, une erreur à la
fois, sans jamais voir la ligne fautive.

Ce module rend le rapport en CSV : la personne l'ouvre à côté de son fichier,
corrige, et relance.

## Ce que le rapport contient, et pourquoi

La ligne, la colonne et le message ne suffisent pas. « Ligne 1847, colonne
`montant`, valeur invalide » oblige à retrouver la ligne 1847 à la main dans un
tableur, et la numérotation du rapport et celle du tableur diffèrent d'une unité
à cause de l'en-tête.

Le rapport porte donc aussi la **valeur refusée** et, si l'appelant fournit les
lignes, un extrait de la ligne d'origine.

## Le rapport est lui même échappé

Il contient des données venues du fichier déposé, donc d'un utilisateur. Sans
échappement, une cellule commençant par `=` redeviendrait une formule vive à
l'ouverture du rapport, et le rapport d'erreurs deviendrait le vecteur.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from forge_mvc_import_export.csv_writer import to_csv
from forge_mvc_import_export.engine import ImportReport, RowError

__all__ = [
    "REPORT_COLUMNS",
    "SPREADSHEET_ROW_OFFSET",
    "errors_to_rows",
    "errors_to_csv",
    "report_filename",
]

#: Colonnes du rapport, dans l'ordre.
REPORT_COLUMNS = ("ligne", "ligne_tableur", "colonne", "probleme", "valeur_refusee")

#: Décalage entre l'index de données et le numéro affiché par un tableur.
#: La ligne 1 des données est la ligne 2 du fichier, l'en-tête occupant la
#: première. Ne pas le dire fait chercher au mauvais endroit.
SPREADSHEET_ROW_OFFSET = 1

#: Au delà, la valeur refusée est tronquée dans le rapport : une cellule de
#: plusieurs kilooctets rend le rapport illisible sans rien apprendre de plus.
MAX_VALUE_LENGTH = 200


def _valeur_refusee(
    erreur: RowError, rows: "Sequence[Mapping[str, str]] | None"
) -> str:
    """Valeur d'origine ayant causé l'erreur, quand elle est retrouvable.

    Une erreur d'en-tête (`row` à zéro) n'en a pas, et une erreur d'insertion
    ne porte pas de colonne : les deux rendent une chaîne vide plutôt qu'une
    valeur approchée qui ferait chercher au mauvais endroit.
    """
    if rows is None or erreur.field is None or erreur.row < 1:
        return ""
    index = erreur.row - 1
    if index >= len(rows):
        return ""
    valeur = str(rows[index].get(erreur.field, ""))
    if len(valeur) > MAX_VALUE_LENGTH:
        return valeur[:MAX_VALUE_LENGTH] + "…"
    return valeur


def errors_to_rows(
    report: ImportReport, rows: "Sequence[Mapping[str, str]] | None" = None
) -> "list[dict[str, object]]":
    """Erreurs du rapport, en lignes prêtes pour un CSV ou un gabarit.

    `rows` sont les lignes lues du fichier. Les fournir ajoute la valeur
    refusée, ce qui évite d'avoir à rouvrir le fichier pour comprendre.
    """
    lignes: list[dict[str, object]] = []
    for erreur in report.errors:
        lignes.append({
            "ligne": erreur.row,
            "ligne_tableur": (
                erreur.row + SPREADSHEET_ROW_OFFSET if erreur.row >= 1 else ""
            ),
            "colonne": erreur.field or "",
            "probleme": erreur.message,
            "valeur_refusee": _valeur_refusee(erreur, rows),
        })
    return lignes


def errors_to_csv(
    report: ImportReport,
    rows: "Sequence[Mapping[str, str]] | None" = None,
    *,
    delimiter: str = ",",
) -> str:
    """Rapport d'erreurs en CSV, prêt à être servi en téléchargement.

    Chaque cellule passe par l'échappement de `to_csv` : le rapport contient
    des données venues du fichier déposé, et une cellule commençant par `=`
    redeviendrait une formule vive à son ouverture.

    Un rapport sans erreur rend l'en-tête seul, jamais une chaîne vide : un
    fichier vide se lit comme un téléchargement raté.
    """
    return to_csv(errors_to_rows(report, rows), REPORT_COLUMNS, delimiter=delimiter)


def report_filename(source_name: str = "import") -> str:
    """Nom de fichier proposé pour le rapport, dérivé du fichier déposé.

    Le nom d'origine vient de l'utilisateur : il est réduit à son dernier
    segment, débarrassé de son extension, et de tout ce qui n'est ni lettre,
    ni chiffre, ni tiret. Il voyage dans un en-tête `Content-Disposition`, où
    un saut de ligne couperait l'en-tête en deux.
    """
    base = (source_name or "import").replace("\\", "/").rsplit("/", 1)[-1]
    base = base.rsplit(".", 1)[0]
    propre = "".join(c if c.isalnum() or c in "-_" else "-" for c in base).strip("-")
    return f"{propre or 'import'}-erreurs.csv"
