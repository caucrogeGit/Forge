# Stockage des événements IoT — contrat SQL

> **Statut** : contrat SQL **figé**, sans branchement base de données.
> Ce ticket (`IOT-STORAGE-EVENTS-001`) définit la table cible, l'ordre
> canonique des colonnes, et fournit les fonctions pures qui sérialisent
> une `Measurement` en `(sql, params)`. La migration versionnée et
> l'insertion réelle sont traitées par les tickets suivants
> (`IOT-STORAGE-MIGRATION-001`, `IOT-STORAGE-REPOSITORY-001`).

## Objectif

Poser le contrat de stockage **avant** d'écrire le repository qui
exécute le SQL. Le subscriber de `IOT-MQTT-SUBSCRIBER-001` produit déjà
des `Measurement` valides ; il manquait juste un consommateur officiel
côté storage, factorisable, testable hors base.

## Module concerné

```text
packages/forge-mvc-iot/forge_mvc_iot/storage/events.py
```

API exposée :

| Symbole | Type | Rôle |
|---------|------|------|
| `TABLE_NAME` | `str` | nom canonique de la table SQL (`"iot_events"`) |
| `COLUMNS` | `tuple[str, ...]` | ordre canonique des colonnes (sans `id`) |
| `INSERT_IOT_EVENT_SQL` | `str` | requête `INSERT` avec placeholders `?` |
| `serialize_measurement_for_storage(measurement, *, received_at=None)` | `dict[str, object]` | dict prêt à insertion |
| `build_insert_iot_event_sql(measurement, *, received_at=None)` | `tuple[str, tuple]` | `(sql, params)` |

## Schéma SQL cible

La migration versionnée est livrée comme **ressource embarquée** du
package depuis `IOT-PACKAGE-DATA-MIGRATIONS-001` :

```text
packages/forge-mvc-iot/forge_mvc_iot/migrations/20260528120000_create_iot_events.sql
```

Elle est déclarée dans `pyproject.toml` via
`[tool.setuptools.package-data]` pour voyager avec la distribution
PyPI. Lecture côté code Python :

```python
from importlib import resources

migration = (
    resources.files("forge_mvc_iot")
    / "migrations"
    / "20260528120000_create_iot_events.sql"
)
content = migration.read_text(encoding="utf-8")
```

La migration utilise `CREATE TABLE IF NOT EXISTS` (idempotente) et
reproduit exactement le schéma ci-dessous. Le contrat Python
(`COLUMNS`) reste la source de vérité : le test
`tests/test_iot_storage_migration_001.py::TestMigrationMirrorsPythonContract`
vérifie que les colonnes du DDL correspondent à l'ordre canonique
Python.

L'application réelle de la migration (`forge migration:apply` après
copie dans `mvc/migrations/` du projet utilisateur) reste à la charge
de l'utilisateur et sera automatisée dans un ticket dédié.

```sql
CREATE TABLE IF NOT EXISTS iot_events (
    id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    site          VARCHAR(64)     NOT NULL,
    device_id     VARCHAR(64)     NOT NULL,
    kind          VARCHAR(64)     NOT NULL,
    value         DOUBLE          NOT NULL,
    unit          VARCHAR(32)     NOT NULL,
    timestamp     VARCHAR(40)     NOT NULL,   -- ISO 8601 UTC, suffixe Z
    metadata_json TEXT            NULL,        -- JSON sérialisé ou NULL
    received_at   DATETIME(6)     NOT NULL,
    PRIMARY KEY (id),
    INDEX idx_iot_events_site_device (site, device_id),
    INDEX idx_iot_events_received_at (received_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

Notes :

- `value` en `DOUBLE` couvre les `int` et `float` du contrat MQTT.
- `timestamp` reste en `VARCHAR(40)` pour préserver la chaîne ISO 8601
  reçue dans le payload. Le consommateur convertit en `DATETIME` quand
  il en a besoin (préserver la valeur d'origine évite les conversions
  silencieuses de fuseau et la perte de microsecondes).
- `metadata_json` en `TEXT NULL` — JSON sérialisé via
  `json.dumps(..., sort_keys=True, ensure_ascii=False)` ou `NULL`.
- `received_at` en `DATETIME(6)` côté serveur (microsecondes).
- Deux index minimaux : couple `(site, device_id)` pour filtrer par
  capteur, `received_at` pour les fenêtres temporelles.

## API Python

### `serialize_measurement_for_storage`

```python
from datetime import UTC, datetime
from forge_mvc_iot.mqtt.contract import Measurement
from forge_mvc_iot.storage.events import serialize_measurement_for_storage

m = Measurement(
    site="atelier",
    device_id="esp32-001",
    kind="temperature",
    value=22.4,
    unit="°C",
    timestamp="2026-05-28T10:00:00Z",
    metadata={"room": "atelier", "sensor": "dht22"},
)

