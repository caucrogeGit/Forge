# Opt-in Forge IoT — branchement local

Ce dossier **branche** le paquet opt-in `forge-mvc-iot` dans ce projet.
Le code métier vit dans le paquet ; ici, uniquement le câblage local.

## Ce que branche cet opt-in

`optins/iot/routes.py` appelle `register_iot_routes(router)`, qui expose
l'**API HTTP IoT en lecture seule** :

- `GET /api/iot/events`
- `GET /api/iot/events/{site}/{device_id}`
- `GET /api/iot/devices/{site}/{device_id}/count`

Le branchement est **explicite** : `mvc/routes.py` appelle
`register_optins(router)` → `optins/registry.py` → `optins/iot/routes.py`.
Aucune découverte automatique.

## Migration à installer

La table `iot_events` est nécessaire pour stocker les mesures :

```bash
forge iot:init          # copie la migration vers mvc/migrations/
forge migration:apply   # crée la table iot_events
```

Voir aussi `optins/iot/migrations/README.md`.

## Commandes utiles

```bash
forge iot:doctor          # diagnostic (config, package, migration, API)
forge iot:doctor --db     # vérifier la table iot_events
forge iot:doctor --mqtt   # vérifier le broker MQTT
forge iot:listen          # écouter le broker et stocker
forge iot:simulate --profile temperature --count 3
```

## Documentation complète

La doc de référence reste **officielle** (pas dupliquée ici) :
<https://forgemvc.com/docs/forge/iot/>.
