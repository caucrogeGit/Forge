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
    | Traiter les tâches de fond | `worker.py` et `forge-jobs-worker.service` engendrés |

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

??? note "9 bis. Secrets laissés à leur valeur d'amorçage"

    `deploy:check` vérifiait `DB_HOST`, `DB_NAME` et `DB_APP_LOGIN`, jamais les mots de passe ni les jetons.

    Un `DB_APP_PWD=change-me` recopié d'un exemple passait donc le contrôle.
    La panne n'apparaissait qu'au premier accès à la base, en production, alors que le pré-vol existe précisément pour l'éviter (`DEPLOY-CHECK-SECRETS-001`).

    Le pré-vol produit alors deux lignes, une par verdict.

    | Verdict | Intitulé | Détail |
    |---|---|---|
    | `[ERREUR]` | Secrets de env/prod | `DB_APP_PWD` : valeur d'amorçage ou vide, poser un secret réel |
    | `[OK]` | Secrets de env/prod | 1 renseigné(s) : `DB_ADMIN_PWD` |

    La commande sort en échec, comme pour toute erreur du pré-vol.

    !!! info "Le repérage porte sur le nom, pas sur une liste"
        Une variable dont le nom contient `PASSWORD`, `PWD`, `SECRET` ou `TOKEN` est traitée comme un secret.
        Un opt-in ajouté demain est donc couvert sans que le pré-vol change.

        Les noms de chemin et de drapeau sont écartés, `SSL_KEYFILE` en tête.
        Un contrôle qui crie à tort finit désactivé, et le pré-vol perdrait alors tout son intérêt.

    !!! warning "La valeur n'est jamais affichée"
        Seul le nom de la variable fautive apparaît dans le rapport.
        Celui-ci peut être collé dans un ticket ou un journal, où un secret réel fuirait.

    !!! info "Forge ne juge pas de la force d'un secret"
        Le contrôle refuse l'évidence, `change-me`, `default`, `secret`, une valeur vide.
        Il ne mesure pas l'entropie d'une chaîne, ce qui demanderait des règles arbitraires que Forge n'impose pas.

        Un mot de passe faible mais non évident passe donc le pré-vol.
        Le choix d'un secret reste celui de l'exploitant.

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

## Le worker de tâches de fond

`forge deploy:init` engendre deux fichiers de plus quand `forge-mvc-jobs` est installé.

| Fichier | Rôle |
|---|---|
| `worker.py` | point d'entrée du worker, à la racine du projet |
| `deploy/systemd/forge-jobs-worker.service` | unité systemd du worker |

Ils ne sont engendrés que si le paquet est là.
Poser un `worker.py` dans un projet sans file de tâches donnerait un fichier à comprendre pour rien.

!!! danger "Rien ne traite la file sans worker"
    `enqueue()` écrit une ligne dans une table.

    Le guide documentait l'unité `forge-app`, le minuteur `forge-jobs-reclaim`, et aucun service pour traiter les tâches (`DEPLOY-JOBS-WORKER-UNIT-001`).
    Une application qui le suivait à la lettre obtenait donc une table qui grossit, et un minuteur qui remet consciencieusement en file des tâches que personne ne prend.

    La panne est silencieuse et trompeuse.
    `systemctl` affiche un `forge-app` parfaitement vert, et le minuteur donne l'impression que quelque chose tourne.

!!! warning "Le worker refuse de démarrer sans gestionnaire, et c'est voulu"
    Forge ne connaît pas vos gestionnaires et ne peut pas les inscrire à votre place.
    `worker.py` est votre fichier, engendré s'il n'existe pas et jamais réécrit.

    Une tâche dont le nom n'a aucun gestionnaire est marquée `failed`.
    Un worker parti avec un `HANDLERS` vide ne se contenterait donc pas de ne rien faire, il viderait la file en la détruisant tâche par tâche, en affichant un service vert.

