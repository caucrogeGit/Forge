# pyright: strict
"""Commande ``forge jobs:reclaim`` — reprise des tâches orphelines (JOBS-STALE-RECLAIM-001).

Un worker tué en cours de traitement laisse sa tâche au statut `running`, jeton
de réservation posé. Personne ne la reprenait : elle restait bloquée jusqu'à ce
qu'un humain la remette en file à la main, et la file se remplissait de tâches
mortes que rien ne signalait.

Cette commande remet en file les tâches dont le bail de réservation a expiré, et
marque en échec celles qui ont épuisé leurs tentatives.

À brancher sur un ordonnanceur externe, cron ou minuteur systemd. Forge ne
fournit pas de planificateur, comme pour `sessions:gc` et `audit:gc`.

Le bail par défaut est de 900 secondes. **Réglez-le au-dessus de votre tâche la
plus longue** : une tâche encore en cours mais plus lente que le bail serait
reprise et donc exécutée deux fois. La reprise ne promet pas l'exécution unique,
elle promet qu'aucune tâche ne reste bloquée.
"""
from __future__ import annotations

import sys

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_ERROR = "[ERREUR]"

#: Variable d'environnement portant le bail, en secondes.
ENV_LEASE_SECONDS = "JOBS_LEASE_SECONDS"

__all__ = [
    "STATUS_OK",
    "STATUS_INFO",
    "STATUS_ERROR",
    "ENV_LEASE_SECONDS",
    "resolve_option",
    "main",
]


def resolve_option(
    argv: list[str],
    nom: str,
    defaut: "int | None",
    env: "dict[str, str] | None" = None,
    variable: "str | None" = None,
) -> "int | str":
    """Valeur entière d'une option `--nom`, sinon de l'environnement, sinon `defaut`.

    Retourne un `int` en cas de succès, un `str` décrivant le problème sinon, de
    sorte que l'appelant décide seul du code de sortie et du flux de sortie.
    """
    brut: str | None = None
    prefixe = f"--{nom}="
    for index, argument in enumerate(argv):
        if argument.startswith(prefixe):
            brut = argument[len(prefixe):]
            break
        if argument == f"--{nom}":
            if index + 1 >= len(argv):
                return f"L'option --{nom} attend une valeur."
            brut = argv[index + 1]
            break
    if brut is None and variable is not None and env is not None:
        brut = env.get(variable)
    if brut is None or not brut.strip():
        if defaut is None:
            return f"Aucune valeur pour --{nom}."
        return defaut
    try:
        return int(brut.strip())
    except ValueError:
        return f"Valeur illisible pour --{nom} : {brut!r}. Un entier est attendu."


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge jobs:reclaim``."""
    import os

    from forge_mvc_jobs.errors import JobError
    from forge_mvc_jobs.queue import DEFAULT_LEASE_SECONDS, reclaim_stale

    argv = list(args or [])

    bail = resolve_option(
        argv, "lease", DEFAULT_LEASE_SECONDS, env=dict(os.environ), variable=ENV_LEASE_SECONDS
    )
    if isinstance(bail, str):
        print(f"{STATUS_ERROR} {bail}", file=sys.stderr)
        return 1

    file_ = "default"
    for index, argument in enumerate(argv):
        if argument.startswith("--queue="):
            file_ = argument.partition("=")[2]
        elif argument == "--queue" and index + 1 < len(argv):
            file_ = argv[index + 1]

    try:
        effet = reclaim_stale(queue=file_, lease_seconds=bail)
    except JobError as erreur:
        print(f"{STATUS_ERROR} {erreur}", file=sys.stderr)
        return 1

    if effet.total == 0:
        print(
            f"{STATUS_INFO} Aucune tâche orpheline dans la file '{file_}' "
            f"(bail de {bail} s)."
        )
        return 0

    print(
        f"{STATUS_OK} {effet.requeued} tâche(s) remise(s) en file et "
        f"{effet.failed} marquée(s) en échec dans la file '{file_}' "
        f"(bail de {bail} s)."
    )
    return 0
