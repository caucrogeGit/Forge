# IoT (opt-in)

Le sujet **IoT (opt-in)** regroupe les starters d'entrée dans
l'écosystème [`forge-mvc-iot`](../../iot/architecture.md), le module
opt-in de Forge dédié à la réception et l'exposition de données IoT.

Comme tout opt-in Forge, IoT n'est **jamais** chargé automatiquement :
le projet le branche explicitement via la couche `optins/`, sans
découverte magique (voir
[structure des opt-ins](../../architecture/optins-project-structure.md)).

## Parcours

| Niveau | Starter | Objectif |
|--------|---------|----------|
| Premier contact | [Bonjour IoT — `welcome-optin-iot`](welcome-optin-iot.md) | Quatre routes de lecture, configuration inspectée (mot de passe masqué), branchement opt-in explicite — sans broker MQTT ni table créée. |

Un seul niveau pour l'instant ; le parcours s'étoffera au fil des
tickets IoT (voir [Architecture Forge IoT](../../iot/architecture.md)).

## Pour aller plus loin

- [Configuration Forge IoT](../../iot/configuration.md)
- [Diagnostic `forge iot:doctor`](../../iot/doctor.md)
- [API HTTP Forge IoT](../../iot/http-api.md)
- [Forge IoT pour Bac Pro / BTS CIEL](../../iot/bts-ciel.md)
