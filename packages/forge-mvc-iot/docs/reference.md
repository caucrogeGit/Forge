# L'IoT dans Forge (forge-mvc-iot)

Ce document explique ce que fait l'opt-in `forge-mvc-iot`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-iot` reçoit des mesures de capteurs via MQTT, les stocke dans une table `iot_events`, et les expose par une API HTTP JSON.

Le cœur de Forge ignore tout de l'IoT : ce paquet fournit le subscriber, le stockage et l'API ; l'application décide de ce qu'elle fait des mesures.

??? note "1. Rôle du module"

    Des capteurs publient des mesures sur un broker MQTT.
    L'opt-in les **écoute**, les **valide** selon un contrat, les **stocke** dans `iot_events`, puis les **expose** en JSON pour l'application.

    L'écoute MQTT tourne dans un process séparé (`iot:listen`), pas dans le serveur web ; l'API HTTP, elle, se branche sur le routeur du projet (modèle opt-in de type route).

??? note "2. Installation"

    !!! warning "Prérequis : activez le venv du projet"

        Quelle que soit la source, installez **dans le venv du projet** :

        ```bash
        source .venv/bin/activate
        ```

        Lancé hors d'un venv, `pip` vise le Python **système** (Debian 12+, Ubuntu 23.04+),
        protégé par PEP 668. Il refuse alors d'installer, pour ne pas écraser les paquets
        gérés par `apt`, et affiche `externally-managed-environment`.
        Le venv de projet créé par `forge new` n'a pas ce verrou.

    #### Installer le paquet

    <div class="canal">

    #### A. Depuis PyPI (stable)

    La dernière version publiée :

    ```bash
    pip install --pre forge-mvc-iot
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-iot"
    ```

    </div>

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

    #### 3. Poser ce dont il a besoin

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


