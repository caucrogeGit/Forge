# pyright: strict
"""Commande ``forge stats:gc`` — purge des événements par âge (STATS-RETENTION-001).

`forge_stats_events` reçoit une ligne par événement suivi et rien ne la bornait.
Une application qui trace consciencieusement y accumule des millions de lignes,
et les agrégats ralentissent d'autant sans que rien ne prévienne.

Même forme que `forge audit:gc`, et pour la même raison : purger détruit de
l'information délibérément enregistrée. La commande **affiche** le nombre de
lignes visées par défaut et n'efface qu'avec ``--run`` (charte §7).

La rétention doit être **dite**, par ``--days N`` ou par la variable
``STATS_KEEP_DAYS``. Aucune valeur par défaut n'est supposée à la place de
l'exploitant.

À brancher sur un ordonnanceur externe, cron ou minuteur systemd. Forge ne
fournit pas de planificateur.
"""
from __future__ import annotations

import os
import sys

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_ERROR = "[ERREUR]"

#: Variable d'environnement portant la rétention, en jours.
ENV_KEEP_DAYS = "STATS_KEEP_DAYS"

__all__ = ["STATUS_OK", "STATUS_INFO", "STATUS_ERROR", "ENV_KEEP_DAYS", "resolve_keep_days", "main"]

_AIDE = (
    "Indiquez la rétention, en jours, par --days N ou par la variable "
    f"d'environnement {ENV_KEEP_DAYS}.\n"
    "  forge stats:gc --days 365          # affiche ce qui serait supprimé\n"
    "  forge stats:gc --days 365 --run    # supprime"
)


def resolve_keep_days(argv: list[str], env: "dict[str, str] | None" = None) -> "int | str":
    """Rétention retenue, ou un message d'erreur si elle est absente ou illisible.

    L'argument l'emporte sur l'environnement : une valeur tapée à la main dit
    une intention plus précise qu'une valeur héritée du déploiement.
    """
    variables = os.environ if env is None else env

    brut: str | None = None
    for index, argument in enumerate(argv):
        if argument.startswith("--days="):
            brut = argument.partition("=")[2]
            break
        if argument == "--days":
            if index + 1 >= len(argv):
                return "L'option --days attend un nombre de jours."
            brut = argv[index + 1]
            break
    if brut is None:
        brut = variables.get(ENV_KEEP_DAYS)
    if brut is None or not brut.strip():
        return "Aucune rétention indiquée."

    try:
        jours = int(brut.strip())
    except ValueError:
        return f"Rétention illisible : {brut!r}. Un nombre entier de jours est attendu."
    if jours < 1:
        return (
            f"Rétention invalide : {jours}. "
            "Une rétention nulle ou négative viderait toute la table d'événements."
        )
    try:
        # La borne est calculee par le coeur, qui seul connait ce qu'une date
        # sait representer. Sans ce controle, une retention absurde traversait
        # la validation et sortait en trace Python nue depuis la commande
        # (`DB-RETENTION-OVERFLOW-001`).
        from forge_mvc_stats.retention import cutoff_for_days as _borne

        _borne(jours)
    except ValueError as exc:
        return str(exc)
    return jours


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge stats:gc``."""
    import core.database.db as db

    from forge_mvc_stats.retention import (
        count_stats_events_before,
        cutoff_for_days,
        purge_stats_events_before,
    )

    argv = list(args or [])
    jours = resolve_keep_days(argv)
    if isinstance(jours, str):
        print(f"{STATUS_ERROR} {jours}\n{_AIDE}", file=sys.stderr)
        return 1

    borne = cutoff_for_days(jours)
    vises = count_stats_events_before(db.fetch_one, borne)

    if "--run" not in argv:
        print(
            f"{STATUS_INFO} {vises} événement(s) antérieur(s) au {borne} UTC "
            f"(rétention de {jours} jour(s)).\n"
            f"{STATUS_INFO} Rien n'a été supprimé. Relancez avec --run pour exécuter."
        )
        return 0

    supprimes = purge_stats_events_before(db.execute, borne)
    print(
        f"{STATUS_OK} {supprimes} événement(s) purgé(s), "
        f"antérieurs au {borne} UTC (rétention de {jours} jour(s))."
    )
    return 0
