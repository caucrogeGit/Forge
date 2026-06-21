# La configuration TLS MQTT dans Forge IoT

Ce document décrit l'application de TLS sur la connexion MQTT.

Le fichier de code correspondant est `forge_mvc_iot/mqtt/tls.py`.

## 1. À quoi sert ce module ?

Une connexion MQTT en clair expose les mesures sur le réseau.
Ce module applique la configuration **TLS** d'un `IotConfig` sur un client `paho`, pour chiffrer la liaison avec le broker.

## 2. L'API

```python
from forge_mvc_iot.mqtt.tls import configure_tls

configure_tls(client, config)
```

| Fonction | Comportement |
|---|---|
| `configure_tls(client, config)` | applique la configuration TLS de `config` sur le `client` paho |

Si `config.mqtt_tls_enabled` est faux, la fonction n'altère pas le client.
Sinon, elle active TLS, en s'appuyant sur `mqtt_tls_ca_file` quand il est fourni.

## 3. Contextes d'utilisation

- **Subscriber** : appelée à la construction du client MQTT quand TLS est activé.
- **Déploiement** : positionner `mqtt_tls_enabled` et le certificat d'autorité.

## 4. Voir aussi

- [La configuration IoT](config.md) : les réglages `mqtt_tls_*`.
- [Le subscriber MQTT](mqtt_subscriber.md) : le client configuré.
