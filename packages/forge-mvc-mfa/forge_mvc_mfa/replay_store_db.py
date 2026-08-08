# pyright: strict
"""Registre anti-rejeu TOTP adossé à la base, partagé par tous les processus.

Le magasin par défaut vit dans la mémoire d'un processus, si bien que derrière
gunicorn à plusieurs workers un même code peut être accepté une fois par worker.
Celui-ci écrit dans la base, donc tous les workers voient le même registre.

Aucune dépendance nouvelle. `core.database` vient de `forge-mvc`, déjà exigé par
le paquet, et l'import reste **paresseux** pour que `forge-mvc-mfa` demeure
utilisable sans backend BDD tant que ce magasin n'est pas installé.

## Pourquoi une ligne par facteur

Le contrat refuse toute fenêtre antérieure **ou égale** à la dernière vue, et
non seulement le doublon exact : sans cela un code plus ancien resterait
rejouable tant que la tolérance de `verify_totp_code` l'accepte. Retenir la
dernière fenêtre par facteur reproduit donc la règle exactement, et borne la
table au nombre de facteurs actifs plutôt qu'au nombre d'authentifications.

## Comment l'atomicité est obtenue, sans transaction

`check_and_record` tente d'abord l'`INSERT`. S'il échoue sur un doublon de clé
primaire, la ligne existe, et un `UPDATE` gardé par `last_step < ?` tranche :
`rowcount` à 1 vaut acceptation, 0 vaut rejeu. Deux ouvriers qui présentent la
même fenêtre ne peuvent pas gagner tous les deux, le second voyant sa garde
fausse. Le doublon est reconnu par `is_unique_violation()`, porté par le contrat
`DatabaseBackend` : aucun code d'erreur n'est portable, et le SQLSTATE 23000 ne
discrimine ni sur MariaDB ni sur SQL Server (`UNIQUE-VIOLATION-PORTABLE-001`).
"""
from __future__ import annotations

from typing import Any

from forge_mvc_mfa.tables import TOTP_REPLAY_TABLE_NAME as _TABLE
from forge_mvc_mfa.totp_replay import (
    _PURGE_AFTER_SECONDS,  # pyright: ignore[reportPrivateUsage]
    is_usable_factor_id,
    step_for_time,
)

__all__ = ["DbTotpReplayStore"]

_INSERT_SQL = f"INSERT INTO {_TABLE} (factor_id, last_step) VALUES (?, ?)"
_ADVANCE_SQL = f"UPDATE {_TABLE} SET last_step = ? WHERE factor_id = ? AND last_step < ?"
_SELECT_SQL = f"SELECT last_step FROM {_TABLE} WHERE factor_id = ?"
_PURGE_SQL = f"DELETE FROM {_TABLE} WHERE last_step < ?"
_PURGE_ALL_SQL = f"DELETE FROM {_TABLE}"


def _db_module() -> Any:
    import core.database.db as db  # noqa: PLC0415

    return db


def _is_duplicate(error: Exception) -> bool:
    from core.database.qualify import is_unique_violation  # noqa: PLC0415

    return is_unique_violation(error)


class DbTotpReplayStore:
    """Registre anti-rejeu partagé, écrit dans la table `mfa_totp_replay`.

    S'installe explicitement au démarrage de l'application :

    ```python
    from forge_mvc_mfa import set_replay_store
    from forge_mvc_mfa.replay_store_db import DbTotpReplayStore

    set_replay_store(DbTotpReplayStore())
    ```

    `db` permet d'injecter un module compatible pour les tests ; par défaut le
    magasin passe par `core.database.db`.
    """

    def __init__(self, *, db: Any = None) -> None:
        self._db = db

    def _database(self) -> Any:
        return self._db if self._db is not None else _db_module()

    def is_replay(self, factor_id: int, step: int) -> bool:
        if not is_usable_factor_id(factor_id):
            return False
        row = self._database().fetch_one(_SELECT_SQL, (factor_id,))
        if row is None:
            return False
        return step <= int(row["last_step"])

    def check_and_record(self, factor_id: int, step: int) -> bool:
        if not is_usable_factor_id(factor_id):
            return True
        return self._claim(factor_id, step)

    def record_used(self, factor_id: int, step: int) -> None:
        if not is_usable_factor_id(factor_id):
            return
        self._claim(factor_id, step)

    def purge_old(self, now_seconds: float) -> int:
        cutoff_step = step_for_time(now_seconds - _PURGE_AFTER_SECONDS)
        return int(self._database().execute(_PURGE_SQL, (cutoff_step,)))

    def purge_all(self) -> None:
        self._database().execute(_PURGE_ALL_SQL, ())

    # ── interne ──────────────────────────────────────────────────────────────

    def _claim(self, factor_id: int, step: int) -> bool:
        """Consomme la fenêtre. Vrai si elle était neuve, faux si rejeu.

        La première authentification d'un facteur pose la ligne ; les suivantes
        avancent `last_step` sous garde. Les deux chemins sont atomiques du
        point de vue du serveur, aucun n'ouvre de transaction applicative.
        """
        database = self._database()
        try:
            database.execute(_INSERT_SQL, (factor_id, step))
        except Exception as error:  # noqa: BLE001 — seul le doublon est rattrapé
            if not _is_duplicate(error):
                raise
        else:
            return True
        return int(database.execute(_ADVANCE_SQL, (step, factor_id, step))) == 1