!!! danger "Le pré-vol refuse une file que personne ne traite"
    Les dix-neuf contrôles de `deploy:check` n'en regardaient aucun (`DEPLOY-CHECK-JOBS-WORKER-001`).

    Un projet pouvait donc passer le pré-vol au vert avec une file que personne ne draine.

    Le contrôle ne se déclenche que si le projet **appelle réellement** `enqueue`, lu par `ast` et jamais par grep.
    Une occurrence dans un commentaire, une chaîne ou une docstring ferait accuser un projet qui n'enfile rien, et un détecteur qui accuse à tort se fait désactiver.

    | Situation | Verdict |
    |---|---|
    | `forge-mvc-jobs` absent | silence |
    | installé, mais rien n'enfile | silence |
    | le projet enfile, `worker.py` absent | erreur |
    | `worker.py` présent, `HANDLERS` vide | erreur |
    | `HANDLERS` rempli, aucune unité déclarée | erreur |
    | tout est là | ok |

    C'est une erreur, pas un avertissement, comme pour les sessions multi-travailleurs.
    Les emails ne partiront pas, il n'y a rien à nuancer.

    Un `HANDLERS` construit autrement qu'en littéral, par une fonction ou un registre, n'est pas jugeable statiquement.
    Le pré-vol se tait alors, plutôt que d'accuser.

!!! info "Dire où vit l'unité du worker"
    `forge deploy:check --worker deploiement/w.service` déclare son emplacement, comme `--unite` et `--nginx` le font pour les autres.

    Un projet qui range ou renomme son unité, ce que le principe 9 l'invite à faire, deviendrait sinon invisible du pré-vol.

!!! info "L'arrêt propre laisse finir la tâche en cours"
    L'unité envoie `SIGTERM`, que `worker.py` note sans interrompre la tâche en cours.

    `TimeoutStopSec` borne cette attente, à quatre-vingt-dix secondes par défaut.
    Au delà, systemd tue le worker, la tâche est perdue en vol et repart par `forge jobs:reclaim` une fois son bail expiré.
    Portez cette valeur au delà de votre tâche la plus longue, un transcodage vidéo dépassant largement ce délai.

## Les gestes périodiques

Le guide engendré porte un tableau des commandes d'entretien à planifier.

Il n'en citait que trois, alors que les opt-ins en livrent neuf.
Un geste d'entretien absent du guide n'est pas planifié, et une table qui grossit sans purge est une panne différée.

!!! danger "Six de ces commandes ne suppriment rien sans leur option"
    Lancées seules, `audit:gc`, `stats:gc`, `iot:gc`, `video:cleanup`, `files:orphans` et `images:orphans` affichent ce qu'elles feraient, puis sortent en succès.

    C'est un bon défaut, il évite une suppression involontaire.
    Mais un minuteur qui planifie la commande nue tourne pour rien, indéfiniment, en affichant un succès à chaque passage.

    Le tableau du guide cite donc les invocations complètes, `--run`, `--apply` ou `--delete` compris.

## La limite sur la connexion

`forge deploy:init` engendre une configuration Nginx qui borne `/login` à cinq POST par minute et par IP, puis répond 429.

!!! danger "Le compteur applicatif vaut par processus"
    Le compteur anti-bruteforce du cœur vit en mémoire du processus.

    L'unité systemd engendrée lance quatre travailleurs, chacun comptant séparément : les cinq tentatives par minute en deviennent vingt, et le verrouillage ne suit pas l'attaquant d'un travailleur à l'autre.

    Ce n'était pas une découverte, le guide de sécurité de Forge le disait et prescrivait cette parade.
    C'était bien le défaut : la configuration engendrée ne la portait pas, et une ligne de défense qui vit dans une page de documentation est absente de tout projet qui n'a pas lu cette page (`DEPLOY-NGINX-RATE-LIMIT-001`).

