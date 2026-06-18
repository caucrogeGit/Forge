# pyright: strict
"""Repository d'insertion des événements IoT — IOT-STORAGE-REPOSITORY-001.

Premier branchement réel entre le contrat de stockage (``events.py``)
et la base de données Forge (``core.database.db``).

Le repository :

- prend une ``Measurement`` produite par le subscriber MQTT ;
- réutilise ``build_insert_iot_event_sql`` pour produire le SQL et les
  paramètres ;
- délègue l'exécution à un *adapter* injectable (par défaut
  ``core.database.db``, qui gère lui-même commit/rollback) ;
- ne **crée pas** la table — la migration ``iot_events`` doit avoir
  été appliquée au préalable.

Le ticket reste strictement scoped insertion : ni API HTTP, ni
déduplication, ni rétention, ni intégration automatique au subscriber.

Note sur la dépendance : c'est le premier endroit où
``forge-mvc-iot`` importe ``core.database``. C'est acceptable car le
sens des dépendances reste correct : ``forge-mvc-iot`` dépend de
``forge-mvc``, jamais l'inverse.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Protocol

from forge_mvc_iot.mqtt.contract import Measurement
from forge_mvc_iot.storage.events import (
    COLUMNS,
    TABLE_NAME,
    build_insert_iot_event_sql,
)

__all__ = [
    "DEFAULT_LIMIT",
    "MAX_LIMIT",
    "DbAdapter",
    "IotEventRepository",
    "SELECT_IOT_EVENTS_RECENT_SQL",
    "SELECT_IOT_EVENTS_BY_DEVICE_SQL",
    "COUNT_IOT_EVENTS_BY_DEVICE_SQL",
]


DEFAULT_LIMIT = 100
"""Nombre maximum de lignes retournées par défaut."""

MAX_LIMIT = 1000
"""Plafond strict — au-delà, ``ValueError``. Ce ticket reste sans
pagination avancée ; un appel qui demanderait plus est probablement
erroné côté caller."""


# ── SQL — lectures explicites ───────────────────────────────────────────────

_READ_COLUMNS = ("id", *COLUMNS)
_READ_COLUMNS_SQL = ", ".join(_READ_COLUMNS)

SELECT_IOT_EVENTS_RECENT_SQL = (
    f"SELECT {_READ_COLUMNS_SQL} "
    f"FROM {TABLE_NAME} "
    "ORDER BY received_at DESC "
    "LIMIT ?"
)

SELECT_IOT_EVENTS_BY_DEVICE_SQL = (
    f"SELECT {_READ_COLUMNS_SQL} "
    f"FROM {TABLE_NAME} "
    "WHERE site = ? AND device_id = ? "
    "ORDER BY received_at DESC "
    "LIMIT ?"
)

COUNT_IOT_EVENTS_BY_DEVICE_SQL = (
    f"SELECT COUNT(*) AS n "
    f"FROM {TABLE_NAME} "
    "WHERE site = ? AND device_id = ?"
)


class DbAdapter(Protocol):
    """Interface attendue par ``IotEventRepository``.

    Conforme au module ``core.database.db`` de Forge : ``execute`` pour
    les ``INSERT``/``UPDATE``/``DELETE`` (gère commit/rollback),
    ``fetch_one`` et ``fetch_all`` pour les ``SELECT`` (retournent des
    dicts).
    """

    def execute(self, sql: str, params: tuple[Any, ...]) -> Any:  # pragma: no cover - protocole
        ...

    def fetch_one(self, sql: str, params: tuple[Any, ...]) -> dict[str, Any] | None:  # pragma: no cover - protocole
        ...

    def fetch_all(self, sql: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:  # pragma: no cover - protocole
        ...


def _default_db_adapter() -> DbAdapter:
    """Importe paresseusement le module ``core.database.db`` de Forge.

    L'import est différé jusqu'à la construction du repository sans
    adapter explicite. ``core.database.db`` ne déclenche aucune
    connexion réseau à l'import (lazy pool — voir
    ``core/database/connection.py``), donc cet import reste sans effet
    de bord. Les tests qui injectent un adapter explicite n'ont jamais
    besoin de ``core.database``.
    """
    from core.database import db  # noqa: PLC0415

    return db


class IotEventRepository:
    """Insère les ``Measurement`` Forge IoT dans la table ``iot_events``.

    Parameters
    ----------
    db_adapter:
        Objet exposant ``execute(sql, params)``. Par défaut, le module
        ``core.database.db`` de Forge — qui gère le pool de connexions,
        le commit et le rollback automatiquement.

    Notes
    -----
    - Le repository ne crée pas la table ``iot_events``. La migration
      ``IOT-STORAGE-MIGRATION-001`` doit avoir été appliquée au
      préalable.
    - Les erreurs SQL sont propagées telles quelles : le repository
      n'intercepte rien silencieusement.
    - Le commit/rollback est délégué à l'adapter (par défaut, Forge
      gère ça dans ``db.execute``). Le repository n'effectue aucun
      `commit` ou `rollback` manuel.
    """

    def __init__(self, db_adapter: DbAdapter | None = None) -> None:
        if db_adapter is None:
            db_adapter = _default_db_adapter()
        self._db: DbAdapter = db_adapter

    def insert(
        self,
        measurement: Measurement,
        *,
        received_at: datetime | None = None,
    ) -> Any:
        """Insère une mesure dans ``iot_events``.

        Parameters
        ----------
        measurement:
            Mesure validée par ``forge_mvc_iot.mqtt.contract.parse_message``.
        received_at:
            Horodatage serveur. Si ``None``, ``datetime.now(UTC)`` est
            utilisé par la sérialisation.

        Returns
        -------
        Retour brut de ``db_adapter.execute(sql, params)``. Avec
        ``core.database.db.execute``, c'est ``rowcount`` (int). Un
        adapter personnalisé peut décider de retourner autre chose
        (par exemple ``lastrowid`` en wrappant ``db.insert``).
        """
        sql, params = build_insert_iot_event_sql(
            measurement, received_at=received_at,
        )
        return self._db.execute(sql, params)

    # ── Lectures ────────────────────────────────────────────────────────────

    def list_recent(self, *, limit: int = DEFAULT_LIMIT) -> list[dict[str, object]]:
        """Retourne les événements les plus récents, ordre `received_at` DESC.

        Parameters
        ----------
        limit:
            Nombre maximum de lignes (``1..MAX_LIMIT``). ``ValueError``
            sinon.
        """
        checked = _validate_limit(limit)
        rows = self._db.fetch_all(SELECT_IOT_EVENTS_RECENT_SQL, (checked,))
        return [_row_to_event_dict(row) for row in rows]

    def find_by_device(
        self,
        site: str,
        device_id: str,
        *,
        limit: int = DEFAULT_LIMIT,
    ) -> list[dict[str, object]]:
        """Retourne les événements d'un device, ordre `received_at` DESC."""
        checked = _validate_limit(limit)
        rows = self._db.fetch_all(
            SELECT_IOT_EVENTS_BY_DEVICE_SQL, (site, device_id, checked),
        )
        return [_row_to_event_dict(row) for row in rows]

    def count_by_device(self, site: str, device_id: str) -> int:
        """Retourne le nombre d'événements d'un device."""
        row = self._db.fetch_one(
            COUNT_IOT_EVENTS_BY_DEVICE_SQL, (site, device_id),
        )
        # COUNT(*) AS n garantit une ligne avec la clé "n" même si la
        # table est vide ; on protège quand même contre un adapter
        # facétieux qui retournerait None.
        if row is None:
            return 0
        return int(row["n"])