row = serialize_measurement_for_storage(
    m,
    received_at=datetime(2026, 5, 28, 10, 0, 5, tzinfo=UTC),
)
# {
#     'site': 'atelier',
#     'device_id': 'esp32-001',
#     'kind': 'temperature',
#     'value': 22.4,
#     'unit': '°C',
#     'timestamp': '2026-05-28T10:00:00Z',
#     'metadata_json': '{"room": "atelier", "sensor": "dht22"}',
#     'received_at': datetime(2026, 5, 28, 10, 0, 5, tzinfo=UTC),
# }
```

Si `received_at` n'est pas fourni, `datetime.now(UTC)` est utilisé.

Si `measurement.metadata` est `None`, `metadata_json` est `None` (pas
la chaîne `"null"`) — c'est cette valeur qui sera passée au connecteur
SQL pour produire un vrai `NULL`.

### `build_insert_iot_event_sql`

```python
from forge_mvc_iot.storage.events import build_insert_iot_event_sql

sql, params = build_insert_iot_event_sql(m)
# sql = "INSERT INTO iot_events (site, device_id, kind, value, unit, timestamp, metadata_json, received_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
# params = ('atelier', 'esp32-001', 'temperature', 22.4, '°C',
#           '2026-05-28T10:00:00Z',
#           '{"room": "atelier", "sensor": "dht22"}',
#           datetime(..., tzinfo=UTC))
```

Le tuple `params` suit exactement l'ordre de `COLUMNS`. Cette paire
`(sql, params)` est conçue pour être consommée plus tard par :

```python
# Code à venir dans IOT-STORAGE-REPOSITORY-001 :
from core.database.db import execute
execute(sql, params)
```

## Décisions verrouillées

- **Le module reste pur.** Pas d'import de `core.database.db`, pas de
  connexion, pas de migration appliquée. La fonction
  `build_insert_iot_event_sql` produit du SQL textuel + paramètres :
  c'est l'appelant qui exécutera la requête.
- **Le SQL est visible.** `INSERT_IOT_EVENT_SQL` est une chaîne Python
  lisible, conforme à la charte v2 §5 « Garder SQL visible ».
- **Placeholders `?`.** Style qmark, cohérent avec le reste de Forge
  (voir le starter Contacts et `core.database.db.execute`).
- **`received_at` toujours UTC.** Pas de fuseau implicite. `datetime.now(UTC)`
  par défaut, ou injection explicite via le paramètre.
- **`metadata` → JSON.** Sérialisation déterministe
  (`sort_keys=True`) — utile pour les tests, le diff, et la
  réindexation future.
- **`id` exclu des colonnes.** Généré par la base, jamais inséré
  explicitement.

## Tests sans base

Le module est testé entièrement hors ligne :

```python
from forge_mvc_iot.mqtt.contract import Measurement
from forge_mvc_iot.storage.events import (
    INSERT_IOT_EVENT_SQL, build_insert_iot_event_sql,
)

m = Measurement(
    site="atelier", device_id="esp32-001",
    kind="temperature", value=22.4, unit="°C",
    timestamp="2026-05-28T10:00:00Z",
    metadata=None,
)
sql, params = build_insert_iot_event_sql(m)
assert sql == INSERT_IOT_EVENT_SQL
assert params[0] == "atelier"
assert params[6] is None  # metadata_json
```

Aucun MariaDB n'est requis. La validation runtime du schéma viendra
avec la migration appliquée.

## Repository d'insertion

Le repository est la première couche qui **exécute réellement le SQL**.
Il ne crée pas la table — il suppose que la migration `iot_events` a
déjà été appliquée.

Module : `forge_mvc_iot.storage.repository` — exporté par
`forge_mvc_iot.storage`.

```python
from forge_mvc_iot.storage import IotEventRepository

repo = IotEventRepository()                  # adapter par défaut : core.database.db
result = repo.insert(measurement)            # exécute INSERT_IOT_EVENT_SQL via db.execute(...)
```

### Adapter injectable

Le repository accepte n'importe quel objet exposant
`execute(sql, params)`. Par défaut, il utilise `core.database.db` —
qui gère le pool de connexions, le commit et le rollback
automatiquement (voir `core/database/db.py`).

Pour les tests, on injecte un `MagicMock` (aucun MariaDB requis) :

```python
from unittest.mock import MagicMock
from forge_mvc_iot.storage import IotEventRepository

adapter = MagicMock()
repo = IotEventRepository(db_adapter=adapter)
repo.insert(measurement)
adapter.execute.assert_called_once()
```

Pour récupérer le `lastrowid` plutôt que le `rowcount`, on enveloppe
soi-même `core.database.db.insert` :

```python
from core.database import db

