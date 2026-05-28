# Diagnostic Forge IoT — `forge iot:doctor`

> **Statut** : diagnostic **statique** uniquement à ce ticket
> (`IOT-DOCTOR-001`). Les options `--mqtt` (test broker) et `--db`
> (test `iot_events`) sont reportées à des tickets ultérieurs pour ne
> pas mélanger CLI, réseau MQTT et base MariaDB dans une seule
> commande.

## Objectif

Donner un signal **avant** d'exécuter quoi que ce soit côté broker ou
base de données :

- le module `forge-mvc-iot` est bien installé ;
- la configuration `load_iot_config()` est cohérente ;
- la migration `iot_events` est shippée avec le package ;
- l'API HTTP est enregistrable (`register_iot_routes`).

C'est l'étape recommandée **avant** un starter pédagogique
(`IOT-STARTER-MQTT-HELLO-001`) ou un déploiement.

## Usage

```bash
forge iot:doctor
```

Aucune option à ce ticket. Aide via :

```bash
forge iot:doctor --help
```

## Vérifications

| # | Vérification | Statut possible |
|---|--------------|-----------------|
| 1 | Package `forge-mvc-iot` importable (et version) | `ok` / `fail` |
| 2 | `load_iot_config()` chargeable, mot de passe masqué | `ok` / `fail` |
| 3 | Migration `*_create_iot_events.sql` présente dans le package | `ok` / `warn` |
| 4 | `register_iot_routes` exposée | `ok` / `fail` |
| 5 | Broker MQTT — **non testé** | `skip` |
| 6 | Base `iot_events` — **non testée** | `skip` |

### Codes de sortie

| Statut | Comptabilisé | Effet sur le code de sortie |
|--------|--------------|-----------------------------|
| `ok` | succès | aucun |
| `skip` | info | aucun |
| `warn` | avertissement | aucun |
| `fail` | erreur | **exit 1** |

Le doctor exit 0 dès qu'aucun `fail` n'est remonté — un `warn` ou un
`skip` ne casse pas la CI.

## Sortie exemple

```text
Forge IoT doctor

  [OK]    package forge-mvc-iot — installé (version 1.0.0b11)
  [OK]    configuration IoT — chargée
           mqtt_host       : localhost
           mqtt_port       : 1883
           mqtt_topic      : forge/+/+/telemetry
           mqtt_client_id  : forge-iot
           mqtt_username   : (none)
           mqtt_password   : (none)
  [OK]    migration iot_events — présente (20260528120000_create_iot_events.sql)
  [OK]    API HTTP IoT — register_iot_routes disponible
  [SKIP]  broker MQTT — non testé à ce ticket (option --mqtt prévue dans un ticket ultérieur)
  [SKIP]  base iot_events — non testée à ce ticket (option --db prévue dans un ticket ultérieur)

0 avertissement(s), 0 erreur(s), 2 info(s).
```

Avec un username/password configurés :

```text
  [OK]    configuration IoT — chargée
           …
           mqtt_username   : forge
           mqtt_password   : ***
```

Le mot de passe est **toujours masqué** par `***` — c'est le contrat
de [`IotConfig.__repr__`](configuration.md#masquage-du-mot-de-passe)
appliqué uniformément dans le doctor.

## Cas d'erreur typiques

### Configuration invalide

Si `FORGE_IOT_MQTT_HOST` est défini mais vide, par exemple :

```text
  [FAIL]  configuration IoT — FORGE_IOT_MQTT_HOST ne peut pas être vide
```

Idem pour un port hors plage, un topic vide, etc. Voir
[Configuration Forge IoT — erreurs](configuration.md#erreurs-levees).

### Migration manquante

Depuis `IOT-PACKAGE-DATA-MIGRATIONS-001`, le doctor lit la migration
via `importlib.resources.files("forge_mvc_iot") / "migrations"` — la
ressource est embarquée dans le package Python lui-même
(`forge_mvc_iot/migrations/`) et déclarée dans `pyproject.toml`
(`[tool.setuptools.package-data]`).

Si le doctor ne trouve plus la migration, c'est probablement le signe
d'une installation cassée :

```text
  [FAIL]  migration iot_events — aucun *_create_iot_events.sql sous
           forge_mvc_iot/migrations/ — vérifier l'installation
           (pip install -e packages/forge-mvc-iot) et
           [tool.setuptools.package-data] dans pyproject.toml
```

Solution : réinstaller le package (`pip install -e packages/forge-mvc-iot`
ou `pip install --force-reinstall forge-mvc-iot`).

Pour **copier ensuite** la migration dans le projet, voir
[`forge iot:init`](init-command.md) — copie idempotente vers
`mvc/migrations/`, sans exécuter le SQL.

### Module non installé

Si l'utilisateur tape `forge iot:doctor` sans avoir installé
`forge-mvc-iot` :

```text
Erreur : module forge-mvc-iot non installé.
indice : installe le module opt-in : pip install forge-mvc-iot
```

Forge Core reste fonctionnel sans le module — l'import est paresseux
côté dispatcher (`forge.py`).

## Limites de ce ticket

Sont volontairement **hors périmètre** :

- pas de test de connexion au broker MQTT (`tcp connect`,
  `subscribe`) — futur `--mqtt` ;
- pas de test de connexion à la base (`SELECT COUNT(*) FROM
  iot_events`) — futur `--db` ;
- pas de vérification de la version du subscriber MQTT démarré ;
- pas de vérification de la version du contrat MQTT déployé côté
  capteurs ;
- pas d'audit des permissions ACL Mosquitto.

Chacun de ces points peut justifier sa propre option / commande pour
rester lisible et localement testable.

## Tickets suivants

- futur `IOT-DOCTOR-MQTT-001` ajoutera `forge iot:doctor --mqtt` qui
  établit une connexion brève au broker (TCP + auth + un
  `subscribe` test), avec timeout court ;
- futur `IOT-DOCTOR-DB-001` ajoutera `forge iot:doctor --db` qui fait
  un `SELECT COUNT(*) FROM iot_events` pour confirmer que la table
  existe et est lisible.

Ce ticket pose le squelette CLI + checks statiques. Les options
réseau viennent quand le besoin est concret et que les conditions de
test sont propres (un Mosquitto local lancé par les tests
d'intégration, ou un compose).
