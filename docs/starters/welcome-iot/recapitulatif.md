# Aide-mémoire de la progression IoT

Récapitulatif des paliers de la progression *Bonjour Forge IoT* et des API du
module opt-in `forge-mvc-iot` introduites à chaque étape.

!!! note "Module opt-in"
    Toute cette progression suppose `forge-mvc-iot` installé
    (`forge opt-in:install iot`). Le cœur de Forge reste autonome.

## Niveau débutant — découvrir (lecture, sans broker)

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Bonjour Forge IoT](debutant/iot-welcome.md) | Vérifier le module, inspecter la config (secret masqué) | `load_iot_config` |
| 2 | [Lire les événements IoT](debutant/iot-events.md) | Lire les derniers événements, rester pédagogique si la table manque | `IotEventRepository.list_recent` |
| 3 | [Les événements d'un capteur](debutant/iot-device.md) | Cibler un capteur et compter ses événements | `find_by_device`, `count_by_device` |

## Niveau intermédiaire — alimenter & exposer (simulation locale)

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Simuler une mesure IoT](intermediaire/iot-simulate.md) | Composer, valider et insérer une mesure sans broker | `build_payload`, `parse_message`, `IotEventRepository.insert` |
| 2 | [Exposer l'API IoT](intermediaire/iot-api.md) | Brancher l'API HTTP JSON officielle (lecture seule, Bearer optionnel) | `register_iot_routes` |

## Configuration (`forge_mvc_iot.config`)

| Élément | Usage |
|---------|-------|
| `load_iot_config()` | Lire la configuration MQTT (hôte, port, topic, identifiants, token API) |

Un secret (mot de passe, token) est **toujours masqué** quand la config est
sérialisée.

## Stockage (`forge_mvc_iot.storage`)

| Élément | Usage |
|---------|-------|
| `IotEventRepository()` | Accès aux événements stockés (utilise `core.database.db` par défaut) |
| `repo.list_recent(limit=…)` | Derniers événements, ordre du plus récent |
| `repo.find_by_device(site, device_id, limit=…)` | Événements d'un capteur précis |
| `repo.count_by_device(site, device_id)` | Nombre d'événements d'un capteur |
| `repo.insert(measurement)` | Écrire une mesure validée dans `iot_events` |

## Contrat & simulation (`forge_mvc_iot.mqtt.contract`, `forge_mvc_iot.cli.simulate`)

| Élément | Usage |
|---------|-------|
| `build_topic(site, device_id)` / `build_payload(...)` | Composer un topic et un payload conformes |
| `parse_message(topic, payload)` | Valider → `Measurement` (lève `ContractError` sinon) |

## API HTTP officielle (`forge_mvc_iot`)

| Élément | Usage |
|---------|-------|
| `register_iot_routes(router)` | Brancher l'API JSON officielle (3 routes lecture seule) |
| `FORGE_IOT_API_TOKEN` | Si défini, exige `Authorization: Bearer <token>` |
