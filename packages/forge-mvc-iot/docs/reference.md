# L'IoT dans Forge (forge-mvc-iot)

Ce document explique ce que fait l'opt-in `forge-mvc-iot`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-iot` reçoit des mesures de capteurs via MQTT, les stocke dans une table `iot_events`, et les expose par une API HTTP JSON.

Le cœur de Forge ignore tout de l'IoT : ce paquet fournit le subscriber, le stockage et l'API ; l'application décide de ce qu'elle fait des mesures.

??? note "1. Rôle du module"

    Des capteurs publient des mesures sur un broker MQTT.
    L'opt-in les **écoute**, les **valide** selon un contrat, les **stocke** dans `iot_events`, puis les **expose** en JSON pour l'application.

    L'écoute MQTT tourne dans un process séparé (`iot:listen`), pas dans le serveur web ; l'API HTTP, elle, se branche sur le routeur du projet (modèle opt-in de type route).

??? note "2. Installation et désinstallation"

    ### Installation

    === "Depuis PyPI (stable)"

        La dernière version publiée :

        ```bash
        pip install --pre forge-mvc-iot
        ```

    === "Depuis Git (avant-garde)"

        Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

        ```bash
        source .venv/bin/activate
        pip install "git+https://github.com/caucrogeGit/Forge.git@main"
        pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-iot"
        ```

        !!! warning "Erreur « externally-managed-environment » ?"

            Lancées hors d'un venv, ces commandes visent le Python **système** (Debian 12+, Ubuntu 23.04+), protégé par PEP 668.
            La cible correcte est le venv du projet (`source .venv/bin/activate`), jamais le Python système.

    Puis activez l'opt-in :

    ```bash
    forge opt-in:enable iot --apply
    ```


    `opt-in:enable` inscrit l'opt-in dans `optins/registry.py` (ADR-061) et câble ses routes dans `mvc/routes/__init__.py`.
    `forge opt-in:install iot` affiche la commande `pip` sans l'exécuter.

    Puis créez la table `iot_events`, prérequis dur du module :

    ```bash
    forge iot:init
    forge migration:apply
    ```

    `iot:init` copie la migration embarquée dans `mvc/migrations/` ; `migration:apply` l'exécute.
    Sans cette table, le premier message reçu échoue.

    Ces gestes ne suffisent pas à rendre l'opt-in **opérationnel** : il reste à l'épingler dans
    `requirements.txt`, à provisionner sa base s'il en a une, à le brancher là où il agit et à le
    prouver par un premier usage réel.
    Voir la procédure canonique, [Rendre un opt-in opérationnel : les cinq points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    ### Désinstallation

    ```bash
    forge opt-in:disable iot
    pip uninstall forge-mvc-iot
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre et débranche les routes de `mvc/routes/__init__.py`, sans toucher au paquet.
    `forge opt-in:remove iot` affiche la commande `pip uninstall` sans l'exécuter.

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-iot`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-iot==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    ```bash
    forge opt-in:enable iot --apply
    ```

    L'opt-in est inscrit dans `optins/registry.py` (ADR-061), ce qui le rend visible du
    projet.
    `--apply` est **obligatoire** : sans lui, la commande simule et n'écrit rien.

    #### 3. Poser sa base

    ```bash
    forge iot:init
    forge migration:apply
    ```

    `iot:init` copie la migration embarquée dans `mvc/migrations/` ;
    `migration:apply` l'exécute et la trace (ADR-071).
    Sans cette étape, le premier appel échoue sur une table absente.

    #### 4. Le brancher là où il agit

    Ses routes montent avec celles des autres opt-ins, par l'appel
    `register_optins(router)` déjà présent dans `mvc/routes/__init__.py`.
    Rien de plus à écrire.

    #### 5. Le prouver

    ```bash
    make check
    forge doctor
    ```

    Puis un premier usage réel.
    Un opt-in installé, inscrit et provisionné qu'aucun code n'appelle n'est pas
    opérationnel : il est seulement présent.


??? note "4. Commandes"

    `forge-mvc-iot` ajoute ces commandes :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `iot:doctor` | Diagnostic (paquet, config, migration, API). | `forge iot:doctor` |
    | `iot:init` | Copie la migration IoT vers `mvc/migrations/`. | `forge iot:init` |
    | `iot:simulate` | Publie des mesures MQTT factices (sans capteur). | `forge iot:simulate` |
    | `iot:listen` | Écoute le broker et insère dans `iot_events`. | `forge iot:listen` |

??? note "5. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-iot` |
    | Module | `forge_mvc_iot` |
    | Catégorie | Communication (ADR-055) |
    | Couche | opt-in de type route (couche `optins/`) |
    | Dépend de | `forge-mvc`, `paho-mqtt`, un backend BDD (ADR-054) |
    | API publique | `register_iot_routes`, `load_iot_config`, `MqttSubscriber`, `IotEventRepository` |
    | Table SQL | `iot_events` |
    | Configuration | MQTT via `load_iot_config` (`IotConfig`) |
    | Commandes | `iot:doctor`, `iot:init`, `iot:simulate`, `iot:listen` |
    | Exposition | API HTTP JSON (`register_iot_routes`) |
    | Installation | `pip install --pre forge-mvc-iot` |

??? note "6. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

    Le diagramme de classe montre le subscriber, le dépôt, l'API et la table.

    Le diagramme de séquence montre le trajet d'une mesure, du capteur à l'API.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre que le `MqttSubscriber` insère via `IotEventRepository`, et que `register_iot_routes` lit ce même dépôt pour l'API.

    ```mermaid
    classDiagram
        direction LR

        class MqttSubscriber {
            +connect()
            +loop_forever()
            +handle_message(topic, payload)
        }

        class IotEventRepository {
            +insert(...)
            +list_recent(limit) list
            +find_by_device(...) list
            +count_by_device(site, device_id) int
        }

        class http {
            <<module>>
            +register_iot_routes(router, repository, config)
        }

        class iot_events {
            <<table>>
            +site
            +device_id
            +metric
            +value
            +recorded_at
        }

        class IotConfig {
            +from env (MQTT)
        }

        MqttSubscriber --> IotEventRepository : insert
        IotEventRepository --> iot_events : lit / écrit
        http --> IotEventRepository : lit
        MqttSubscriber --> IotConfig : se connecte avec
    ```

    À retenir :

    - le subscriber transforme un message MQTT en ligne `iot_events` ;
    - le dépôt est la seule porte vers la table ;
    - l'API HTTP lit le même dépôt ;
    - la configuration MQTT vient de l'environnement (`IotConfig`).

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre une mesure du capteur jusqu'à l'API.

    ```mermaid
    sequenceDiagram
        actor Capteur
        participant Broker as Broker MQTT
        participant Listen as iot:listen (MqttSubscriber)
        participant Repo as IotEventRepository
        participant Table as iot_events
        participant API as register_iot_routes
        actor App as Application

        Capteur->>Broker: publie une mesure (topic, payload)
        Listen->>Broker: abonné, reçoit le message
        Listen->>Listen: valide selon le contrat
        Listen->>Repo: insert(mesure)
        Repo->>Table: insère la ligne
        App->>API: GET /iot/events
        API->>Repo: list_recent / find_by_device
        Repo-->>API: lignes
        API-->>App: JSON
    ```

    À retenir :

    - l'écoute MQTT tourne dans un process séparé (`iot:listen`) ;
    - chaque message valide devient une ligne `iot_events` ;
    - un message non conforme au contrat est rejeté ;
    - l'API HTTP expose les mesures en JSON, sans toucher au broker.

??? note "7. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `register_iot_routes` | `register_iot_routes(router, *, repository=None, config=None) -> None` | branche l'API HTTP JSON |
    | `load_iot_config` | `load_iot_config(env=None) -> IotConfig` | configuration MQTT |
    | `MqttSubscriber` | classe | abonné MQTT : `connect`, `loop_forever`, `handle_message` |
    | `IotEventRepository` | classe | `insert`, `list_recent`, `find_by_device`, `count_by_device` |
    | `IotConfig` | dataclass | configuration (broker, topics, TLS) |

??? note "8. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Vérifier l'installation | `forge iot:doctor` |
    | Préparer la table | `forge iot:init` puis `forge migration:apply` |
    | Tester sans capteur | `forge iot:simulate` |
    | Recevoir les mesures | `forge iot:listen` (process séparé) |
    | Exposer en JSON | `register_iot_routes(router)` |
    | Lire par appareil | `IotEventRepository.find_by_device(...)` |

??? note "9. Exemples d'utilisation"

    ### 8.1 Brancher l'API HTTP JSON

    ```python
    # optins/iot/routes.py (couche optins du projet)
    from forge_mvc_iot import register_iot_routes


    def register(router) -> None:
        register_iot_routes(router)
    ```

    `forge opt-in:enable iot --apply` crée cette couche ; le branchement reste explicite.

    ### 8.2 Écouter le broker (process séparé)

    ```bash
    forge iot:init && forge migration:apply     # crée la table iot_events
    forge iot:simulate                   # publie des mesures de test
    forge iot:listen                     # écoute et stocke
    ```

    `iot:listen` tourne en service (systemd) ou en terminal dédié, pas dans le serveur web.

    !!! tip "Aide-mémoire"
        Deux process, une table :

        - réception : `iot:listen` (MQTT vers `iot_events`) ;
        - exposition : `register_iot_routes` (HTTP JSON depuis `iot_events`).

??? note "10. MQTT, contrat et exécution"

    Les messages MQTT suivent un **contrat** (site, appareil, métrique, valeur, horodatage) ; un message non conforme est rejeté à la réception.

    `paho-mqtt` est la dépendance MQTT ; TLS est géré par `mqtt/tls.py`.

    !!! warning "L'écoute tourne à part"
        `iot:listen` (le subscriber MQTT) s'exécute dans un **process distinct** du serveur web.

        Ne l'intégrez pas au process WSGI : le serveur doit rester disponible pour les requêtes.

    !!! note "Tester sans matériel"
        `forge iot:simulate` publie des mesures factices conformes au contrat.

        Vous pouvez ainsi valider toute la chaîne (réception, stockage, API) sans capteur réel.

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-iot` : la dépendance va de l'opt-in vers le cœur.

## Voir aussi

- [Configuration (config.py)](references/config.md) : `IotConfig`, MQTT.
- [Subscriber MQTT (mqtt/subscriber.py)](references/mqtt_subscriber.md) et [Contrat MQTT](references/mqtt_contract.md).
- [Repository d'événements (storage/repository.py)](references/storage_repository.md) et [Contrat SQL](references/storage_events.md).
- [API HTTP (http.py)](references/http.md) : routes JSON.
- [Architecture Forge IoT](architecture.md) : trajectoire d'ensemble.
- [Welcome-IoT](welcome/debutant/iot-welcome.md) : parcours d'apprentissage.
