# pyright: strict
"""Commande ``forge jobs:status`` — état des files de tâches (JOBS-STATUS-CLI-001).

Le paquet n'offrait aucun moyen de voir sa file. Un exploitant qui se demandait
si le travail avançait devait interroger la base à la main, et rien ne lui
disait quelle requête écrire. Une file bloquée ressemblait donc exactement à
une file vide.

La commande lit et n'écrit rien. Elle ne relance aucune tâche, ne reprend aucun
orphelin, ne purge rien : `jobs:reclaim` fait la reprise, et confondre les deux
donnerait à une commande de diagnostic un effet de bord que personne n'attend.

## Ce que « en attente » ne dit pas

Une tâche `pending` peut être différée, par `available_in` ou par le délai
croissant d'un réessai. Compter les deux ensemble ferait chercher un ouvrier en
panne là où tout se déroule normalement, d'où la colonne « prêtes », qui ne
retient que les tâches réellement disponibles maintenant.
"""
from __future__ import annotations

import sys

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_WARN = "[ATTENTION]"
STATUS_ERROR = "[ERREUR]"

__all__ = [
    "STATUS_OK",
    "STATUS_INFO",
    "STATUS_WARN",
    "STATUS_ERROR",
    "resolve_queue",
    "format_status_lines",
    "main",
]

_AIDE = (
    "Usage :\n"
    "  forge jobs:status              # toutes les files\n"
    "  forge jobs:status --queue mails"
)


def resolve_queue(argv: list[str]) -> "str | None":
    """File demandée par `--queue`, ou `None` pour toutes.

    Rend une chaîne vide si l'option est présente sans valeur, ce que
    l'appelant traite comme une erreur : `--queue` suivi de rien est une faute
    de frappe, pas une demande de tout voir.
    """
    for index, argument in enumerate(argv):
        if argument.startswith("--queue="):
            return argument.partition("=")[2].strip()
        if argument == "--queue":
            if index + 1 >= len(argv):
                return ""
            return argv[index + 1].strip()
    return None


def format_status_lines(etats: "list[object]") -> list[str]:
    """Rend l'état des files en lignes alignées, une par file.

    Séparé de l'affichage pour être testable sans capturer une sortie.
    """
    from forge_mvc_jobs.queue import JOB_STATUSES, QueueStatus

    files = [e for e in etats if isinstance(e, QueueStatus)]
    if not files:
        return []

    largeur = max(len(e.queue) for e in files)
    largeur = max(largeur, len("FILE"))

    entete = (
        f"{'FILE':<{largeur}}  "
        + "  ".join(f"{statut.upper():>8}" for statut in JOB_STATUSES)
        + f"  {'PRÊTES':>8}"
    )
    lignes = [entete, "-" * len(entete)]

    for etat in files:
        cellules = "  ".join(
            f"{etat.counts.get(statut, 0):>8}" for statut in JOB_STATUSES
        )
        lignes.append(f"{etat.queue:<{largeur}}  {cellules}  {etat.ready:>8}")
    return lignes


def main(args: "list[str] | None" = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge jobs:status``."""
    from forge_mvc_jobs.queue import status_counts

    argv = list(args or [])
    file = resolve_queue(argv)
    if file == "":
        print(f"{STATUS_ERROR} L'option --queue attend un nom de file.\n{_AIDE}",
              file=sys.stderr)
        return 1

    etats = status_counts(queue=file)
    if not etats:
        portee = f"la file « {file} »" if file else "aucune file"
        print(f"{STATUS_INFO} Aucune tâche dans {portee}.")
        return 0

    for ligne in format_status_lines(list(etats)):
        print(ligne)

    en_echec = sum(e.counts.get("failed", 0) for e in etats)
    bloquees = sum(e.counts.get("running", 0) for e in etats)
    print()
    if en_echec:
        print(f"{STATUS_WARN} {en_echec} tâche(s) en échec. "
              "Voir last_error, colonne de la table jobs.")
    if bloquees:
        print(f"{STATUS_INFO} {bloquees} tâche(s) réservée(s). "
              "Une réservation qui dure signale un ouvrier tué : forge jobs:reclaim.")
    if not en_echec and not bloquees:
        print(f"{STATUS_OK} Rien d'anormal.")
    return 0
