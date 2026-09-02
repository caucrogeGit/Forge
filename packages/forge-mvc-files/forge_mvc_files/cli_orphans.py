# pyright: strict
"""Commande ``forge files:orphans`` (`FILES-ORPHAN-PURGE-001`).

Rapproche le dossier d'upload et le registre de l'ADR-094, et nomme les deux
sortes d'orphelins : le fichier que personne n'a inscrit, et l'inscription dont
le fichier a disparu.

## Pourquoi elle affiche avant d'effacer

Le motif est celui d'`audit:gc`, de `fixtures:purge` et de `db:init`
(charte §7, ADR-067), et il est ici plus impérieux qu'ailleurs : la commande
supprime des fichiers déposés par des utilisateurs, que rien ne restaure.

Un rapport qui surprend doit arrêter le geste, pas l'accompagner.
"""
from __future__ import annotations

from pathlib import Path

from forge_mvc_files.orphans import (
    DEFAULT_MIN_AGE_SECONDS,
    OrphanPurgeRefused,
    OrphanReport,
    find_orphans,
    purge_orphans,
)

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_ERROR = "[ERREUR]"

__all__ = [
    "STATUS_OK",
    "STATUS_INFO",
    "STATUS_ERROR",
    "parse_options",
    "render_report",
    "main",
]

#: Au delà, la liste est tronquée : un rapport de mille lignes ne se lit pas.
APERCU = 20


class _Options:
    """Options reconnues, ou le motif du refus de les lire."""

    def __init__(self) -> None:
        self.delete = False
        self.min_age = DEFAULT_MIN_AGE_SECONDS
        self.root: "Path | None" = None
        self.allow_empty_registry = False
        self.error: "str | None" = None


def _lire_entier(valeur: str, option: str) -> "int | str":
    try:
        nombre = int(valeur)
    except ValueError:
        return f"L'option {option} attend un nombre entier de secondes. Reçu : {valeur!r}."
    if nombre < 0:
        return f"L'option {option} ne peut pas être négative. Reçu : {nombre}."
    return nombre


def parse_options(argv: list[str]) -> _Options:
    """Lit les arguments. Un argument inconnu est une erreur, jamais un silence.

    Ignorer `--dlete` ferait afficher un rapport là où l'exploitant croyait
    supprimer, ou l'inverse.
    """
    options = _Options()
    index = 0
    while index < len(argv):
        argument = argv[index]
        if argument == "--delete":
            options.delete = True
        elif argument == "--allow-empty-registry":
            options.allow_empty_registry = True
        elif argument.startswith("--min-age=") or argument == "--min-age":
            if argument == "--min-age":
                index += 1
                if index >= len(argv):
                    options.error = "L'option --min-age attend un nombre de secondes."
                    return options
                brut = argv[index]
            else:
                brut = argument.partition("=")[2]
            lu = _lire_entier(brut, "--min-age")
            if isinstance(lu, str):
                options.error = lu
                return options
            options.min_age = lu
        elif argument.startswith("--root=") or argument == "--root":
            if argument == "--root":
                index += 1
                if index >= len(argv):
                    options.error = "L'option --root attend un chemin."
                    return options
                brut = argv[index]
            else:
                brut = argument.partition("=")[2]
            if not brut.strip():
                options.error = "L'option --root attend un chemin non vide."
                return options
            options.root = Path(brut)
        else:
            options.error = f"Option inconnue : {argument!r}."
            return options
        index += 1

    if options.delete and options.allow_empty_registry:
        options.error = (
            "--allow-empty-registry avec --delete effacerait tous les fichiers "
            "d'un projet qui n'inscrit rien au registre."
        )
    return options


def _lignes(titre: str, chemins: "tuple[str, ...]") -> list[str]:
    if not chemins:
        return []
    sortie = [f"  {titre} ({len(chemins)}) :"]
    sortie.extend(f"    {chemin}" for chemin in chemins[:APERCU])
    if len(chemins) > APERCU:
        sortie.append(f"    et {len(chemins) - APERCU} autres")
    return sortie


def render_report(report: OrphanReport) -> str:
    """Rapport lisible.

    Dit toujours ce qui a été **écarté**, pas seulement ce qui a été trouvé :
    un exploitant qui ne voit pas son fichier dans la liste doit pouvoir savoir
    s'il a été jugé sain ou seulement jugé trop récent.
    """
    lignes = [
        f"{STATUS_INFO} Disque : {report.files_on_disk} fichiers. "
        f"Registre : {report.files_in_registry} inscriptions."
    ]
    if report.skipped_too_recent:
        lignes.append(
            f"{STATUS_INFO} {report.skipped_too_recent} fichiers trop récents, "
            "écartés par précaution."
        )
    if report.is_empty:
        lignes.append(f"{STATUS_OK} Aucun orphelin.")
        return "\n".join(lignes)

    lignes.extend(_lignes("Sur disque, jamais inscrits", report.on_disk_only))
    lignes.extend(_lignes("Inscrits, disparus du disque", report.in_registry_only))
    return "\n".join(lignes)


def main(args: "list[str] | None" = None) -> int:
    argv = list(args or [])
    options = parse_options(argv)
    if options.error:
        print(f"{STATUS_ERROR} {options.error}")
        return 1

    try:
        report = find_orphans(
            root=options.root,
            min_age_seconds=options.min_age,
            allow_empty_registry=options.allow_empty_registry,
        )
    except OrphanPurgeRefused as exc:
        print(f"{STATUS_ERROR} {exc}")
        return 1

    print(render_report(report))

    if not options.delete:
        if not report.is_empty:
            print(
                f"{STATUS_INFO} Rien n'a été supprimé. "
                "Relancer avec --delete pour appliquer."
            )
        return 0

    resultat = purge_orphans(report)
    print(
        f"{STATUS_OK} Supprimés : {len(resultat.deleted_files)} fichiers, "
        f"{len(resultat.forgotten_records)} inscriptions."
    )
    if resultat.failed:
        print(f"{STATUS_ERROR} Échecs ({len(resultat.failed)}) :")
        for chemin, motif in resultat.failed:
            print(f"    {chemin} : {motif}")
        return 1
    return 0
