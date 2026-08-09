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

`check_and_record` tente d'abord l'`UPDATE`, gardé par `last_step < ?` :
`rowcount` à 1 vaut acceptation. À zéro ligne touchée, soit le facteur est
inconnu, soit la fenêtre est déjà consommée, et l'`INSERT` tranche, son échec en
doublon valant rejeu. Deux ouvriers qui présentent la même fenêtre ne peuvent
pas gagner tous les deux.

Cet ordre n'est pas indifférent, et le pré-mortem de la rc5 l'a montré
(`PREMORTEM-RC5-003`). L'ordre inverse, `INSERT` puis `UPDATE`, provoquait un
interblocage InnoDB sous concurrence : un `INSERT` qui échoue prend un verrou
partagé sur la ligne, et l'`UPDATE` suivant en réclame un exclusif. Les deux
défauts trouvés alors sont couverts par
`tests/db/test_mfa_replay_concurrency_real_server_001.py`, qui passe par la
vraie couche de données et non par un adaptateur.
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
    """Cette erreur est-elle un doublon de clé ?

    Deux formes possibles, et confondre les deux coûte cher.

    `core.database.db` **qualifie déjà** ses erreurs et lève
    :class:`UniqueViolationError`, forme portable du doublon. C'est le cas en
    production, et c'est celui à tester en premier.

    `is_unique_violation()`, elle, interroge le backend sur une erreur **de
    pilote**. Appliquée à l'exception déjà qualifiée, elle rend `False`, le
    wrapper n'étant plus un objet du pilote. Ce module ne testait que celle-là,
    si bien que chaque rejeu remontait une erreur au lieu d'un refus propre :
    défaut trouvé en mettant le magasin en concurrence réelle
    (`PREMORTEM-RC5-003`). Le CRUD engendré et `forge-mvc-settings` attrapaient
    déjà `UniqueViolationError`, ce module était le seul à s'en écarter.

    Le second test reste utile pour un exécuteur injecté qui laisserait passer
    l'erreur brute du pilote, ce que font les adaptateurs de test.
    """
    from core.database.errors import UniqueViolationError  # noqa: PLC0415
    from core.database.qualify import is_unique_violation  # noqa: PLC0415

    return isinstance(error, UniqueViolationError) or is_unique_violation(error)


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

        L'`UPDATE` passe **en premier**, et l'`INSERT` ne sert que de repli
        quand aucune ligne n'existe encore. L'ordre inverse paraît plus naturel,
        il est pourtant faux sous concurrence, et c'est un pré-mortem qui l'a
        montré : douze requêtes simultanées sur le même facteur provoquaient un
        `Deadlock found when trying to get lock` et remontaient une erreur au
        client (`PREMORTEM-RC5-003`).

        La raison tient à InnoDB. Un `INSERT` qui échoue sur doublon prend un
        verrou **partagé** sur la ligne existante ; l'`UPDATE` qui suivait
        réclamait alors un verrou **exclusif** sur cette même ligne. N requêtes
        détenant chacune le partagé et voulant l'exclusif se bloquent
        mutuellement, et le moteur en tue une partie.

        Dans l'ordre retenu, l'`UPDATE` prend directement le verrou exclusif et
        l'`INSERT` est terminal, donc aucune montée en puissance de verrou ne
        peut se croiser. C'est aussi le plus rapide : passé la première
        authentification d'un facteur, la ligne existe toujours, donc le premier
        ordre suffit.
        """
        database = self._database()
        if int(database.execute(_ADVANCE_SQL, (step, factor_id, step))) == 1:
            return True

        # Zéro ligne touchée : soit le facteur est inconnu, soit la fenêtre est
        # déjà consommée. L'`INSERT` tranche, son échec en doublon signifiant
        # qu'une autre requête a posé la ligne entre-temps, donc rejeu.
        try:
            database.execute(_INSERT_SQL, (factor_id, step))
        except Exception as error:  # noqa: BLE001 — seul le doublon est rattrapé
            if not _is_duplicate(error):
                raise
            return False
        return True