class _InsertAdapter:
    def execute(self, sql, params):
        return db.insert(sql, params)  # retourne lastrowid

repo = IotEventRepository(db_adapter=_InsertAdapter())
new_id = repo.insert(measurement)
```

### Flux complet (subscriber → repository → base)

```text
subscriber.handle_message(topic, payload)
        │
        │  parse_message(topic, payload)
        ▼
   Measurement
        │
        │  repo.insert(measurement, received_at=...)
        ▼
   build_insert_iot_event_sql(...)  →  (sql, params)
        │
        │  db_adapter.execute(sql, params)
        ▼
   iot_events
```

> **Le branchement automatique** `on_measurement=repo.insert` reste
> **un exemple documentaire**. Le subscriber ne tire pas le repository
> dans son code ; c'est le code applicatif qui décide explicitement de
> connecter les deux :
>
> ```python
> repo = IotEventRepository()
> sub = MqttSubscriber(cfg, on_measurement=repo.insert)
> sub.connect()
> sub.loop_forever()
> ```

### Comportement

- Les erreurs SQL sont **propagées telles quelles** — le repository
  n'intercepte rien silencieusement.
- Aucun `commit` ou `rollback` manuel — c'est l'adapter (par défaut
  Forge) qui s'en charge.
- Le `id` n'est pas retourné par défaut (puisque `db.execute` renvoie
  `rowcount`). Utiliser le pattern d'adapter ci-dessus pour récupérer
  `lastrowid`.

### Méthodes de lecture

Trois méthodes pour interroger la table, toutes paramétrées et toutes
testables via le même adapter (`fetch_one`/`fetch_all`) :

```python
repo.list_recent(limit=100)
repo.find_by_device("atelier", "esp32-001", limit=100)
repo.count_by_device("atelier", "esp32-001")
```

Chaque ligne retournée par `list_recent` et `find_by_device` est un
dict **prêt à consommer** :

```python
{
    "id": 42,
    "site": "atelier",
    "device_id": "esp32-001",
    "kind": "temperature",
    "value": 22.4,
    "unit": "°C",
    "timestamp": "2026-05-28T10:00:00Z",
    "metadata": {"room": "atelier", "sensor": "dht22"},   # ou None
    "received_at": datetime(2026, 5, 28, 10, 0, 5, tzinfo=UTC),
}
```

Notes :

- `metadata_json` (interne stockage) est automatiquement parsé en
  `metadata` (dict ou `None`). Le consommateur n'a jamais à voir le
  JSON sérialisé.
- `received_at` reste un `datetime` tel que retourné par le connecteur
  MariaDB (UTC). La conversion en chaîne JSON-friendly sera le travail
  de la future API HTTP.
- L'ordre est `received_at DESC` — les événements les plus récents en
  premier.

### Limites et validation

- `limit` doit être un `int` strict dans `1..MAX_LIMIT` (par défaut
  `MAX_LIMIT = 1000`). Hors plage → `ValueError`. Type incorrect →
  `TypeError`. `True`/`False` sont refusés bien qu'ils héritent de
  `int`.
- Pas de pagination par offset à ce ticket — un appel qui voudrait
  paginer au-delà de `MAX_LIMIT` est probablement le signe qu'il faut
  un autre endpoint (agrégat, filtre temporel, etc.).
- Aucun filtre temporel exposé pour l'instant (`since=`, `until=`).
  Sera ajouté avec l'API HTTP si nécessaire.

### SQL exposé

Les requêtes de lecture sont publiques pour rester lisibles
(charte v2 §5) :

```python
from forge_mvc_iot.storage import (
    SELECT_IOT_EVENTS_RECENT_SQL,
    SELECT_IOT_EVENTS_BY_DEVICE_SQL,
    COUNT_IOT_EVENTS_BY_DEVICE_SQL,
)
```

Toutes utilisent les placeholders qmark `?` (cohérent avec le reste
de Forge) et la table `iot_events`.

## Hors périmètre de ce ticket
- **Pas d'API HTTP** — lecture JSON par `IOT-HTTP-API-001`.
- **Pas de CLI**, pas de dashboard, pas d'intégration Forge Design.
- **Pas de rétention long terme**, pas d'agrégation, pas de
  downsampling, pas d'alertes.

Ces points feront chacun l'objet d'un ticket dédié — voir
[Architecture Forge IoT](architecture.md#tickets-suivants).

## Découpage rappelé

```text
IOT-STORAGE-EVENTS-001            contrat SQL + sérialisation   ← livré
IOT-STORAGE-MIGRATION-001         migration versionnée           ← livré
IOT-STORAGE-REPOSITORY-001        insertion réelle en base       ← livré
IOT-STORAGE-REPOSITORY-READ-001   lectures repository            ← livré
IOT-HTTP-API-001                  lecture HTTP JSON              (à venir)
```
