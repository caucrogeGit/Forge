# pyright: strict
"""Anti-replay TOTP — RFC 6238 §5.2 : un code accepté ne peut pas être rejoué.

Le registre est derrière un **contrat**, :class:`TotpReplayStore`, dont Forge
livre deux mises en œuvre.

:class:`InMemoryTotpReplayStore` est le **défaut**, inchangé depuis l'origine.
Il vit dans la mémoire du processus, donc chaque worker gunicorn a le sien, et
un même code peut être accepté une fois par worker.
Sa portée est dite à l'exploitant (`MFA-REPLAY-SCOPE-DOC-001`).

:class:`~forge_mvc_mfa.replay_store_db.DbTotpReplayStore` est adossé à la base
et vaut donc pour tous les processus à la fois.
Il ne s'active pas tout seul, l'application le pose par
:func:`set_replay_store` au démarrage, en une ligne visible (principe 3).
Le remède reste ainsi au choix de l'exploitant selon son modèle de menace, ce
que la décision antérieure avait posé, mais il existe désormais.

Le contrat est plus fort qu'un simple refus du doublon.
Une fenêtre **antérieure** à la dernière vue est refusée elle aussi, sans quoi
un code plus ancien resterait rejouable tant que la tolérance de
``verify_totp_code`` (``valid_window=1``) l'accepte.
Les deux magasins ne retiennent donc que la dernière fenêtre par facteur.
"""

from __future__ import annotations

import threading
import time
from typing import Protocol


_TOTP_PERIOD_SECONDS = 30
_PURGE_AFTER_SECONDS = 24 * 3600
_PURGE_EVERY_N_RECORDS = 100


