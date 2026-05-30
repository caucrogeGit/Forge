# forge-mvc-iot

Module **opt-in** pour Forge MVC — réception et exposition de données IoT
(capteurs, périphériques connectés) via MQTT. Le module reçoit la
télémétrie depuis un broker MQTT, la stocke en base (SQL visible) et
l'expose via une API HTTP JSON en lecture seule.

## Statut

**Alpha** (`Development Status :: 3 - Alpha`). Le module est fonctionnel
de bout en bout pour un usage local et pédagogique. Les briques
suivantes sont implémentées :

- subscriber MQTT (`paho-mqtt`) avec contrat de message validé ;
- stockage des événements dans la table `iot_events` (migration SQL
  embarquée) ;
- API HTTP JSON en lecture seule, protection Bearer optionnelle ;
- commandes CLI `forge iot:doctor`, `iot:init`, `iot:listen`,
  `iot:simulate` ;
- TLS MQTT optionnel.

Limites Alpha assumées : pas de JWT/OAuth/RBAC sur l'API (Bearer global
uniquement), pas de politique de rétention sur `iot_events`, rate-limit
non distribué. Voir la section « Limites ».

## Décisions verrouillées

- **Forge Core reste indépendant.** `forge-mvc` ne dépend jamais de
  `forge-mvc-iot`. La présence ou l'absence du module IoT ne change
  rien au fonctionnement du framework.
- **`forge-mvc-iot` dépend de Forge Core.** Le module réutilise
  routeur, contrôleurs, accès base de données, conventions
  applicatives.
- **MQTT est le protocole d'entrée**, pas une API front. Mosquitto est
  le broker recommandé en environnement local (BTS CIEL, ateliers
  pédagogiques) ; un broker MQTT cloud reste possible.
- **Forge Design IoT consomme l'API HTTP JSON exposée par Forge**
  (via ce module), jamais directement le broker MQTT.

Voir
[Architecture Forge IoT](https://forgemvc.com/docs/forge/iot/architecture/)
pour la doctrine complète et les règles de séparation.

## Installation

```bash
pip install forge-mvc-iot
```

Depuis le monorepo, en mode développement :

```bash
pip install -e packages/forge-mvc-iot
```

La dépendance `paho-mqtt` est installée automatiquement.

## Configuration

Le module lit sa configuration depuis l'environnement
(`load_iot_config()`), avec des valeurs par défaut adaptées à un broker
local :

| Variable | Défaut | Rôle |
|---|---|---|
| `FORGE_IOT_MQTT_HOST` | `localhost` | hôte du broker MQTT |
| `FORGE_IOT_MQTT_PORT` | `1883` | port du broker |
| `FORGE_IOT_MQTT_TOPIC` | `forge/+/+/telemetry` | topic d'abonnement |
| `FORGE_IOT_MQTT_CLIENT_ID` | `forge-iot` | identifiant client MQTT |
| `FORGE_IOT_MQTT_USERNAME` | _(aucun)_ | authentification broker (optionnelle) |
| `FORGE_IOT_MQTT_PASSWORD` | _(aucun)_ | authentification broker (optionnelle) |
| `FORGE_IOT_MQTT_TLS_ENABLED` | `false` | active TLS vers le broker |
| `FORGE_IOT_MQTT_TLS_CA_FILE` | _(aucun)_ | CA pour la vérification TLS |
| `FORGE_IOT_API_TOKEN` | _(aucun)_ | si défini, exige `Authorization: Bearer <token>` sur l'API |

## Commandes CLI

- `forge iot:doctor` — diagnostic **statique** par défaut (config,
  package, présence de la migration). Options explicites :
  `--db` (teste `iot_events` en base) et `--mqtt` (connexion brève au
  broker).
- `forge iot:init` — copie la migration SQL embarquée vers
  `mvc/migrations/` du projet. **Aucune exécution SQL**, idempotente ;
  puis lancer `forge migration:apply`.
- `forge iot:listen` — relie le flux local
  `broker → MqttSubscriber → IotEventRepository.insert() → iot_events`.
- `forge iot:simulate` — publie des mesures factices conformes au
  contrat MQTT sur `forge/{site}/{device_id}/telemetry`, sans capteur
  physique (pédagogique).

Flux complet de démonstration :

```text
forge iot:doctor --mqtt  →  forge iot:simulate  →  forge iot:listen
  →  iot_events  →  GET /api/iot/events
```

## API HTTP

Branchement **explicite** dans `mvc/routes.py` (jamais automatique) :

```python
from forge_mvc_iot import register_iot_routes

register_iot_routes(router)
```

Routes exposées (GET, lecture seule, JSON) :

| Route | Rôle |
|---|---|
| `GET /api/iot/events` | derniers événements (paramètre `limit`) |
| `GET /api/iot/events/{site}/{device_id}` | événements d'un device |
| `GET /api/iot/devices/{site}/{device_id}/count` | nombre d'événements |

**Sécurité** : si `FORGE_IOT_API_TOKEN` est défini, les trois routes
exigent `Authorization: Bearer <token>` (comparaison en temps constant
via `secrets.compare_digest`). Sinon l'API est ouverte — acceptable en
atelier local, à proscrire en production publique.

## Limites

- Authentification API globale (Bearer unique) : pas de scope par site,
  par device, ni de rotation de clé.
- Pas de politique de rétention / purge / agrégation sur `iot_events`.
- Rate-limit non distribué.
- API en **lecture seule** : aucune écriture/commande device via HTTP.

## Licence

LicenseRef-Forge-Proprietary — voir le dépôt Forge pour les conditions
complètes.
