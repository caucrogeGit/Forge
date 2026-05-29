# Smoke test local Forge IoT

> **Statut** : parcours de vérification **local et opt-in**. Il valide
> que les briques Forge IoT livrées fonctionnent **ensemble** avec un
> vrai broker Mosquitto et une vraie base MariaDB. Ce n'est **pas** un
> test de la CI standard : il dépend de services locaux qui ne sont pas
> toujours disponibles.

## Objectif

Dérouler une fois, de bout en bout, le flux complet :

```text
Mosquitto
   → forge iot:doctor --mqtt
   → forge iot:init
   → forge migration:apply
   → forge iot:doctor --db
   → forge iot:listen
   → forge iot:simulate
   → /api/iot/events
```

Si chaque étape passe, l'intégration locale est saine.

## Pré-requis

Ce smoke test suppose :

- **Mosquitto actif** localement — voir
  [Mosquitto local](mosquitto-local.md) :

  ```bash
  sudo systemctl status mosquitto
  ```

- **MariaDB configurée** pour le projet (variables `DB_*` dans `env/dev`) ;
- un **projet Forge** avec le module opt-in `forge-mvc-iot` installé.

## Script semi-automatique

Le dépôt fournit un script qui enchaîne les étapes et marque des pauses
aux endroits manuels (migration et écoute, à lancer toi-même) :

```bash
bash scripts/iot-local-smoke.sh
```

Le script ne masque aucune étape : il lance les diagnostics et la
simulation, mais te laisse exécuter `forge migration:apply` et
`forge iot:listen` toi-même, entre deux pauses.

## Parcours manuel détaillé

Si tu préfères tout dérouler à la main :

```bash
sudo systemctl status mosquitto          # Mosquitto tourne ?

forge iot:doctor                         # diagnostic statique
forge iot:doctor --mqtt                  # le broker répond ?

forge iot:init                           # copier la migration
forge migration:apply                    # créer la table iot_events
forge iot:doctor --db                    # la table est lisible ?
```

Dans un **premier terminal**, lance l'écoute (laisse tourner) :

```bash
forge iot:listen
```

Dans un **deuxième terminal**, publie des mesures :

```bash
forge iot:simulate --count 3 --interval 1
```

Trois lignes `[OK]` doivent apparaître côté `forge iot:listen`. Enfin,
avec l'application lancée (`forge run`), relis les mesures stockées :

```bash
curl http://localhost:8000/api/iot/events
```

## Ce que ce smoke test n'est pas

- **pas un test de CI standard** : il dépend de Mosquitto et MariaDB
  locaux, qui ne sont pas toujours présents en intégration continue ;
- il **suppose Mosquitto actif** et **MariaDB configurée** ;
- il **suppose** un projet Forge avec `forge-mvc-iot` installé ;
- il **ne teste pas** TLS ni l'authentification MQTT ;
- il **ne teste pas** Forge Design.

Pour un broker local, voir [Mosquitto local](mosquitto-local.md). Pour
le détail de chaque commande, voir [Diagnostic](doctor.md),
[Initialisation](init-command.md), [Écoute](listen-command.md) et
[Simulateur](simulator.md).