def step_for_time(at_seconds: float) -> int:
    """Retourne le numéro de step TOTP pour un timestamp Unix (float)."""
    return int(at_seconds // _TOTP_PERIOD_SECONDS)


def is_usable_factor_id(factor_id: int) -> bool:
    """Un identifiant de facteur traçable, donc utilisable comme clé.

    Un `factor_id` absent ou aberrant n'identifie rien : le magasin ne peut ni
    le retenir ni décider à son sujet, et les fonctions publiques le laissent
    alors passer plutôt que de bloquer une authentification sur une clé qu'elles
    ne savent pas lire.
    """
    if not isinstance(factor_id, int) or isinstance(factor_id, bool):  # pyright: ignore[reportUnnecessaryIsInstance]
        return False
    return factor_id > 0


class TotpReplayStore(Protocol):
    """Registre des fenêtres TOTP déjà consommées, par facteur.

    Toute mise en œuvre doit garantir que :meth:`check_and_record` est
    **atomique** : deux requêtes concurrentes portant le même code valide ne
    peuvent pas être acceptées toutes les deux.
    """

    def is_replay(self, factor_id: int, step: int) -> bool:
        """Vrai si cette fenêtre a déjà été consommée, ou est antérieure."""
        ...

    def check_and_record(self, factor_id: int, step: int) -> bool:
        """Consomme la fenêtre et retourne vrai, ou retourne faux si rejeu."""
        ...

    def record_used(self, factor_id: int, step: int) -> None:
        """Enregistre la fenêtre sans rien décider. N'avance jamais à reculons."""
        ...

    def purge_old(self, now_seconds: float) -> int:
        """Retire les entrées trop anciennes. Retourne le nombre supprimé."""
        ...

    def purge_all(self) -> None:
        """Vide le registre. Réservé aux tests."""
        ...


class InMemoryTotpReplayStore:
    """Registre en mémoire du processus, thread-safe par `RLock`.

    Défaut historique de Forge, sans dépendance ni écriture.
    Limite assumée, en multi-worker chaque processus a le sien, et rien ne
    survit à un redémarrage (fenêtre de risque inférieure à 30 s).
    """

    def __init__(self) -> None:
        self._used_steps: dict[int, int] = {}
        self._lock = threading.RLock()
        self._record_count = 0

    def is_replay(self, factor_id: int, step: int) -> bool:
        if not is_usable_factor_id(factor_id):
            return False
        with self._lock:
            last = self._used_steps.get(factor_id)
            return last is not None and step <= last

    def record_used(self, factor_id: int, step: int) -> None:
        if not is_usable_factor_id(factor_id):
            return
        with self._lock:
            previous = self._used_steps.get(factor_id)
            if previous is None or step > previous:
                self._used_steps[factor_id] = step
            self._tick_purge()

    def check_and_record(self, factor_id: int, step: int) -> bool:
        if not is_usable_factor_id(factor_id):
            return True
        with self._lock:
            last = self._used_steps.get(factor_id)
            if last is not None and step <= last:
                return False
            self._used_steps[factor_id] = step
            self._tick_purge()
            return True

    def purge_old(self, now_seconds: float) -> int:
        with self._lock:
            return self._do_purge_old(now_seconds)

    def purge_all(self) -> None:
        with self._lock:
            self._used_steps.clear()
            self._record_count = 0

    # ── interne ──────────────────────────────────────────────────────────────

    def _tick_purge(self) -> None:
        """Purge opportuniste, à appeler avec le verrou déjà tenu."""
        self._record_count += 1
        if self._record_count >= _PURGE_EVERY_N_RECORDS:
            self._record_count = 0
            self._do_purge_old(time.time())

    def _do_purge_old(self, now_seconds: float) -> int:
        """Implémentation interne — doit être appelée avec le verrou tenu."""
        cutoff_step = step_for_time(now_seconds - _PURGE_AFTER_SECONDS)
        old = [fid for fid, last in self._used_steps.items() if last < cutoff_step]
        for fid in old:
            del self._used_steps[fid]
        return len(old)


_store: TotpReplayStore = InMemoryTotpReplayStore()
_store_lock = threading.RLock()


def set_replay_store(store: TotpReplayStore) -> None:
    """Installe le magasin anti-rejeu du processus.

    À appeler **au démarrage**, avant de servir la première requête, depuis le
    point d'entrée de l'application. Exemple, pour partager le registre entre
    tous les workers :

    ```python
    from forge_mvc_mfa import set_replay_store
    from forge_mvc_mfa.replay_store_db import DbTotpReplayStore

    set_replay_store(DbTotpReplayStore())
    ```

    La table correspondante se provisionne par `forge mfa:init` puis
    `forge migration:apply`.
    """
    global _store
    with _store_lock:
        _store = store


def get_replay_store() -> TotpReplayStore:
    """Magasin anti-rejeu courant du processus."""
    with _store_lock:
        return _store


def reset_replay_store() -> None:
    """Rétablit le magasin par défaut, en mémoire. Réservé aux tests."""
    set_replay_store(InMemoryTotpReplayStore())


def is_replay(factor_id: int, step: int) -> bool:
    """Retourne True si cette step a déjà été utilisée pour ce facteur."""
    return get_replay_store().is_replay(factor_id, step)


def record_used(factor_id: int, step: int) -> None:
    """Enregistre qu'un code de cette step a été accepté pour ce facteur.

    Avance la step enregistrée seulement — ne régresse jamais.
    """
    get_replay_store().record_used(factor_id, step)


def check_and_record(factor_id: int, step: int) -> bool:
    """Vérifie et enregistre la step de façon **atomique**.

    Retourne True si la step n'avait pas encore été consommée pour ce facteur
    (elle est alors enregistrée), False s'il s'agit d'un rejeu. Ferme la fenêtre
    de course entre `is_replay()` (avant la vérification du code) et
    `record_used()` (après) : deux requêtes concurrentes portant le même code
    valide ne peuvent plus être acceptées toutes les deux.

    Un `factor_id` invalide n'est pas traçable : on renvoie True (ne bloque
    pas), cohérent avec `is_replay()`/`record_used()`.
    """
    return get_replay_store().check_and_record(factor_id, step)


def purge_old(now_seconds: float | None = None) -> int:
    """Supprime les entrées dont la step est antérieure à 24h dans le passé.

    Retourne le nombre d'entrées supprimées.
    """
    ts = now_seconds if now_seconds is not None else time.time()
    return get_replay_store().purge_old(ts)


def purge_all() -> None:
    """Vide le store complet — réservé aux tests."""
    get_replay_store().purge_all()
