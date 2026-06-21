# Exemple ESP32 pour Forge IoT

> **Statut** : exemple **pédagogique**. Il montre comment un microcontrôleur
> **ESP32** publie une mesure conforme au contrat MQTT Forge IoT. C'est un
> exemple de code, pas une dépendance Forge : Forge reste un framework web,
> pas un outil Arduino.

## Objectif

Remplacer le simulateur (`forge iot:simulate`) par un **vrai capteur** :
un ESP32 qui publie une température sur le topic Forge IoT, ingérée
ensuite par `forge iot:listen` et lisible via l'API HTTP.

```text
ESP32  →  MQTT  →  Mosquitto  →  forge iot:listen  →  iot_events  →  /api/iot/events
```

## Matériel nécessaire

- une carte **ESP32** (DevKit, WROOM…) ;
- un câble USB ;
- optionnel : un capteur de température réel (DHT22, DS18B20…) — sinon
  l'exemple publie une valeur fixe.

## Pré-requis

- l'**IDE Arduino** (ou PlatformIO) avec le **coeur ESP32** installé ;
- la bibliothèque **PubSubClient** (Nick O'Leary) installée via le
  gestionnaire de bibliothèques ;
- un **broker Mosquitto** joignable sur le réseau local — voir
  [Mosquitto local](mosquitto-local.md) ;
- un projet **Forge** avec `forge-mvc-iot` installé.

## Contrat MQTT Forge IoT

L'ESP32 doit publier exactement sur :

```text
forge/{site}/{device_id}/telemetry
```

Exemple utilisé ici :

```text
forge/atelier/esp32-001/telemetry
```

Avec un payload JSON conforme :

```json
{
  "kind": "temperature",
  "value": 22.4,
  "unit": "°C",
  "timestamp": "2026-05-29T10:00:00Z"
}
```

Le `timestamp` est en **UTC**, suffixe `Z` — l'exemple l'obtient par NTP.

## Code ESP32 minimal

Le sketch complet est ici :
[`esp32_mqtt_temperature.ino`](examples/esp32_mqtt_temperature.ino).

Extrait — les paramètres à adapter et la publication :

```cpp
#include <WiFi.h>
#include <PubSubClient.h>

const char* WIFI_SSID     = "CHANGE_ME";
const char* WIFI_PASSWORD = "CHANGE_ME";
const char* MQTT_HOST     = "192.168.1.222";   // IP du PC qui héberge Mosquitto
const int   MQTT_PORT     = 1883;

const char* MQTT_TOPIC = "forge/atelier/esp32-001/telemetry";

// ... dans loop() :
snprintf(payload, sizeof(payload),
  "{\"kind\":\"temperature\",\"value\":%.1f,\"unit\":\"°C\",\"timestamp\":\"%s\"}",
  value, timestamp.c_str());
mqtt.publish(MQTT_TOPIC, payload);
```

## Adapter le Wi-Fi

Remplace `WIFI_SSID` et `WIFI_PASSWORD` par les identifiants de ton
réseau. L'ESP32 et le PC qui héberge Mosquitto doivent être sur le
**même réseau**.

## Adapter l'adresse du broker MQTT

`MQTT_HOST` doit pointer vers l'**adresse IP** du poste qui fait tourner
Mosquitto — surtout **pas** `localhost` (qui désignerait l'ESP32
lui-même). Trouve l'IP du PC, par exemple :

```bash
ip addr | grep 'inet '
```

puis mets-la dans `MQTT_HOST` (ex. `192.168.1.222`).

## Lancer Mosquitto

```bash
sudo systemctl status mosquitto
forge iot:doctor --mqtt
```

Détail : [Mosquitto local](mosquitto-local.md).

## Lancer Forge IoT

Côté serveur, prépare le stockage puis écoute :

```bash
forge iot:init
forge migration:apply
forge iot:doctor --db
forge iot:listen
```

## Vérifier la réception

Téléverse le sketch sur l'ESP32. Dans le terminal `forge iot:listen`,
des lignes `[OK]` doivent apparaître à chaque message. Vérifie ensuite
l'API HTTP (application lancée via `forge run`) :

```bash
curl http://localhost:8000/api/iot/events
```

Tu peux aussi observer le trafic brut :

```bash
mosquitto_sub -h localhost -t 'forge/+/+/telemetry' -v
```

## Erreurs fréquentes

- **L'ESP32 ne se connecte pas au Wi-Fi** : vérifie SSID/mot de passe et
  que le réseau est en 2,4 GHz (l'ESP32 ne gère pas le 5 GHz) ;
- **Pas de connexion MQTT** : `MQTT_HOST` pointe sur `localhost` au lieu
  de l'IP du PC, ou Mosquitto n'écoute pas (voir
  [Mosquitto local](mosquitto-local.md)) ;
- **Message rejeté par Forge** : topic hors format
  `forge/{site}/{device_id}/telemetry`, ou payload incomplet
  (`kind`/`value`/`unit`/`timestamp` obligatoires) ;
- **Timestamp faux** : NTP pas encore synchronisé — attends quelques
  secondes après la connexion Wi-Fi.

## Limites

Cet exemple reste volontairement simple. Sont **hors périmètre** :

- pas de **TLS** ni d'authentification MQTT ;
- pas de gestion Wi-Fi avancée (reconnexion fine, économie d'énergie) ;
- la bibliothèque PubSubClient est utilisée **comme exemple**, ce n'est
  pas une dépendance de Forge ;
- **Arduino R4 n'est pas couvert ici** (hors périmètre) — ce ticket
  cible l'ESP32, la cible la plus simple et la plus standard pour MQTT.
  Voir l'[évaluation Arduino R4](arduino-r4-assessment.md) pour l'état de
  cette piste.
