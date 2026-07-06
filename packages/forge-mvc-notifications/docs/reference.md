# Les notifications in-app dans Forge (forge-mvc-notifications)

Ce document explique ce que fait l'opt-in `forge-mvc-notifications`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-notifications` crée des notifications destinées aux utilisateurs dans une table `notifications`, les lit, et les marque comme lues.

Le cœur de Forge ignore tout des notifications : ce paquet fournit la table et les helpers, l'application décide de qui notifier et quand.

## 1. Rôle du module

Une application a souvent besoin d'avertir un utilisateur : élève inscrit, note publiée, devoir à rendre.

L'opt-in stocke ces avis dans une table SQL (`notifications`) et expose des fonctions pour notifier, lister, compter les non lues et marquer comme lu.

Son périmètre V1 est **in-app** : des lignes en base. La livraison hors application (email, push) reste applicative, par exemple en combinant ce paquet avec `forge-mvc-jobs` et `forge-mvc-mail`.

## 2. Installation et désinstallation

### Installation

```bash
pip install --pre forge-mvc-notifications
forge opt-in:enable notifications
```

`opt-in:enable` inscrit l'opt-in dans `optins/registry.py` (ADR-061) (l'opt-in s'importe et s'utilise directement, sans route).
`forge opt-in:install notifications` affiche la commande `pip` sans l'exécuter.

### Désinstallation

```bash
forge opt-in:disable notifications
pip uninstall forge-mvc-notifications
```

`opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre (le code n'était pas câblé), sans toucher au paquet.
`forge opt-in:remove notifications` affiche la commande `pip uninstall` sans l'exécuter.

## 3. Vue d'ensemble rapide

| Élément | Valeur |
|---|---|
| Paquet | `forge-mvc-notifications` |
| Module | `forge_mvc_notifications` |
| Catégorie | Communication (ADR-055) |
| Couche | opt-in (brique optionnelle) |
| Dépend de | `forge-mvc` et un backend BDD installé (ADR-054) |
| API publique | `notify`, `get_notifications`, `unread_count`, `mark_read`, `mark_all_read`, `Notification` |
| Table SQL | `notifications` (`TABLE_NAME`, `CREATE_TABLE_SQL`) |
| Limite de lecture | `MAX_LIMIT` = 1000 entrées |
| Exception liée | `NotificationError` si destinataire/message vide ou limite invalide |
| Périmètre | in-app (V1) ; livraison email/push à charge de l'application |
| Installation | `pip install --pre forge-mvc-notifications` |

## 4. Schémas UML

Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

Le diagramme de classe montre l'API, l'objet renvoyé et la table.

Le diagramme de séquence montre la création puis la lecture des notifications.

### 4.1 Diagramme de classe

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

### 4.2 Diagramme de séquence

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

## 5. API publique

| Élément | Signature | Rôle |
|---|---|---|
| `notify` | `notify(recipient, message, *, type="info", data=None, db=None) -> int` | crée une notification, renvoie son id |
| `get_notifications` | `get_notifications(recipient, *, unread_only=False, limit=50, db=None) -> list[Notification]` | liste les notifications d'un destinataire |
| `unread_count` | `unread_count(recipient, *, db=None) -> int` | nombre de non lues |
| `mark_read` | `mark_read(notification_id, *, db=None) -> bool` | marque une notification lue |
| `mark_all_read` | `mark_all_read(recipient, *, db=None) -> int` | marque tout lu, renvoie le nombre marqué |
| `Notification` | dataclass | `id`, `recipient`, `type`, `message`, `data`, `read`, `created_at` |
| `NotificationError` | exception (`ValueError`) | destinataire/message vide ou limite invalide |
| `TABLE_NAME` | `"notifications"` | nom de la table |
| `CREATE_TABLE_SQL` | constante SQL | création de la table |
| `MAX_LIMIT` | `1000` | plafond du paramètre `limit` |

`recipient` est un identifiant applicatif (par exemple `"eleve.42"` ou un login).

`data` est un complément libre sérialisé en JSON ; `db` est l'exécuteur, omis il utilise le backend actif.

## 6. Contextes d'utilisation

| Besoin | Élément |
|---|---|
| Notifier un utilisateur | `notify(recipient, message)` |
| Qualifier la notification | paramètre `type=...` |
| Joindre des données | paramètre `data=...` |
| Lister les notifications | `get_notifications(recipient)` |
| Ne montrer que les non lues | `unread_only=True` |
| Afficher un badge | `unread_count(recipient)` |
| Marquer lu | `mark_read(id)` / `mark_all_read(recipient)` |
| Créer la table | `CREATE_TABLE_SQL` ou `forge notifications:init` |

## 7. Exemples d'utilisation

### 7.1 Notifier puis afficher les non lues

```python
from forge_mvc_notifications import notify, get_notifications, unread_count

notify("eleve.42", "Votre note de maths est publiée.", type="info")

badge = unread_count("eleve.42")
nouvelles = get_notifications("eleve.42", unread_only=True)
```

### 7.2 Marquer comme lu

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

## 8. Périmètre, validation et injection

`recipient` et `message` sont obligatoires ; sinon `notify` lève `NotificationError`.

`limit` est borné à `MAX_LIMIT` (1000) ; une limite négative ou nulle lève `NotificationError`.

!!! warning "Création de la table"
    Les fonctions supposent la table `notifications` présente.

    Créez-la avec `forge notifications:init` (ou exécutez `CREATE_TABLE_SQL`) avant le premier appel.

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
- [Progression Notifications](welcome/installation.md) : apprendre l'opt-in pas à pas.
