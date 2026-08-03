# Le déploiement dans Forge (forge-mvc-deploy)

Ce document explique ce que fait l'opt-in `forge-mvc-deploy`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-deploy` est un outillage **CLI-only** : il ajoute `forge deploy:init` (générer les fichiers de déploiement) et `forge deploy:check` (les vérifier).

Il n'expose aucune API runtime : une application ne l'importe jamais à l'exécution (ADR-053).

??? note "1. Rôle du module"

    Mettre une application Forge en production demande quelques fichiers standard : un point d'entrée WSGI, une configuration de serveur web, un service système.

    L'opt-in **génère** ces fichiers à partir de gabarits : `wsgi.py`, une configuration Nginx, une unité systemd et un README, alignés sur le chemin de production officiel (Gunicorn).

    Il reste un outil de **préparation** : il écrit des fichiers que vous relisez et adaptez, il ne déploie pas à votre place et ne tourne pas dans le serveur.

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
    pip install --pre forge-mvc-deploy
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-deploy"
    ```

    </div>

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-deploy`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-deploy==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    ```bash
    forge opt-in:enable deploy --apply
    ```

    L'opt-in est inscrit dans `optins/registry.py` (ADR-061), ce qui le rend visible du
    projet.
    `--apply` est **obligatoire** : sans lui, la commande simule et n'écrit rien.

    #### 3. Poser ce dont il a besoin

    Cet opt-in n'apporte aucune table, mais il a tout de même une initialisation :

    ```bash
    forge deploy:init
    ```

    Elle génère les fichiers Nginx et systemd dans `deploy/`.
    Ne pas avoir de tables ne veut pas dire n'avoir rien à faire.

    #### 4. Le brancher là où il agit

    Rien à brancher : il ajoute des commandes `forge`, sans surface de runtime.
    Une application ne l'importe pas dans le chemin d'une requête.

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
    forge opt-in:disable deploy
    pip uninstall forge-mvc-deploy
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre, sans toucher au paquet.
    `forge opt-in:remove deploy` affiche la commande `pip uninstall` sans l'exécuter.

??? note "5. Commandes"

    `forge-mvc-deploy` ajoute ces commandes (opt-in CLI-only) :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `deploy:init` | Génère `wsgi.py`, la config Nginx, l'unité systemd et un README (write-if-new). | `forge deploy:init` |
    | `deploy:check` | Vérifie la configuration de déploiement. | `forge deploy:check` |

??? note "6. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-deploy` |
    | Module | `forge_mvc_deploy` |
    | Catégorie | Exploitation et outillage (ADR-055) |
    | Couche | opt-in **CLI-only** (aucune API runtime) |
    | Dépend de | `forge-mvc` (au moment du CLI seulement) |
    | Commandes | `deploy:init`, `deploy:check` |
    | Génère | `wsgi.py`, configuration Nginx, unité systemd, README |
    | Serveur de production | Gunicorn (`wsgi:application`) |
    | Décision d'architecture | ADR-053 (extraction, opt-in CLI-only) |
    | Installation | `pip install --pre forge-mvc-deploy` |