!!! info "Seul le POST est compté"
    Un `map` sur `$request_method` donne une clé vide hors POST, ce qui n'applique pas la limite.

    Limiter aussi le GET ferait répondre 429 à qui recharge la page de connexion six fois.
    Une limite qui gêne se fait désactiver, et ne protège alors plus rien.

!!! warning "Une route de connexion renommée n'est plus bornée"
    Le `location` vise `/login`, la route qu'écrit `forge make:auth`.

    Un projet qui a renommé sa route adapte ce bloc, sans quoi la limite paraît posée et ne garde rien.

!!! warning "Le challenge MFA n'est pas couvert"
    `forge-mvc-mfa` ne pose aucune route, l'application écrit les siennes, et Forge ne peut donc pas viser celle du challenge.

    Son compteur souffre pourtant du même défaut.
    Ajoutez un `location` de même forme sur votre route de challenge.

!!! info "Le nom de la zone vient du dossier du projet"
    Deux projets Forge derrière le même Nginx déclareraient sinon deux zones homonymes, et Nginx refuserait de démarrer sur un message qui ne dit pas quel fichier est en cause.

## Servir derrière Caddy plutôt que Nginx

Forge engendre **un** gabarit de reverse proxy, celui de Nginx, et il n'en engendrera pas un second.
Ce n'est pas un manque de temps : `deploy:check` lit cette configuration pour vous dire ce qui manque, et deux syntaxes voudraient dire deux lecteurs, dont l'un finirait en retard sur l'autre sans que rien ne le signale.

Caddy reste un choix légitime, et il obtient ses certificats tout seul.
Voici ce que chaque bloc du gabarit Nginx y devient, y compris ceux qui n'y ont pas d'équivalent direct.

```caddyfile
monapp.example.com {
    encode zstd gzip

    handle_path /static/* {
        root * /srv/monapp/public/static
        header Cache-Control "max-age=604800, immutable"
        header X-Content-Type-Options "nosniff"
        file_server
    }

    # L'équivalent de `internal;` : ce chemin n'est atteignable que
    # par un en-tête X-Accel-Redirect émis par l'application.
    handle_path /protected/* {
        root * /srv/monapp/storage/uploads
        file_server
    }

    reverse_proxy unix//run/forge-app.sock
}
```

| Bloc Nginx | En Caddy | Écart à connaître |
|---|---|---|
| `listen 443 ssl` et les directives `ssl_*` | rien à écrire | Caddy obtient et renouvelle le certificat seul ; il lui faut le port 80 ouvert |
| `add_header Strict-Transport-Security` | rien à écrire | Caddy le pose par défaut sur un site en HTTPS |
| `location /static/` | `handle_path /static/*` | `handle_path` retire le préfixe, ce que `alias` faisait |
| `location /protected/ { internal; }` | `handle_path` non exposé | **Caddy n'a pas d'équivalent de `internal;`** : c'est votre `X-Accel-Redirect` qui doit pointer là, et rien ne l'empêchera d'être appelé directement |
| `limit_req_zone` sur `/login` | `rate_limit` | Le module n'est pas dans la version standard : il faut un binaire construit avec lui |
| `proxy_pass` | `reverse_proxy` | Les en-têtes `X-Forwarded-*` sont posés par défaut |

!!! danger "Le point qui ne se transpose pas"
    `internal;` est la moitié qui protège dans le service de fichiers par accélération.

    Sans lui, `/protected/` répond à quiconque devine un nom de fichier, et l'autorisation que l'application venait de faire ne sert plus à rien.
    Caddy ne l'a pas : si vous servez des fichiers protégés, gardez Nginx, ou faites passer les téléchargements par l'application.

!!! warning "`deploy:check` ne lira pas votre Caddyfile"
    Les contrôles qui portent sur Nginx se tairont, et leur silence n'est pas un feu vert.

    Les autres, l'unité systemd, les secrets, `APP_ENV`, le compte de service, les droits du stockage et le worker, restent valables tels quels.
