# Le subscriber MQTT

Objectif : recevoir les mesures d'un **vrai broker MQTT**, en temps réel.

**Ce que vous allez apprendre :** le chemin de production complet. Un broker
pousse les messages ; `forge iot:listen` lance un `MqttSubscriber` qui, pour
chaque message, **valide** (`parse_message`) puis **stocke**
(`IotEventRepository.insert`). C'est l'aboutissement de la progression : les
mêmes données qu'en simulation, mais venues d'un vrai capteur.

Palier 2 du **niveau avancé** de la progression IoT, après
[Valider un message IoT](iot-contract.md).

!!! note "Infrastructure requise"
    Recevoir de vrais messages demande un **broker MQTT** (par exemple Mosquitto)
    démarré et atteignable, à votre charge. Ce starter explique et câble le
    chemin ; il ne fournit pas le broker.

## Ce que ce starter montre

- la chaîne réelle : `Mosquitto → forge iot:listen → MqttSubscriber → parse_message → insert` ;
- une route qui affiche la **configuration broker effective** (hôte, topic, TLS)
  pour la vérifier avant de lancer le subscriber ;
- la commande officielle `forge iot:listen`.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_iot.config.load_iot_config` | Lire la configuration broker à vérifier. | [Forge IoT : configuration](../../configuration.md) |
| `forge iot:listen` (CLI) | Lancer le `MqttSubscriber` sur le broker. | [Forge IoT : listen](../../listen-command.md) |
| `MqttSubscriber` | Recevoir, valider et stocker chaque message. | [Forge IoT : architecture](../../architecture.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/iot-subscriber` : la page récapitule le broker, le
topic et l'état TLS. Puis, avec un broker démarré :

```bash
forge iot:listen
```

Le subscriber se connecte, s'abonne au topic et stocke chaque message reçu.
Consultez-les via le [tableau de bord](../intermediaire/iot-dashboard.md) ou
l'[API JSON](../intermediaire/iot-api.md).

## Le contrôleur

Créez le fichier ci-dessous, complet et copiable tel quel.

```python
# mvc/controllers/iot_subscriber_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_iot.config import load_iot_config


class IotSubscriberController(BaseController):
    """Starter pédagogique : visualiser la config broker avant `iot:listen`."""

    @staticmethod
    def index(request: Request) -> Response:
        cfg = load_iot_config()
        return BaseController.render(
            "iot_subscriber/index.html",
            context={
                "broker": f"{cfg.mqtt_host}:{cfg.mqtt_port}",
                "topic": cfg.mqtt_topic,
                "tls_enabled": cfg.mqtt_tls_enabled,
            },
            request=request,
        )
```

### Comprendre ce code

- La route **ne lance pas** le subscriber : recevoir en continu est le rôle d'une
  commande CLI (`forge iot:listen`), pas d'une requête web. La route sert à
  **vérifier la configuration** avant de lancer.
- Le `MqttSubscriber` (utilisé par `forge iot:listen`) applique **le même**
  `parse_message` que le palier précédent : le contrat est le point d'entrée
  unique, qu'on simule ou qu'on reçoive pour de vrai.
- En TLS, `load_iot_config` expose `mqtt_tls_enabled` et le fichier CA : la
  connexion sécurisée est explicite, jamais devinée.

## La vue

Créez le gabarit ci-dessous : il récapitule la configuration de connexion et
rappelle la commande d'écoute.

```html
<!-- mvc/views/iot_subscriber/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Le subscriber MQTT — Forge</title>
</head>
<body>
  <h1>Le subscriber MQTT</h1>

  <h2>Configuration de connexion</h2>
  <ul>
    <li>Broker : <code>{{ broker }}</code></li>
    <li>Topic : <code>{{ topic }}</code></li>
    <li>TLS : {% if tls_enabled %}activé{% else %}désactivé{% endif %}</li>
  </ul>

  <h2>Recevoir de vrais messages</h2>
  <p>Avec un broker MQTT démarré et atteignable, lancez le subscriber :</p>
  <pre>forge iot:listen</pre>
  <p>
    Chaque message reçu est validé contre le contrat puis stocké dans
    <code>iot_events</code>. Consultez-les ensuite via le tableau de bord ou
    l'API JSON.
  </p>
</body>
</html>
```

## La route

Déclarez la route dans `mvc/routes.py`, à l'intérieur du groupe public.

```python
# mvc/routes.py
from mvc.controllers.iot_subscriber_controller import IotSubscriberController

with router.group("", public=True) as public:
    public.add("GET", "/iot-subscriber", IotSubscriberController.index, name="iot_subscriber_index")
```

## À retenir

- Le temps réel passe par un **broker** + `forge iot:listen` (un `MqttSubscriber`).
- Le subscriber **valide puis stocke** chaque message : même contrat qu'en
  simulation.
- Une route web vérifie la config ; l'écoute continue est une commande CLI.

## Après ce starter

Vous recevez les vraies données. Dernier palier : diagnostiquer le module quand
quelque chose cloche.

[Diagnostiquer le module IoT](iot-doctor.md)
