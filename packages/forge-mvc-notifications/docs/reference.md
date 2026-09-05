# Les notifications in-app dans Forge (forge-mvc-notifications)

Ce document explique ce que fait l'opt-in `forge-mvc-notifications`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-notifications` crée des notifications destinées aux utilisateurs dans une table `notifications`, les lit, et les marque comme lues.

Le cœur de Forge ignore tout des notifications : ce paquet fournit la table et les helpers, l'application décide de qui notifier et quand.

??? note "1. Rôle du module"

    Une application a souvent besoin d'avertir un utilisateur : élève inscrit, note publiée, devoir à rendre.

    L'opt-in stocke ces avis dans une table SQL (`notifications`) et expose des fonctions pour notifier, lister, compter les non lues et marquer comme lu.

    Son périmètre V1 est **in-app** : des lignes en base.
    La livraison hors application (email, push) reste applicative, par exemple en combinant ce paquet avec `forge-mvc-jobs` et `forge-mvc-mail`.

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
    pip install --pre forge-mvc-notifications
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-notifications"
    ```

    </div>

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-notifications`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-notifications==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    ```bash
    forge opt-in:enable notifications --apply
    ```

    L'opt-in est inscrit dans `optins/registry.py` (ADR-061), ce qui le rend visible du
    projet.
    `--apply` est **obligatoire** : sans lui, la commande simule et n'écrit rien.

    #### 3. Poser ce dont il a besoin

    ```bash
    forge notifications:init
    forge migration:apply
    ```

    `notifications:init` copie la migration embarquée dans `mvc/migrations/` ;
    `migration:apply` l'exécute et la trace (ADR-071).
    Sans cette étape, le premier appel échoue sur une table absente.

    #### 4. Le brancher là où il agit

    Il s'importe dans le code qui s'en sert. Il n'y a ni route à monter ni middleware
    à poser.

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
    forge opt-in:disable notifications
    pip uninstall forge-mvc-notifications
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre (le code n'était pas câblé), sans toucher au paquet.
    `forge opt-in:remove notifications` affiche la commande `pip uninstall` sans l'exécuter.

??? note "5. Commandes"

    `forge-mvc-notifications` ajoute une commande :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `notifications:init` | Crée la table `notifications` (DDL fournie). | `forge notifications:init` |

??? note "6. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-notifications` |
    | Module | `forge_mvc_notifications` |
    | Catégorie | Communication (ADR-055) |
    | Couche | opt-in (brique optionnelle) |
    | Dépend de | `forge-mvc` et un backend BDD installé (ADR-054) |
    | API publique | `notify`, `get_notifications`, `unread_count`, `mark_read`, `mark_all_read`, `Notification`, `on_notification_created`, `validate_target_url` |
    | Table SQL | `notifications` (`TABLE_NAME`) |
    | Limite de lecture | `MAX_LIMIT` = 1000 entrées |
    | Exception liée | `NotificationError` si destinataire/message vide ou limite invalide |
    | Périmètre | in-app (V1) ; livraison email/push à charge de l'application |
    | Installation | `pip install --pre forge-mvc-notifications` |

??? note "7. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

    Le diagramme de classe montre l'API, l'objet renvoyé et la table.

    Le diagramme de séquence montre la création puis la lecture des notifications.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre que le module agit sur la table `notifications` au travers d'un exécuteur **injecté** et renvoie des `Notification` typées.

    ```mermaid
    classDiagram
        direction LR

        class notifications {
            <<module>>
            +notify(recipient, message, type, data, db) int
            +get_notifications(recipient, unread_only, limit, db) list
            +unread_count(recipient, db) int
            +mark_read(notification_id, db) bool
            +mark_all_read(recipient, db) int
        }

        class Notification {
            <<dataclass>>
            +int id
            +str recipient
            +str type
            +str message
            +dict data
            +bool read
            +str created_at
        }

        class notifications_table {
            <<table>>
            +id
            +recipient
            +type
            +message
            +data
            +read
            +created_at
        }

        class DBExecutor {
            +execute(sql, params)
            +fetch_all(sql, params)
        }

        class NotificationError {
            <<exception>>
        }

        notifications --> DBExecutor : exécuteur injecté
        DBExecutor --> notifications_table : lit / écrit
        notifications --> Notification : renvoie 0..*
        notifications ..> NotificationError : peut lever

    ```

    À retenir :

    - le module expose cinq fonctions, pas de classe à instancier ;
    - les avis vivent dans la table `notifications` ;
    - `get_notifications` renvoie des `Notification` typées ;
    - le module n'ouvre jamais de connexion : il reçoit un exécuteur.

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre un `notify` puis l'affichage des non lues d'un utilisateur.

    ```mermaid
    sequenceDiagram
        participant App as Code applicatif
        participant Notif as forge_mvc_notifications
        participant DB as Exécuteur BDD
        participant Table as notifications

        App->>Notif: notify("eleve.42", "Note publiée", type="info")
        Notif->>Notif: valide recipient et message
        Notif->>DB: execute(INSERT, params)
        DB->>Table: insère la ligne (read = false)
        Notif-->>App: id de la notification
        App->>Notif: get_notifications("eleve.42", unread_only=True)
        Notif->>DB: fetch_all(SELECT filtré, params)
        DB-->>Notif: lignes
        Notif-->>App: list[Notification] (plus récentes d'abord)
        App->>Notif: mark_read(id)
        Notif->>DB: execute(UPDATE read=true)

    ```

    À retenir :

    - une notification est créée comme **non lue** ;
    - `get_notifications` filtre par destinataire, et optionnellement par non lues ;
    - `mark_read` / `mark_all_read` basculent l'état lu ;
    - `unread_count` donne le nombre de non lues (pour un badge).

??? note "8. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `notify` | `notify(recipient, message, *, type="info", data=None, target_url=None, db=None) -> int` | crée une notification, renvoie son id |
    | `get_notifications` | `get_notifications(recipient, *, unread_only=False, limit=50, db=None) -> list[Notification]` | liste les notifications d'un destinataire |
    | `unread_count` | `unread_count(recipient, *, db=None) -> int` | nombre de non lues |
    | `mark_read` | `mark_read(notification_id, *, recipient=None, db=None) -> bool` | marque une notification lue, bornée au destinataire s'il est fourni |
    | `mark_all_read` | `mark_all_read(recipient, *, db=None) -> int` | marque tout lu, renvoie le nombre marqué |
    | `register_notification_routes` | `register_notification_routes(router, *, recipient_of, db=None)` | pose les quatre routes JSON sur le routeur |
    | `NotificationHttpController` | classe | les quatre handlers, si l'application préfère les brancher elle-même |
    | `serialize_notification` | `serialize_notification(notification) -> dict` | notification rendue en JSON, sans `recipient` |
    | `Notification` | dataclass | `id`, `recipient`, `type`, `message`, `data`, `read`, `created_at` |
    | `NotificationError` | exception (`ValueError`) | destinataire/message vide ou limite invalide |
    | `TABLE_NAME` | `"notifications"` | nom de la table |
    | `MAX_LIMIT` | `1000` | plafond du paramètre `limit` |
    | `DEFAULT_PAGE_SIZE` | `20` | taille de page des routes HTTP |

    `recipient` est un identifiant applicatif (par exemple `"eleve.42"` ou un login).

    `data` est un complément libre sérialisé en JSON ; `db` est l'exécuteur, omis il utilise le backend actif.

??? note "9. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Notifier un utilisateur | `notify(recipient, message)` |
    | Qualifier la notification | paramètre `type=...` |
    | Joindre des données | paramètre `data=...` |
    | Lister les notifications | `get_notifications(recipient)` |
    | Ne montrer que les non lues | `unread_only=True` |
    | Afficher un badge | `unread_count(recipient)` |
    | Marquer lu | `mark_read(id)` / `mark_all_read(recipient)` |
    | Marquer lu sans laisser toucher celle d'un autre | `mark_read(id, recipient=...)` |
    | Afficher les notifications dans une page | `register_notification_routes(router, recipient_of=...)` |
    | Créer la table | `forge notifications:init` puis `forge migration:apply` |

??? note "10. Exemples d'utilisation"

    ### 8.1 Notifier puis afficher les non lues

    ```python
    from forge_mvc_notifications import notify, get_notifications, unread_count

    notify("eleve.42", "Votre note de maths est publiée.", type="info")

    badge = unread_count("eleve.42")
    nouvelles = get_notifications("eleve.42", unread_only=True)
    ```

    ### 8.2 Marquer comme lu

    ```python
    from forge_mvc_notifications import mark_read, mark_all_read

    mark_read(notification_id)        # une seule
    mark_all_read("eleve.42")         # toutes celles du destinataire
    ```

    !!! tip "Aide-mémoire"
        Écrire, lire, compter, marquer :

        - `notify` pour créer ;
        - `get_notifications` / `unread_count` pour lire ;
        - `mark_read` / `mark_all_read` pour marquer lu.

??? note "11. Périmètre, validation et injection"

    `recipient` et `message` sont obligatoires ; sinon `notify` lève `NotificationError`.

    `limit` est borné à `MAX_LIMIT` (1000) ; une limite négative ou nulle lève `NotificationError`.

    !!! warning "Création de la table"
        Les fonctions supposent la table `notifications` présente.

        Créez-la avec `forge notifications:init` puis `forge migration:apply`, avant le premier appel.

    !!! note "Périmètre in-app"
        La V1 stocke des notifications **in-app** (lignes en base).

        Pour envoyer un email ou un push, combinez ce paquet avec `forge-mvc-jobs` (tâche de fond) et `forge-mvc-mail` : la livraison externe reste applicative.

    !!! note "SQL visible et indépendance du cœur"
        Le module ne crée jamais de connexion : il reçoit un exécuteur (`execute`, `fetch_all`).

        Le cœur de Forge ne dépend pas de `forge-mvc-notifications` : la dépendance va de l'opt-in vers le cœur.

## Voir aussi

- [Les notifications (store.py)](references/store.md) : détail des fonctions et du SQL.
- [Initialisation (notifications:init)](references/cli.md) : création de la table.
- [Les erreurs (errors.py)](references/errors.md) : détail de `NotificationError`.
- [Welcome-Notifications](welcome/debutant/notif-welcome.md) : parcours d'apprentissage.

## Déclaration de table

Le paquet ne livre plus de fichier SQL figé : il **déclare** sa table dans `tables.py`
(`NOTIFICATIONS`, plus la liste `MIGRATIONS`).
Le DDL est rendu pour le backend installé par `core.database.table_ddl`, puis écrit
dans `mvc/migrations/` par `forge notifications:init` (chantier `OPTIN-DDL-DIALECTAL`).
Le SQL reste donc relisible avant `forge migration:apply`, mais il est correct pour
MariaDB, SQLite, PostgreSQL comme SQL Server.

## Doubler une notification par un autre canal

Une notification in-app n'est vue que si son destinataire revient sur le site.

Pour une alerte qui compte, une facture impayée ou un incident, c'est trop tard, et l'opt-in n'offrait aucun moyen de doubler le canal (`NOTIF-MAIL-BRIDGE-001`).

Chaque application réécrivait la même chose à côté de `notify`, et l'y oubliait à un endroit sur trois : la notification partait, l'email non, et personne ne s'en apercevait avant la réclamation.

`notify` annonce désormais ce qu'il écrit.

```python
from forge_mvc_jobs import enqueue
from forge_mvc_mail import MAIL_JOB_TASK, MailMessage, message_to_payload
from forge_mvc_notifications import on_notification_created

@on_notification_created
def doubler_par_email(notification):
    if notification.type != "alerte":
        return
    enqueue(MAIL_JOB_TASK, message_to_payload(MailMessage(
        subject=f"Alerte : {notification.message}",
        to=adresse_de(notification.recipient),
        body_text=notification.message,
    )))
```

| Champ | Ce qu'il porte |
|---|---|
| `notification_id` | l'identifiant écrit, pour retrouver la ligne |
| `recipient` | le destinataire, tel que l'application le nomme |
| `message`, `type` | le contenu et sa qualification |
| `data` | le complément libre, souvent nécessaire pour composer le message |

!!! info "Le paquet annonce, il ne parle à personne"
    `forge-mvc-notifications` n'importe aucun autre opt-in, et un test le vérifie sur l'arbre syntaxique.

    `forge-mvc-mail` et `forge-mvc-jobs` sont les destinataires évidents sans être imposés : une application peut relayer vers un SMS, une alerte d'exploitation, ou rien du tout.

!!! warning "Un relais ne peut pas annuler une notification"
    L'annonce suit l'écriture. Si un relais lève, l'exception est avalée et journalisée en avertissement.

    La notification est déjà en base : faire échouer `notify` après coup laisserait l'appelant croire qu'elle n'existe pas, alors qu'elle s'affiche.
    Les relais suivants sont appelés malgré tout.

!!! info "Toutes les notifications ne méritent pas un email"
    Le `type` sert précisément à filtrer.

    Relayer chaque information doublerait le bruit, et le destinataire cesserait de lire les deux canaux.

!!! info "Passer par la file plutôt qu'envoyer directement"
    L'exemple mène à `enqueue` et non à `mailer.send`.

    Un envoi direct ferait attendre la requête qui a créé la notification, et une panne du relais SMTP deviendrait une panne de l'action de l'utilisateur.

## Lien cible et pagination

### Le lien vers ce que la notification annonce

Une notification annonce quelque chose, et l'utilisateur veut y aller.

Le lien pouvait se ranger dans `data`, qui est libre, mais rien ne l'y validait alors qu'il finit dans un `href` (`NOTIF-TARGET-URL-001`).

```python
notify("roger", "Facture impayée", type="alerte", target_url="/factures/12")
```

| Forme | Acceptée |
|---|---|
| `/factures/12` | oui, chemin interne |
| `https://exemple.test/a` | oui |
| `javascript:alert(1)` | non |
| `data:text/html,…` | non |
| `//ailleurs.test` | non |
| `factures/12` | non, chemin sans barre initiale |

!!! danger "Le lien est validé à l'écriture, pas à l'affichage"
    Une notification est écrite par l'application, mais son contenu vient souvent d'une saisie.

    Un schéma qui exécute du code au clic est refusé, y compris coupé par un blanc : certains navigateurs lisent `java<tabulation>script:` comme un schéma.
    Le refus empêche l'écriture : la ligne ne doit pas exister, plutôt que d'être filtrée à chaque affichage.

!!! info "Une URL protocole-relative est refusée"
    `//ailleurs.test/piege` emmène sur un autre domaine tout en ressemblant à un chemin interne.

### Paginer la liste

`before_id` ne rend que les notifications antérieures à cet identifiant.

```python
page1 = get_notifications("roger", limit=20)
page2 = get_notifications("roger", limit=20, before_id=page1[-1].id)
```

!!! warning "Pourquoi un curseur et non un décalage"
    Un `OFFSET` paginerait de travers.

    Une notification arrivée entre deux pages décale tout ce qui suit : la page 2 réafficherait la dernière ligne de la page 1 et en cacherait une autre.
    Une liste de notifications est justement celle qui reçoit des écritures pendant qu'on la parcourt.

Le curseur se combine à `unread_only`, et l'ordre reste du plus récent au plus ancien, ce qui fait de `before_id` un « plus ancien que ».

## Afficher les notifications dans une page

Le paquet savait écrire une notification et la relire depuis Python.
Il n'exposait aucune route, là où `forge-mvc-video` livre `register_video_routes` et `forge-mvc-iot` livre `register_iot_routes`.

Chaque application devait donc écrire son contrôleur, sa sérialisation JSON et son compteur de non-lus avant d'afficher quoi que ce soit (`NOTIF-HTTP-ROUTES-001`).

### Poser les routes

```python
from forge_mvc_notifications import register_notification_routes

from mvc.services.auth import utilisateur_courant


def _destinataire(request):
    utilisateur = utilisateur_courant(request)
    return f"professeur.{utilisateur.id}" if utilisateur else None


register_notification_routes(router, recipient_of=_destinataire)
```

L'appel est explicite, comme tout câblage de routes d'opt-in (ADR-030).

| Méthode | Chemin | Rend |
|---|---|---|
| `GET` | `/api/notifications/unread-count` | `{"data": {"count": 3}}` |
| `GET` | `/api/notifications` | `{"data": {"notifications": [...], "next_before_id": 41}}` |
| `POST` | `/api/notifications/{id}/read` | `{"data": {"marked": true}}` |
| `POST` | `/api/notifications/read-all` | `{"data": {"marked": 3}}` |

La liste accepte `limit`, `before_id` et `unread=1`.

!!! danger "Le destinataire vient de la session, jamais de la requête"
    C'est le point qui décide de tout le reste.

    Un destinataire est une chaîne libre, `professeur.42`, et Forge ne sait pas la dériver d'une session puisque la convention appartient à l'application.
    Elle fournit donc `recipient_of`, dont l'absence lève à l'enregistrement.

    Accepter `?recipient=professeur.7` donnerait à quiconque les notifications de n'importe qui.
    Ce n'est pas une précaution théorique, c'est la première chose qu'on écrit quand on veut aller vite.

!!! warning "Une session illisible ne rend pas 500, elle refuse"
    Un `recipient_of` qui lève est journalisé, et la requête est traitée comme non authentifiée.

    Se rabattre sur « personne » est acceptable, se rabattre sur « tout le monde » ne l'est pas.

!!! info "Le marquage est borné au destinataire"
    `POST /api/notifications/12/read` ne marque la notification 12 que si elle appartient au demandeur.

    Sans cette borne, l'identifiant seul suffirait à faire disparaître l'alerte de quelqu'un d'autre, et les identifiants d'une table se devinent.
    La réponse ne distingue pas « déjà lue » de « celle d'un autre », car les distinguer apprendrait à l'appelant qu'un identifiant existe ailleurs.

!!! info "`recipient` est absent du JSON rendu"
    Le client ne reçoit que les siennes.

    Le lui répéter à chaque ligne n'apprend rien et expose la convention de nommage interne de l'application.

### Rafraîchir l'écran sans le recharger

Ces routes rendent du JSON.
Elles ne poussent rien, n'ouvrent aucune connexion longue et ne fournissent aucun script.

Le rafraîchissement s'écrit avec HTMX, que le squelette livre déjà :

```html
<span id="badge-notifications"
      hx-get="/api/notifications/unread-count"
      hx-trigger="load, every 10s"
      hx-swap="innerHTML"></span>
```

!!! info "Pourquoi interroger plutôt que pousser"
    Une interrogation toutes les dix secondes coûte, pour quarante écrans ouverts, quatre requêtes par seconde servies en quelques millisecondes.

    Les tenir ouvertes en SSE coûterait quarante travailleurs immobilisés, soit davantage que ce qu'un serveur WSGI de taille courante en compte.
    Le choix se renverse à un autre ordre de grandeur, et une application qui l'atteint peut poser sa propre route sans rien changer ici.

!!! warning "Les mutations portent le jeton CSRF"
    Les deux `POST` ne sont pas dispensés de CSRF.

    Un appel HTMX doit donc envoyer le jeton, par exemple avec `hx-headers` posé une fois sur `<body>`.


## Ce qui est écrit est ce qui se relit

`notify` validait le destinataire sur sa forme **élaguée** et stockait la forme **brute**.

Une notification écrite pour `"  professeur.42  "` était donc invisible à `get_notifications`, `unread_count` et `mark_all_read`, qui interrogent la valeur telle qu'on la leur passe (`NOTIF-STORE-AS-VALIDATED-001`).

!!! danger "Écrite, comptée comme réussie, et jamais lue"
    Mesuré : écrit avec `recipient = '  professeur.42  '`, relu avec `'professeur.42'` rendait zéro notification et zéro non lue.

    Aucune erreur nulle part. C'est le pire mode de panne, tout paraît avoir marché.

!!! warning "Le paquet était incohérent d'une fonction à l'autre"
    `mark_read` élaguait, seule de toutes.

    Elle a été ajoutée par `NOTIF-HTTP-ROUTES-001`, qui a donc creusé l'écart sans le voir : une notification au destinataire mal saisi pouvait être listée, par correspondance brute, et pas marquée lue, par correspondance élaguée.

    La normalisation vit désormais à un seul endroit, et un garde-fou lu sur l'arbre syntaxique refuse qu'une fonction à destinataire la contourne.

## Le type d'une notification

`type` était le **seul** champ ni validé ni normalisé, alors que `recipient`, `message`, `data` et `target_url` le sont tous.

C'est pourtant celui sur lequel un client branche son affichage : `" Alerte "` et `"Alerte"` y produisent deux comportements.

| Refusé | Pourquoi |
|---|---|
| vide, ou fait d'espaces | il ne qualifie rien, et se rabattre en silence sur « info » donnerait un type que personne n'a écrit |
| plus de 64 caractères | c'est la largeur de la colonne, et tronquer donnerait un type sur lequel un gabarit brancherait à tort |

!!! info "Le vocabulaire reste ouvert, et ce n'est pas un oubli"
    Une application réelle observée écrit `type="copie_a_corriger"`.

    Fermer la liste à « info, alerte, tâche » casserait ce que Forge est censé servir.
    Ce qui est refusé n'est pas un mot inconnu, c'est une valeur qui ne peut pas qualifier.

    Le contraste avec `forge-mvc-workflow` et `forge-mvc-sessions-db`, dont les vocabulaires sont **fermés**, est délibéré : là bas, une nature inventée rendrait la métrique incomparable d'un projet à l'autre, ce qui est justement ce que ces champs doivent permettre.