# ── Helpers internes ────────────────────────────────────────────────────────


def _validate_limit(limit: int) -> int:
    if isinstance(limit, bool) or not isinstance(limit, int):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise TypeError(
            f"limit doit être un int (vu : {type(limit).__name__})"
        )
    if limit < 1:
        raise ValueError(f"limit doit être >= 1 (vu : {limit})")
    if limit > MAX_LIMIT:
        raise ValueError(
            f"limit doit être <= {MAX_LIMIT} (vu : {limit})"
        )
    return limit


def _row_to_event_dict(row: dict[str, Any]) -> dict[str, object]:
    """Transforme une ligne SQL brute en dict consommable.

    - ``metadata_json`` (string JSON ou ``None``) → ``metadata``
      (dict ou ``None``). Le détail de sérialisation reste interne au
      stockage.
    - Les autres colonnes sont passées telles quelles.
    """
    metadata_json = row.get("metadata_json")
    metadata: dict[str, Any] | None
    if metadata_json is None:
        metadata = None
    else:
        metadata = json.loads(metadata_json)
    return {
        "id": row["id"],
        "site": row["site"],
        "device_id": row["device_id"],
        "kind": row["kind"],
        "value": row["value"],
        "unit": row["unit"],
        "timestamp": row["timestamp"],
        "metadata": metadata,
        "received_at": row["received_at"],
    }
