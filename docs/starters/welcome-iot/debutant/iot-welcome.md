# Bonjour Forge IoT

Objectif : premier contact avec le module **opt-in** `forge-mvc-iot` et sa
configuration.

**Ce que vous allez apprendre :** vérifier que le module IoT répond, et
**inspecter sa configuration MQTT** avec `load_iot_config` — en **masquant le mot
de passe**. Aucun broker, aucune base : on découvre simplement comment Forge IoT
est branché.

Premier palier du **niveau débutant** de la progression IoT
([vue d'ensemble des starters](../../index.md#progression-recommandee)).

!!! note "Module opt-in"
    Ce starter suppose le module installé : `forge opt-in:install iot`
    (ou `pip install forge-mvc-iot`). Le cœur de Forge reste autonome ; l'IoT
    est une brique que l'on ajoute à la demande.

## Ce que ce starter montre

- une route texte de **premier contact** (`GET /iot-welcome`) ;
- la lecture de la configuration IoT avec `load_iot_config` ;
- la sérialisation JSON de cette config avec le **mot de passe masqué**.

Aucun broker MQTT, aucune base de données.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_iot.config.load_iot_config` | Lire la configuration MQTT du module IoT. | [Forge IoT](../../../iot/architecture.md) |
| `Response.text` / `Response.json` | Renvoyer du texte puis du JSON. | [Response](../../../reference/api.md#corehttp) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/iot-welcome` : la page affiche
**« Bonjour Forge IoT »**. Puis `https://localhost:8000/iot-welcome/inspect`
renvoie la configuration MQTT en JSON, le mot de passe remplacé par `***`.

## Le contrôleur

```python
# mvc/controllers/iot_welcome_controller.py
from forge_mvc_iot.config import load_iot_config


def _config_to_safe_dict(cfg) -> dict:
    return {
        "mqtt_host": cfg.mqtt_host,
        "mqtt_port": cfg.mqtt_port,
        "mqtt_topic": cfg.mqtt_topic,
        "mqtt_client_id": cfg.mqtt_client_id,
        "mqtt_username": cfg.mqtt_username,
        "mqtt_password": "***" if cfg.mqtt_password else None,
    }


class IotWelcomeController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge IoT")

    @staticmethod
    def inspect(request: Request) -> Response:
        cfg = load_iot_config()
        return Response.json(_config_to_safe_dict(cfg))
```

### Comprendre ce code

- `load_iot_config()` lit la configuration MQTT (hôte, port, topic, identifiants)
  depuis l'environnement Forge — comme le reste de la config Forge, elle est
  **explicite**.
- On ne renvoie **jamais** le mot de passe : `"***" if cfg.mqtt_password else
  None`. Une config exposée masque toujours ses secrets.

## À retenir

- Le module IoT est **opt-in** : on l'installe à la demande, le cœur reste
  autonome.
- `load_iot_config()` donne accès à la configuration MQTT de façon explicite.
- On **masque les secrets** dès qu'une config est sérialisée.

## Après ce starter

Premier contact établi. Faites le point dans le bilan du niveau.

[Bilan du niveau débutant](bilan.md)
