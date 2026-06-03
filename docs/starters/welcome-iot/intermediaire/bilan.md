# Bilan — niveau intermédiaire (IoT)

Récapitulatif des compétences acquises au **niveau intermédiaire** de la
progression *Bonjour Forge IoT*. Ce niveau fait passer de la lecture à une
petite chaîne **alimenter → exposer → afficher**, toujours en simulation locale.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1 — [Simuler une mesure IoT](iot-simulate.md) | Composer, valider (`parse_message`) et insérer (`IotEventRepository.insert`) une mesure **sans broker**. |
| 2 — [Exposer l'API IoT](iot-api.md) | Brancher l'API HTTP JSON officielle (`register_iot_routes`), trois routes en lecture seule, Bearer optionnel. |
| 3 — [Tableau de bord IoT](iot-dashboard.md) | Afficher les derniers événements dans une page HTML (`list_recent` + `render`). |

Vous savez maintenant alimenter `iot_events` en local, exposer ces données via
l'API officielle et les afficher dans un tableau de bord — sans infrastructure
MQTT.

## Et ensuite

Place au **niveau avancé** : on bascule vers le réel — contrat des messages,
subscriber MQTT branché sur un vrai broker, diagnostic du module.

[Niveau avancé : Valider un message IoT](../avance/iot-contract.md)
