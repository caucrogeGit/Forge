# Exposer l'API IoT

Objectif : exposer les événements IoT via l'**API HTTP JSON officielle** du module, sans écrire de code métier.

**Ce que vous allez apprendre :** `register_iot_routes(router)`.
Une seule ligne branche les trois routes en **lecture seule** de Forge IoT.
Le code vit dans le paquet `forge-mvc-iot` ; votre application ne fait que le **brancher** : c'est le principe « lock + delegate »
de Forge.

Palier 2 du **niveau intermédiaire** de la progression IoT, après [Simuler une mesure IoT](iot-simulate.md).

## Ce que ce starter montre

- le branchement de l'API officielle avec `register_iot_routes(router)` ;
- trois routes JSON en lecture seule :
    - `GET /api/iot/events` : N derniers événements,
    - `GET /api/iot/events/{site}/{device_id}` : événements d'un capteur,
    - `GET /api/iot/devices/{site}/{device_id}/count` : compteur ;
- une **authentification Bearer optionnelle** (`FORGE_IOT_API_TOKEN`).

La table `iot_events` est garantie par la migration livrée.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_iot.register_iot_routes` | Brancher l'API HTTP JSON officielle sur le routeur. | [Forge IoT : API HTTP](../../http-api.md) |

## Tester

```bash
forge db:init
forge run
```

Après avoir injecté quelques mesures (palier précédent), interrogez l'API :

```bash
curl -k https://localhost:8000/api/iot/events
curl -k https://localhost:8000/api/iot/events/atelier/capteur-1
curl -k https://localhost:8000/api/iot/devices/atelier/capteur-1/count
```

Si `FORGE_IOT_API_TOKEN` est défini, ajoutez l'en-tête `Authorization: Bearer <token>` ; sinon l'API reste ouverte (mode local).

## La route

Ce palier n'a **pas** de contrôleur à créer : le code métier des trois routes vit dans le paquet opt-in `forge-mvc-iot`.
Votre application se contente de le **brancher** via `register_iot_routes(router)`, ajouté dans `mvc/routes/__init__.py`.

```python
# mvc/routes/__init__.py
from forge_mvc_iot import register_iot_routes

register_iot_routes(router)
```

L'appel se place au niveau du module de routes (il enregistre lui-même ses chemins sous `/api/iot/…`), pas dans le groupe `public`.

### Comprendre ce code

- `register_iot_routes(router)` enregistre les trois routes officielles d'un coup.
  Vous n'écrivez **aucun** contrôleur : le code métier appartient au paquet, l'application le **branche** explicitement (pas de découverte automatique, principe « refuser la magie cachée »).
- L'authentification est **optionnelle** : pas de token configuré → API ouverte (pratique en local) ; token configuré → `Authorization: Bearer <token>` exigé, sinon `401`.
- L'API est en **lecture seule** : elle expose les événements, elle n'en crée pas.
  L'écriture passe par le subscriber (ou la simulation).

## La migration

L'API officielle lit la table `iot_events`.
Créez le fichier de migration ci-dessous (le nom commence par un horodatage), puis appliquez-le avec `forge db:init`.

```sql
-- mvc/migrations/20260601180000_create_iot_events.sql
CREATE TABLE IF NOT EXISTS iot_events (
    id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    site          VARCHAR(64)     NOT NULL,
    device_id     VARCHAR(64)     NOT NULL,
    kind          VARCHAR(64)     NOT NULL,
    value         DOUBLE          NOT NULL,
    unit          VARCHAR(32)     NOT NULL,
    timestamp     VARCHAR(40)     NOT NULL,
    metadata_json TEXT            NULL,
    received_at   DATETIME(6)     NOT NULL,
    PRIMARY KEY (id),
    INDEX idx_iot_events_site_device (site, device_id),
    INDEX idx_iot_events_received_at (received_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

`CREATE TABLE IF NOT EXISTS` rend la migration idempotente : elle est sûre même si le palier de simulation a déjà créé la table.

## À retenir

- `register_iot_routes(router)` branche l'API officielle en une ligne.
- Le code vit dans le paquet ; l'application **délègue** au lieu de réécrire.
- L'auth Bearer est optionnelle, pilotée par `FORGE_IOT_API_TOKEN`.

## Après ce starter

Vous savez exposer l'API officielle.
La suite : afficher les événements dans une vraie page.

[Tableau de bord IoT](iot-dashboard.md)
