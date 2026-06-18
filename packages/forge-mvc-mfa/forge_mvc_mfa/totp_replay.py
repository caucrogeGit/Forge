# pyright: strict
"""Anti-replay TOTP — RFC 6238 §5.2 : un code accepté ne peut pas être rejoué.

Le store est in-memory process-local (thread-safe via RLock).
Limitation assumée : en multi-worker chaque processus a son propre dict.
Pas de persistance entre redémarrages (fenêtre de risque < 30 s).
"""

from __future__ import annotations

import threading
import time


_TOTP_PERIOD_SECONDS = 30
_PURGE_AFTER_SECONDS = 24 * 3600
_PURGE_EVERY_N_RECORDS = 100

# factor_id (int) → dernière step TOTP acceptée
_used_steps: dict[int, int] = {}
_lock = threading.RLock()
_record_count = 0


def step_for_time(at_seconds: float) -> int:
    """Retourne le numéro de step TOTP pour un timestamp Unix (float)."""
    return int(at_seconds // _TOTP_PERIOD_SECONDS)


def is_replay(factor_id: int, step: int) -> bool:
    """Retourne True si cette step a déjà été utilisée pour ce facteur."""
    if not isinstance(factor_id, int) or isinstance(factor_id, bool) or factor_id <= 0:  # pyright: ignore[reportUnnecessaryIsInstance]
        return False
    with _lock:
        last = _used_steps.get(factor_id)
        return last is not None and step <= last


def record_used(factor_id: int, step: int) -> None:
    """Enregistre qu'un code de cette step a été accepté pour ce facteur.

    Avance la step enregistrée seulement — ne régresse jamais.
    Déclenche une purge opportuniste toutes les _PURGE_EVERY_N_RECORDS opérations.
    """
    global _record_count
    if not isinstance(factor_id, int) or isinstance(factor_id, bool) or factor_id <= 0:  # pyright: ignore[reportUnnecessaryIsInstance]
        return
    with _lock:
        previous = _used_steps.get(factor_id)
        if previous is None or step > previous:
            _used_steps[factor_id] = step
        _record_count += 1
        if _record_count >= _PURGE_EVERY_N_RECORDS:
            _record_count = 0
            _do_purge_old(time.time())


def check_and_record(factor_id: int, step: int) -> bool:
    """Vérifie et enregistre la step de façon **atomique** (un seul verrou).

    Retourne True si la step n'avait pas encore été consommée pour ce facteur
    (elle est alors enregistrée), False s'il s'agit d'un rejeu. Ferme la fenêtre
    de course entre `is_replay()` (avant la vérification du code) et
    `record_used()` (après) : deux requêtes concurrentes portant le même code
    valide ne peuvent plus être acceptées toutes les deux.

    Un `factor_id` invalide n'est pas traçable : on renvoie True (ne bloque
    pas), cohérent avec `is_replay()`/`record_used()`.
    """
    global _record_count
    if not isinstance(factor_id, int) or isinstance(factor_id, bool) or factor_id <= 0:  # pyright: ignore[reportUnnecessaryIsInstance]
        return True
    with _lock:
        last = _used_steps.get(factor_id)
        if last is not None and step <= last:
            return False
        _used_steps[factor_id] = step
        _record_count += 1
        if _record_count >= _PURGE_EVERY_N_RECORDS:
            _record_count = 0
            _do_purge_old(time.time())
        return True


def purge_old(now_seconds: float | None = None) -> int:
    """Supprime les entrées dont la step est antérieure à 24h dans le passé.

    Retourne le nombre d'entrées supprimées.
    """
    ts = now_seconds if now_seconds is not None else time.time()
    with _lock:
        return _do_purge_old(ts)


def _do_purge_old(now_seconds: float) -> int:
    """Implémentation interne — doit être appelée avec _lock déjà acquis."""
    cutoff_step = step_for_time(now_seconds - _PURGE_AFTER_SECONDS)
    old = [fid for fid, last in _used_steps.items() if last < cutoff_step]
    for fid in old:
        del _used_steps[fid]
    return len(old)


def purge_all() -> None:
    """Vide le store complet — réservé aux tests."""
    global _record_count
    with _lock:
        _used_steps.clear()
        _record_count = 0
