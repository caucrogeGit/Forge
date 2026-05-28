# forge-mvc-iot

Module **opt-in** pour Forge MVC — préparation de la réception et de
l'exposition de données IoT (capteurs, périphériques connectés) via
MQTT.

## Statut

**Squelette initial.** Ce package est posé pour fixer la trajectoire
de Forge IoT. Aucune logique fonctionnelle n'est encore implémentée :

- pas de subscriber MQTT ;
- pas de dépendance `paho-mqtt` ;
- pas de stockage SQL ;
- pas de routes HTTP ;
- pas de commande CLI `forge iot:*`.

L'implémentation viendra par tickets successifs — voir
[Tickets suivants](https://forgemvc.com/docs/forge/iot/architecture/#tickets-suivants)
dans la page d'architecture officielle.

## Décisions verrouillées

- **Forge Core reste indépendant.** `forge-mvc` ne dépend jamais de
  `forge-mvc-iot`. La présence ou l'absence du module IoT ne change
  rien au fonctionnement du framework.
- **`forge-mvc-iot` dépend de Forge Core.** Le module réutilise
  routeur, contrôleurs, accès base de données, conventions
  applicatives.
- **MQTT est le premier protocole supporté** (à implémenter).
- **Mosquitto** sera le broker MQTT recommandé en environnement local
  (BTS CIEL, ateliers pédagogiques). Un broker MQTT cloud reste
  possible mais non prioritaire.
- **Forge Design IoT consommera l'API HTTP JSON exposée par Forge**
  (via ce module), jamais directement le broker MQTT.

Voir
[Architecture Forge IoT](https://forgemvc.com/docs/forge/iot/architecture/)
pour la doctrine complète et les règles de séparation.

## Installation (futur)

À terme :

```bash
pip install forge-mvc-iot
```

Aujourd'hui, le package est installable depuis le monorepo en mode
développement :

```bash
pip install -e packages/forge-mvc-iot
```

mais il n'expose encore aucune API publique fonctionnelle.

## Structure

```text
packages/forge-mvc-iot/
├── pyproject.toml
├── README.md
└── forge_mvc_iot/
    ├── __init__.py
    ├── mqtt/         # futur subscriber MQTT (vide)
    ├── storage/      # futur stockage des événements IoT (vide)
    └── diagnostics/  # futur forge iot:doctor (vide)
```

## Licence

LicenseRef-Forge-Proprietary — voir le dépôt Forge pour les conditions
complètes.
