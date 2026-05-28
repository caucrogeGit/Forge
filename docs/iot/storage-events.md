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

## Schéma SQL cible (informatif)

La migration qui sera produite dans `IOT-STORAGE-MIGRATION-001` créera
la table suivante. Elle est documentée ici pour figer le contrat ; ce
ticket **n'applique aucune migration**.

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

## Hors périmètre de ce ticket

- **Pas de migration SQL** — fichier `mvc/migrations/*.sql` à produire
  par `IOT-STORAGE-MIGRATION-001`.
- **Pas d'insertion réelle** — branchement à `core.database.db.execute`
  par `IOT-STORAGE-REPOSITORY-001`.
- **Pas d'API HTTP** — lecture JSON par `IOT-HTTP-API-001`.
- **Pas de CLI**, pas de dashboard, pas d'intégration Forge Design.
- **Pas de rétention long terme**, pas d'agrégation, pas de
  downsampling, pas d'alertes.

Ces points feront chacun l'objet d'un ticket dédié — voir
[Architecture Forge IoT](architecture.md#tickets-suivants).

## Découpage rappelé

```text
IOT-STORAGE-EVENTS-001        contrat SQL + sérialisation  ← ce ticket
IOT-STORAGE-MIGRATION-001     migration versionnée
IOT-STORAGE-REPOSITORY-001    insertion réelle en base
IOT-HTTP-API-001              lecture HTTP JSON
```
