# pyright: strict
"""Import différé par une file de tâches (IMPEXP-ASYNC-JOBS-001).

Importer un fichier pendant une requête HTTP la fait attendre autant qu'il y a
de lignes. Dix mille lignes, dix mille insertions, et le navigateur abandonne
avant la fin : l'utilisateur relance, l'import repart de zéro, et parfois
double les lignes déjà écrites.

## Pourquoi la charge utile ne porte pas le travail

Le moteur prend des `FieldSpec` avec leurs fonctions de conversion, et une
fonction d'insertion. Rien de tout cela ne se sérialise en JSON, contrairement
à un message d'email.

La tâche transporte donc un **nom d'importeur** et un **chemin de fichier**.
L'application enregistre ses importeurs au démarrage, des deux côtés, et la
file ne voit que des chaînes.

## Les lignes invalides ne sont pas une panne

Un CSV mal rempli n'est pas une erreur technique : réessayer ne le corrigera
pas, et faire échouer la tâche la ferait rejouer jusqu'à épuisement de ses
tentatives. Le gestionnaire ne lève que sur ce qu'un réessai peut résoudre, ou
sur ce qui relève d'une configuration à corriger.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from forge_mvc_import_export.engine import FieldSpec, ImportReport, import_rows
from forge_mvc_import_export.errors import CsvImportError

__all__ = [
    "IMPORT_JOB_TASK",
    "ImporterNotFound",
    "ImportSourceError",
    "RegisteredImporter",
    "register_importer",
    "clear_importers",
    "registered_importers",
    "import_payload",
    "make_import_job_handler",
]

#: Nom de tâche du motif officiel.
IMPORT_JOB_TASK = "import.csv"


class ImporterNotFound(CsvImportError):
    """Aucun importeur de ce nom n'est enregistré côté ouvrier."""


class ImportSourceError(CsvImportError):
    """Le fichier à importer est introuvable, illisible, ou hors de la racine."""


@dataclass(frozen=True)
class RegisteredImporter:
    """Un importeur nommé, tel que l'application le déclare.

    `on_report` reçoit le rapport après l'import. Sans lui, un import différé
    serait muet : l'utilisateur qui a déposé le fichier n'apprendrait jamais
    combien de lignes sont passées, ni lesquelles ont été refusées.
    """

    name: str
    specs: "Sequence[FieldSpec]"
    insert: "Callable[[dict[str, Any]], Any]"
    partial: bool = False
    delimiter: str = ","
    on_report: "Callable[[ImportReport, dict[str, Any]], None] | None" = None


_importers: dict[str, RegisteredImporter] = {}


def register_importer(
    name: str,
    *,
    specs: "Sequence[FieldSpec]",
    insert: "Callable[[dict[str, Any]], Any]",
    partial: bool = False,
    delimiter: str = ",",
    on_report: "Callable[[ImportReport, dict[str, Any]], None] | None" = None,
) -> RegisteredImporter:
    """Enregistre un importeur sous un nom, et le rend.

    Le même nom doit être enregistré des **deux** côtés, celui qui met en file
    et celui qui traite : la tâche ne transporte que ce nom.

    Raises:
        CsvImportError: nom vide, ou déjà pris par un autre importeur. Écraser
            en silence ferait traiter un fichier par le mauvais importeur, et
            écrire dans la mauvaise table.
    """
    nom = (name or "").strip()
    if not nom:
        raise CsvImportError("Le nom d'importeur ne peut pas être vide.")
    if nom in _importers:
        raise CsvImportError(
            f"Importeur déjà enregistré : {nom!r}. Retirez le premier avec "
            "clear_importers() si le remplacement est voulu."
        )
    importeur = RegisteredImporter(
        name=nom, specs=specs, insert=insert,
        partial=partial, delimiter=delimiter, on_report=on_report,
    )
    _importers[nom] = importeur
    return importeur


def clear_importers() -> None:
    """Retire tous les importeurs. Sert aux tests et au réamorçage."""
    _importers.clear()


def registered_importers() -> "tuple[str, ...]":
    """Noms enregistrés, triés."""
    return tuple(sorted(_importers))


def import_payload(
    importer_name: str,
    path: "str | Path",
    **context: Any,
) -> "dict[str, Any]":
    """Charge utile à mettre en file, prête pour `enqueue`.

    `context` est libre et suit la tâche jusqu'au rapport : l'identifiant de
    celui qui a déposé le fichier, par exemple, sans quoi le rapport ne saurait
    à qui répondre.
    """
    nom = (importer_name or "").strip()
    if not nom:
        raise CsvImportError("Le nom d'importeur ne peut pas être vide.")
    chemin = str(path).strip()
    if not chemin:
        raise CsvImportError("Le chemin du fichier ne peut pas être vide.")
    return {"importer": nom, "path": chemin, "context": dict(context)}


def _resoudre_source(chemin: str, racine: "Path | None") -> Path:
    """Chemin du fichier, refusé s'il sort de la racine autorisée.

    Le chemin vient d'une charge utile, donc d'une file que plusieurs processus
    écrivent. Sans racine, un `../../etc/passwd` serait lu et importé ligne à
    ligne dans la base.
    """
    source = Path(chemin)
    if racine is not None:
        base = racine.resolve()
        resolu = (base / source).resolve() if not source.is_absolute() else source.resolve()
        if not resolu.is_relative_to(base):
            raise ImportSourceError(
                f"chemin hors de la racine autorisée : {chemin!r}."
            )
        source = resolu
    if not source.is_file():
        raise ImportSourceError(f"fichier introuvable : {source}.")
    return source


def make_import_job_handler(
    *,
    root: "str | Path | None" = None,
) -> "Callable[[dict[str, Any]], None]":
    """Rend le gestionnaire de tâche à enregistrer auprès de la file.

    `root` borne les chemins acceptés. Le laisser à `None` accepte n'importe
    quel chemin, ce qui ne convient qu'à un dépôt de fichiers dont l'application
    maîtrise entièrement l'origine.

    Le gestionnaire **lève** quand l'importeur est inconnu ou le fichier
    illisible : ce sont des erreurs de configuration ou de dépôt, qu'un réessai
    peut résoudre ou qu'un exploitant doit voir. Il ne lève **pas** pour des
    lignes invalides, qu'un réessai ne corrigerait jamais.
    """
    racine = None if root is None else Path(root)

    def handler(payload: "dict[str, Any]") -> None:
        nom = str(payload.get("importer", "")).strip()
        importeur = _importers.get(nom)
        if importeur is None:
            raise ImporterNotFound(
                f"importeur inconnu : {nom!r}. Enregistrés : "
                f"{', '.join(registered_importers()) or 'aucun'}."
            )

        source = _resoudre_source(str(payload.get("path", "")), racine)
        try:
            contenu = source.read_text(encoding="utf-8")
        except OSError as exc:
            raise ImportSourceError(f"lecture impossible de {source} : {exc}") from exc

        from forge_mvc_import_export.csv_reader import parse_csv

        lignes = parse_csv(contenu, delimiter=importeur.delimiter)
        rapport = import_rows(
            lignes,
            importeur.specs,
            cast("Callable[[dict[str, object]], object]", importeur.insert),
            partial=importeur.partial,
        )
        if importeur.on_report is not None:
            brut = payload.get("context")
            contexte: dict[str, Any] = (
                dict(cast("dict[str, Any]", brut)) if isinstance(brut, dict) else {}
            )
            importeur.on_report(rapport, contexte)

    return handler