??? note "4. Désinstallation"

    ```bash
    forge opt-in:disable iot
    pip uninstall forge-mvc-iot
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre et débranche les routes de `mvc/routes/__init__.py`, sans toucher au paquet.
    `forge opt-in:remove iot` affiche la commande `pip uninstall` sans l'exécuter.

??? note "5. Commandes"

    `forge-mvc-iot` ajoute ces commandes :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `iot:doctor` | Diagnostic (paquet, config, migration, API). | `forge iot:doctor` |
    | `iot:init` | Copie la migration IoT vers `mvc/migrations/`. | `forge iot:init` |
    | `iot:simulate` | Publie des mesures MQTT factices (sans capteur). | `forge iot:simulate` |
    | `iot:listen` | Écoute le broker et insère dans `iot_events`. | `forge iot:listen` |
    | `iot:gc` | Purge les mesures antérieures à une rétention. | `forge iot:gc --days 90 --run` |

??? note "5 bis. Borner la table de mesures"

    `iot_events` reçoit une ligne par mesure publiée, et rien ne la bornait avant `IOT-RETENTION-GC-001`.

    Un capteur qui émet toutes les dix secondes y dépose plus de trois millions de lignes par an.
    Un site en compte rarement un seul, et la table grossissait donc jusqu'à la panne de remplissage.

    ```bash
    forge iot:gc --days 90          # affiche ce qui serait supprimé
    forge iot:gc --days 90 --run    # supprime
    ```

    La rétention peut aussi venir de la variable d'environnement `IOT_KEEP_DAYS`.
    L'option `--days` l'emporte sur elle, une valeur tapée disant une intention plus précise qu'une valeur héritée du déploiement.

    !!! warning "La rétention doit être dite"
        Aucune valeur par défaut n'est supposée à la place de l'exploitant, dont les obligations de conservation ne regardent pas Forge.
        Sans `--days` ni `IOT_KEEP_DAYS`, la commande refuse et explique.

        Une rétention nulle ou négative est refusée : elle viderait toute la table, ce qui ne peut pas être le résultat d'une étourderie de frappe.

    !!! info "Elle affiche avant d'effacer"
        Une mesure est un enregistrement délibéré, souvent conservé pour un historique ou une obligation, et aucune date ne dit d'elle-même qu'elle a cessé de valoir.

        La commande montre donc le nombre de lignes visées, et n'efface qu'avec `--run`.
        Aucune archive n'est produite avant suppression : un exploitant tenu de conserver ses mesures doit les exporter lui-même, en amont.

    Le module `storage/retention.py` porte le SQL et le calcul de la borne.

    | Élément | Rôle |
    |---|---|
    | `cutoff_for_days(keep_days)` | borne de rétention, en UTC |
    | `get_iot_count_before_sql()` | SQL du comptage, sans rien supprimer |
    | `get_iot_purge_sql()` | SQL de la suppression |
    | `IotRetentionError` | rétention invalide |

    Comme le reste du paquet, ce module n'accède jamais à la base de lui-même.
    Il rend du SQL et calcule des paramètres, la commande faisant la jonction.

    !!! info "Forge ne planifie rien"
        La commande est le point d'entrée à déclencher depuis cron ou un minuteur systemd, comme `sessions:gc`, `audit:gc` et `stats:gc`.

        La purge est indexée, `idx_iot_events_received_at` portant déjà sur la colonne filtrée.
        Aucune migration n'est requise.

??? note "6. Vue d'ensemble rapide"

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
    | Commandes | `iot:doctor`, `iot:init`, `iot:simulate`, `iot:listen`, `iot:gc` |
    | Exposition | API HTTP JSON (`register_iot_routes`) |
    | Installation | `pip install --pre forge-mvc-iot` |

??? note "7. Schémas UML"

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

??? note "8. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `register_iot_routes` | `register_iot_routes(router, *, repository=None, config=None) -> None` | branche l'API HTTP JSON |
    | `load_iot_config` | `load_iot_config(env=None) -> IotConfig` | configuration MQTT |
    | `MqttSubscriber` | classe | abonné MQTT : `connect`, `loop_forever`, `handle_message` |
    | `IotEventRepository` | classe | `insert`, `list_recent`, `find_by_device`, `count_by_device` |
    | `IotConfig` | dataclass | configuration (broker, topics, TLS) |

??? note "9. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Vérifier l'installation | `forge iot:doctor` |
    | Préparer la table | `forge iot:init` puis `forge migration:apply` |
    | Tester sans capteur | `forge iot:simulate` |
    | Recevoir les mesures | `forge iot:listen` (process séparé) |
    | Exposer en JSON | `register_iot_routes(router)` |
    | Lire par appareil | `IotEventRepository.find_by_device(...)` |

??? note "10. Exemples d'utilisation"

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

??? note "11. MQTT, contrat et exécution"

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

??? note "12. Jetons par site ou par équipement"

    L'API de lecture était protégée par **un** jeton, `FORGE_IOT_API_TOKEN`, qui donnait accès à toutes les mesures de tous les sites (`IOT-DEVICE-AUTH-001`).

    Un prestataire chargé des capteurs d'un bâtiment recevait ce jeton, et lisait par là les mesures des autres bâtiments, sans qu'aucun mécanisme ne l'en empêche ni ne le signale.

    | Portée | Ce qu'elle ouvre |
    |---|---|
    | globale | toutes les mesures, tous les sites |
    | site | toutes les mesures d'un site |
    | équipement | les mesures d'un seul équipement d'un site |

    ```bash
    forge iot:init && forge migration:apply
    forge iot:token create --site batimentA --label "prestataire CVC"
    forge iot:token list
    forge iot:token revoke 3
    ```

    !!! danger "Le registre s'active en le passant, jamais d'office"
        ```python
        from forge_mvc_iot import IotTokenRepository, register_iot_routes

        register_iot_routes(router, token_repository=IotTokenRepository())
        ```

        Le monter par défaut exigerait un jeton là où l'API était ouverte, et casserait sans le dire les déploiements existants. Le principe 3 veut que ce changement soit demandé, pas deviné.

        Sans registre, le comportement est exactement celui d'avant : le jeton d'environnement suffit, et son absence laisse l'API ouverte, ce que `register_iot_routes` refuse déjà en production.

    !!! warning "`FORGE_IOT_API_TOKEN` garde la portée globale"
        Le retirer serait une rupture d'API publique hors release majeure, que la règle C de la charte refuse.

        Préférez un jeton de site pour tout ce qui n'a pas besoin de tout voir.

    !!! info "Le jeton n'est affiché qu'une fois"
        Seule son empreinte SHA-256 est stockée. Le perdre oblige à en créer un autre, ce qui est le prix à payer pour qu'aucun secret ne dorme en clair dans la base.

        Un simple SHA-256 suffit ici, sans sel ni étirement : le jeton est engendré par Forge avec 256 bits d'entropie, contrairement à un mot de passe choisi par un humain, et il n'existe donc ni dictionnaire ni table arc-en-ciel à lui opposer. C'est la pratique établie pour les jetons d'API, et elle diffère de celle des mots de passe pour cette raison précise.

    !!! info "Un refus de portée est un 403, pas un 401"
        Un 401 ferait croire au porteur que son jeton est faux, et il le remplacerait au lieu d'en demander un dont la portée convient.

    Le filtrage a lieu **en SQL**. Rapatrier les mesures des autres sites pour les écarter ensuite les aurait fait passer par un processus qui n'y a pas droit.

    La révocation pose une date et ne supprime pas la ligne : savoir qu'un jeton a existé, et quand il a cessé de valoir, fait partie de ce qu'un exploitant doit pouvoir retrouver.

??? note "13. Moyenne, minimum et maximum sur une fenêtre"

    Le paquet rendait les mesures brutes et les comptait. La question qu'on pose à des relevés de capteurs n'avait aucune réponse (`IOT-AGGREGATES-001`) : « quelle a été la température moyenne de la semaine, et jusqu'où est elle montée ».

    L'application devait rapatrier toutes les mesures pour les additionner en Python, ce qui charge en mémoire ce que la base sait faire sans rien déplacer, et devient impraticable dès qu'un capteur relève chaque minute.

    ```
    GET /api/iot/sites/batimentA/aggregate/temperature?hours=168
    GET /api/iot/devices/batimentA/capteur-01/aggregate/temperature
    ```

    ```python
    from forge_mvc_iot import aggregate_for_device

    agregat = aggregate_for_device("batimentA", "capteur-01", "temperature", hours=24)
    agregat.average, agregat.minimum, agregat.maximum, agregat.count
    ```

    !!! warning "Une fenêtre vide ne rend pas zéro"
        `count` vaut zéro et les trois autres valent `None`.

        « Le capteur n'a rien envoyé » et « le capteur a relevé zéro » sont deux faits différents, que confondre fausserait toute moyenne.

    !!! info "La moyenne d'un site pèse par mesure, pas par équipement"
        C'est le comportement d'un `AVG` SQL : un capteur qui relève dix fois plus souvent pèse dix fois plus.

        Le dire vaut mieux que de le laisser supposer.

    !!! info "Ce que le module ne fait pas"
        Il ne **regroupe pas par intervalle**. Une série par tranches de cinq minutes demande des fonctions de fenêtrage que les quatre backends n'écrivent pas de la même façon, et le principe 5 veut du SQL visible plutôt qu'un générateur masquant quatre dialectes.

        Il n'**interpole** rien non plus.

    Le comptage porte sur `value` et non sur `*` : une mesure sans valeur ne doit pas gonfler l'effectif d'une moyenne qu'elle n'alimente pas. La fenêtre est bornée à un an, au delà la question relevant d'un export.

    PostgreSQL rend `AVG` en `Decimal`, MariaDB en flottant : la valeur est ramenée en flottant, sans quoi la même requête donnerait deux types selon le backend et la sérialisation JSON échouerait sur l'un des deux.

??? note "14. Brancher un contrôle d'accès applicatif"

    Le jeton dit **ce qu'un porteur peut lire**. Il ne dit rien de **qui** le porte, ni de ce que cette personne a le droit de faire dans l'application (`IOT-RBAC-READ-001`).

    Une console interne où un opérateur consulte les relevés a besoin des deux.

    ```python
    from forge_mvc_iot import ACTION_READ_EVENTS, register_iot_permission_check

    def controle(request, scope, action):
        return has_permission(request, "iot.read")   # votre RBAC

    register_iot_permission_check(controle)
    ```

    !!! info "Une prise, et non une dépendance à `forge-mvc-rbac`"
        Aucun opt-in Forge n'importe un autre opt-in, et un garde-fou le vérifie.

        Un paquet IoT qui dépendrait du RBAC obligerait à installer le RBAC pour recevoir des mesures MQTT, ce que le principe 8 refuse.

    !!! danger "Une vérification qui échoue refuse la lecture"
        Un contrôle qui lève, ou qui rend autre chose qu'un booléen, ne dit **pas** que l'accès est permis, il ne dit rien.

        Traiter ce silence comme une autorisation est la faute classique de ce genre de branchement : le jour où le service de permissions tombe, tout s'ouvre, et rien ne le signale. L'incident est journalisé pour l'exploitant.

    Plusieurs contrôles peuvent cohabiter : tous doivent accepter, et le premier refus arrête la série. Une politique d'accès s'ajoute, elle ne se remplace pas.

    Sans contrôle branché, seule la portée du jeton s'applique : le paquet n'invente pas une politique que personne n'a demandée.

    La liste des actions est **fermée**, `iot.read_events` et `iot.read_aggregates` : un contrôle branché sait ainsi exactement ce qu'il peut recevoir, et une action inconnue lève au lieu de passer.

## Voir aussi

- [Configuration (config.py)](references/config.md) : `IotConfig`, MQTT.
- [Subscriber MQTT (mqtt/subscriber.py)](references/mqtt_subscriber.md) et [Contrat MQTT](references/mqtt_contract.md).
- [Repository d'événements (storage/repository.py)](references/storage_repository.md) et [Contrat SQL](references/storage_events.md).
- [API HTTP (http.py)](references/http.md) : routes JSON.
- [Architecture Forge IoT](architecture.md) : trajectoire d'ensemble.
- [Welcome-IoT](welcome/debutant/iot-welcome.md) : parcours d'apprentissage.
