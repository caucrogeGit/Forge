# Bilan — niveau avancé (IoT)

Récapitulatif des compétences acquises au **niveau avancé** de la progression
*Bonjour Forge IoT*. Ce niveau **bascule vers le réel** : contrat des messages,
subscriber MQTT branché sur un vrai broker, et diagnostic du module.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1 — [Valider un message IoT](iot-contract.md) | Comprendre et appliquer le contrat des messages (`parse_message`, `ContractError`). |
| 2 — [Le subscriber MQTT](iot-subscriber.md) | Recevoir d'un vrai broker via `forge iot:listen` (`MqttSubscriber` : valider puis stocker). |
| 3 — [Diagnostiquer le module IoT](iot-doctor.md) | Vérifier la santé du module (`forge iot:doctor`, contrôles non invasifs exposés en JSON). |

Vous savez maintenant ce qu'un message réel doit respecter, comment le recevoir
d'un vrai broker et comment diagnostiquer le module en exploitation.

## Et ensuite

Le récapitulatif rassemble toutes les API IoT de la progression sur une seule
page.

[Récapitulatif de la progression IoT](../recapitulatif.md)
