# pyright: strict
"""Commande ``forge iot:gc`` — purge des mesures IoT par âge (IOT-RETENTION-GC-001).

`iot_events` reçoit une ligne par mesure publiée et rien ne la bornait. Un
capteur qui émet toutes les dix secondes y dépose plus de trois millions de
lignes par an, et un site en compte rarement un seul. La table grossissait donc
jusqu'à la panne de remplissage, sans que rien ne prévienne.

À brancher sur un ordonnanceur externe, cron ou minuteur systemd. Forge ne
fournit pas de planificateur, cette commande est le point d'entrée à
déclencher, comme `sessions:gc`, `audit:gc` et `stats:gc`.

## Pourquoi elle affiche avant d'effacer

Une mesure est un enregistrement délibéré, souvent conservé pour un historique
ou une obligation, et aucune date ne dit d'elle-même qu'elle a cessé de valoir.
La commande **affiche** donc le nombre de lignes visées par défaut et n'efface
qu'avec ``--run``, motif déjà suivi par `audit:gc`, `fixtures:purge` et
`db:init` (charte §7, ADR-067).

La rétention doit par ailleurs être **dite** : aucune valeur par défaut n'est
supposée à la place de l'exploitant, dont les obligations de conservation ne
regardent pas Forge.

## Pourquoi `iot:gc` et non `iot:purge`

Trois opt-ins nommaient déjà ce geste `<opt-in>:gc`, avec la même option
`--days`. Une quatrième forme aurait donné deux façons de dire la même chose,
ce que le principe 11 refuse.
"""
from __future__ import annotations

import os
import sys

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_ERROR = "[ERREUR]"

#: Variable d'environnement portant la rétention, en jours.
ENV_KEEP_DAYS = "IOT_KEEP_DAYS"

__all__ = [
    "STATUS_OK",
    "STATUS_INFO",
    "STATUS_ERROR",
    "ENV_KEEP_DAYS",
    "resolve_keep_days",
    "main",
]

_AIDE = (
    "Indiquez la rétention, en jours, par --days N ou par la variable "
    f"d'environnement {ENV_KEEP_DAYS}.\n"
    "  forge iot:gc --days 90          # affiche ce qui serait supprimé\n"
    "  forge iot:gc --days 90 --run    # supprime"
)


def resolve_keep_days(
    argv: list[str], env: "dict[str, str] | None" = None
) -> "int | str":
    """Rétention retenue, ou un message d'erreur si elle est absente ou illisible.

    L'argument l'emporte sur l'environnement : une valeur tapée à la main dit
    une intention plus précise qu'une valeur héritée du déploiement.

    Retourne un `int` en cas de succès, un `str` décrivant le problème sinon,
    de sorte que l'appelant décide seul du code de sortie et du flux de sortie.
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
            "Une rétention nulle ou négative viderait toute la table de mesures."
        )
    try:
        # La borne est calculee par le coeur, qui seul connait ce qu'une date
        # sait representer. Sans ce controle, une retention absurde traversait
        # la validation et sortait en trace Python nue depuis la commande
        # (`DB-RETENTION-OVERFLOW-001`).
        from forge_mvc_iot.storage.retention import cutoff_for_days as _borne

        _borne(jours)
    except ValueError as exc:
        return str(exc)
    return jours


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge iot:gc``."""
    from core.database import db

    from forge_mvc_iot.storage.retention import (
        cutoff_for_days,
        get_iot_count_before_sql,
        get_iot_purge_sql,
    )

    argv = list(args or [])
    jours = resolve_keep_days(argv)
    if isinstance(jours, str):
        print(f"{STATUS_ERROR} {jours}\n{_AIDE}", file=sys.stderr)
        return 1

    borne = cutoff_for_days(jours)
    ligne = db.fetch_one(get_iot_count_before_sql(), (borne,))
    vises = int(ligne["total"]) if ligne else 0

    if "--run" not in argv:
        print(
            f"{STATUS_INFO} {vises} mesure(s) antérieure(s) au {borne} UTC "
            f"(rétention de {jours} jour(s)).\n"
            f"{STATUS_INFO} Rien n'a été supprimé. Relancez avec --run pour exécuter."
        )
        return 0

    supprimees = int(db.execute(get_iot_purge_sql(), (borne,)))
    print(
        f"{STATUS_OK} {supprimees} mesure(s) purgée(s), "
        f"antérieures au {borne} UTC (rétention de {jours} jour(s))."
    )
    return 0
