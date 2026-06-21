# La configuration IoT dans Forge

Ce document décrit la configuration du module IoT, lue depuis l'environnement.

Le fichier de code correspondant est `forge_mvc_iot/config.py`.

## 1. À quoi sert ce module ?

Le module IoT a besoin de savoir comment joindre le broker MQTT, quel topic écouter, et comment sécuriser l'accès.
`IotConfig` rassemble ces réglages, **immuables**, lus depuis l'environnement.

## 2. L'objet `IotConfig`

| Attribut | Rôle |
|---|---|
| `mqtt_host`, `mqtt_port` | adresse du broker MQTT |
| `mqtt_topic` | topic souscrit |
| `mqtt_client_id` | identifiant client MQTT |
| `mqtt_username`, `mqtt_password` | identifiants MQTT (optionnels) |
| `api_token` | jeton facultatif protégeant l'API HTTP de lecture |
| `mqtt_tls_enabled` | active TLS sur la connexion MQTT |
| `mqtt_tls_ca_file` | certificat d'autorité pour TLS |

## 3. Charger la configuration

```python
from forge_mvc_iot.config import load_iot_config

config = load_iot_config()
```

`load_iot_config(env=None)` lit `os.environ` par défaut ; un mapping peut être injecté pour les tests.

## 4. Contextes d'utilisation

- **Subscriber** : fournir le `config` à `MqttSubscriber`.
- **API HTTP** : `api_token` protège les routes de lecture.

## 5. Voir aussi

- [Le subscriber MQTT](mqtt_subscriber.md) : consomme la configuration.
- [La configuration TLS](mqtt_tls.md) : applique `mqtt_tls_*`.
- [Configuration (guide)](../configuration.md) : la liste détaillée des variables.
