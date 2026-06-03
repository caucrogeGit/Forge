# Bilan — niveau débutant (IoT)

Récapitulatif des compétences acquises au **niveau débutant** de la progression
*Bonjour Forge IoT*. Ce niveau découvre le module opt-in `forge-mvc-iot` et la
**lecture** des données, sans broker ni infrastructure.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1 — [Bonjour Forge IoT](iot-welcome.md) | Vérifier le module et inspecter sa configuration MQTT (`load_iot_config`), mot de passe masqué. |
| 2 — [Lire les événements IoT](iot-events.md) | Lire les derniers événements (`IotEventRepository.list_recent`) et rester pédagogique (`503`) si la table manque. |
| 3 — [Les événements d'un capteur](iot-device.md) | Cibler un capteur (`find_by_device`) et compter ses événements (`count_by_device`) via une route paramétrée. |

Vous savez maintenant inspecter la configuration du module et lire les
événements stockés — flux global comme capteur précis.

## Et ensuite

Le récapitulatif rassemble toutes les API IoT de la progression sur une seule
page.

[Récapitulatif de la progression IoT](../recapitulatif.md)
