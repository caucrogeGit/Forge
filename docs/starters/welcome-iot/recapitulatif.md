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

## Configuration (`forge_mvc_iot.config`)

| Élément | Usage |
|---------|-------|
| `load_iot_config()` | Lire la configuration MQTT (hôte, port, topic, identifiants, token API) |

Un secret (mot de passe, token) est **toujours masqué** quand la config est
sérialisée.