??? note "7. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

    Le diagramme de classe montre les commandes et les fichiers générés.

    Le diagramme de séquence montre la préparation puis la pile de production servie.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre les deux commandes et les artefacts qu'elles produisent ou vérifient.

    ```mermaid
    classDiagram
        direction LR

        class deploy {
            <<CLI>>
            +deploy:init
            +deploy:check
        }

        class artefacts {
            <<fichiers générés>>
            +wsgi.py
            +nginx.conf
            +systemd .service
            +README
        }

        class production {
            <<pile>>
            +Nginx
            +Gunicorn
            +wsgi:application
        }

        deploy --> artefacts : génère (init) / vérifie (check)
        artefacts --> production : décrivent

    ```

    À retenir :

    - `deploy:init` écrit les fichiers de déploiement (write-if-new) ;
    - `deploy:check` vérifie leur présence et leur cohérence ;
    - la pile cible est Nginx devant Gunicorn servant `wsgi:application` ;
    - aucun de ces fichiers n'est importé par l'application au runtime.

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre la préparation, puis une requête servie en production.

    ```mermaid
    sequenceDiagram
        actor Op as Opérateur
        participant CLI as forge deploy
        participant Repo as Fichiers projet
        actor Client
        participant Nginx as Nginx
        participant Gunicorn as Gunicorn
        participant App as wsgi:application

        Op->>CLI: forge deploy:init
        CLI->>Repo: écrit wsgi.py, nginx, systemd, README
        Op->>CLI: forge deploy:check
        CLI-->>Op: rapport (présence / cohérence)

        Client->>Nginx: requête HTTPS
        Nginx->>Gunicorn: proxy
        Gunicorn->>App: appelle l'application WSGI
        App-->>Client: réponse

    ```

    À retenir :

    - la génération et la vérification sont des étapes d'**opérateur**, hors application ;
    - en production, Nginx reçoit le trafic et le passe à Gunicorn ;
    - Gunicorn sert le callable `application` de `wsgi.py` ;
    - le serveur de développement (`python app.py`) ne sert pas la production.


??? note "8. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Générer les fichiers de déploiement | `forge deploy:init` |
    | Vérifier la configuration | `forge deploy:check` |
    | Servir en production | Gunicorn sur `wsgi:application` |
    | Mettre derrière un proxy | configuration Nginx générée |
    | Gérer le service | unité systemd générée |

??? note "9. Exemple d'utilisation"

    ```bash
    # 1. Générer les fichiers (ne réécrit pas l'existant)
    forge deploy:init

    # 2. Vérifier la cohérence
    forge deploy:check

    # 3. Servir en production (exemple)
    .venv/bin/gunicorn wsgi:application --workers 4 --bind 127.0.0.1:8000
    ```

    Relisez et adaptez les fichiers générés (domaine, chemins, nombre de workers) avant de les mettre en service.

    !!! tip "Aide-mémoire"
        Deux commandes, une pile :

        - `deploy:init` génère, `deploy:check` vérifie ;
        - en production, Nginx devant Gunicorn servant `wsgi:application`.

    !!! warning "Projet créé avant la 1.0.0-rc.4"

        L'unité systemd attend le service du backend résolu, `postgresql.service` sous PostgreSQL, aucun sous SQLite.
        Avant la `1.0.0-rc.4`, elle nommait toujours `mariadb.service`.

        `deploy:init` ne réécrit jamais un fichier existant (principe 9), donc un projet plus ancien garde son unité d'origine.
        Sous un autre backend, cet `After=` désigne un service inexistant et ne retarde donc rien : au démarrage de la machine, l'application part avant sa base et rate ses premières connexions.

        `deploy:check` le signale désormais. La correction reste manuelle, dans `deploy/systemd/forge-app.service`.

??? note "10. CLI-only et adaptation"

    `forge-mvc-deploy` n'a pas d'API runtime : il sert uniquement à préparer le déploiement.
    Une application ne l'importe pas à l'exécution.

    Les fichiers générés sont des **points de départ** : adaptez le domaine, les chemins absolus, le nombre de workers et les options TLS à votre serveur.

    !!! warning "Relire avant de déployer"
        Les gabarits supposent une disposition standard (`.venv`, `wsgi.py` à la racine).

        Vérifiez chemins, utilisateur système, certificats et limites de taille avant la mise en service.

    !!! note "Chemin de production officiel"
        Gunicorn servant `wsgi:application`, derrière Nginx, est le chemin de production de Forge.

        Le serveur de développement (`python app.py`) n'est pas destiné à la production.

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-deploy` ; le paquet n'ajoute que des commandes CLI quand il est installé (ADR-053).

## Voir aussi

- [Commandes deploy:* (cli/deploy.py)](references/cli.md) : détail de `deploy:init` / `deploy:check`.
- [Welcome-Deploy](welcome/debutant/deploy-welcome.md) : parcours d'apprentissage.
