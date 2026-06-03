# Bilan — niveau intermédiaire (IoT)

Récapitulatif des compétences acquises au **niveau intermédiaire** de la
progression *Bonjour Forge IoT*. Ce niveau fait passer de la lecture à une
petite chaîne **alimenter → exposer → afficher**, toujours en simulation locale.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1 — [Simuler une mesure IoT](iot-simulate.md) | Composer, valider (`parse_message`) et insérer (`IotEventRepository.insert`) une mesure **sans broker**. |
| 2 — [Exposer l'API IoT](iot-api.md) | Brancher l'API HTTP JSON officielle (`register_iot_routes`), trois routes en lecture seule, Bearer optionnel. |

Vous savez maintenant alimenter `iot_events` en local et exposer ces données via
l'API officielle, sans infrastructure MQTT.

## Et ensuite

Le récapitulatif rassemble toutes les API IoT de la progression sur une seule
page.

[Récapitulatif de la progression IoT](../recapitulatif.md)
