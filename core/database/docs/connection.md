# L'emprunt de connexion dans Forge

Ce document décrit l'emprunt et la restitution d'une connexion à la base de données.

C'est une API interne du cœur : le code applicatif passe en pratique par les helpers SQL.

## 1. Rôle

Le module `core.database.connection` emprunte une connexion au backend BDD actif et la restitue après usage.

Ouvrir une connexion à chaque requête HTTP serait coûteux.
Selon le backend installé, la connexion peut provenir d'un pool puis y retourner plutôt que d'être détruite.

Depuis ADR-054, le cœur est agnostique BDD : ce module ne connaît plus aucun SGBD particulier.
Il délègue l'acquisition et la restitution au backend résolu par `core.database.backend.get_backend()` (l'opt-in installé, par exemple `forge-mvc-mariadb`).

C'est une API interne.
En usage normal, on passe par les helpers SQL (`fetch_one`, `fetch_all`, `execute`, `insert`) qui empruntent et restituent la connexion pour vous.

## 2. Vue d'ensemble rapide

| Élément | Valeur |
|---|---|
| Module | `core.database.connection` |
| Couche | Accès base de données |
| Rôle | emprunter et restituer une connexion BDD |
| Dépend de | `core.database.backend` |
| API publique | `get_connection`, `close_connection` |
| Statut | API interne (préférer les helpers SQL) |

Ce module est une frontière fine entre le cœur et le backend BDD opt-in.
Il ne porte aucune logique propre à un SGBD.

## 3. Schéma UML

Le diagramme montre la délégation au backend résolu par ADR-054.

```mermaid
classDiagram
    direction LR

    class connection {
        <<module core.database.connection>>
        +get_connection() Any
        +close_connection(connection) None
    }

    class backend {
        <<module core.database.backend>>
        +get_backend() DatabaseBackend
    }

    class DatabaseBackend {
        +get_connection() Any
        +close_connection(connection) None
    }

    connection ..> backend : get_backend()
    backend --> DatabaseBackend : résout l'opt-in installé
    connection ..> DatabaseBackend : délègue
```

À retenir :

- `connection` ne connaît aucun SGBD ;
- il délègue au backend actif résolu par `core.database.backend` ;
- chaque emprunt par `get_connection()` doit être suivi d'un `close_connection()` ;
- selon le backend, la connexion retourne à un pool plutôt que d'être détruite.

## 4. API publique

| Fonction | Signature | Rôle |
|---|---|---|
| `get_connection` | `get_connection() -> Any` | emprunter une connexion auprès du backend BDD actif |
| `close_connection` | `close_connection(connection) -> None` | restituer la connexion au backend BDD actif |

## 5. Contextes d'utilisation

| Besoin | Élément |
|---|---|
| Exécuter une requête courante | helpers SQL `fetch_*` / `execute` / `insert` (ne pas appeler ce module) |
| Cas avancé non couvert par les helpers | `get_connection()` puis `close_connection()` systématique |
| Transaction multi-instructions | bloc `with transaction()` (qui s'appuie sur ce module) |

## 6. Exemples d'utilisation

En usage normal, on ne touche pas à ce module : on passe par les helpers SQL.

```python
from core.database.db import fetch_all

rows = fetch_all("SELECT id, name FROM categories ORDER BY name")
```

Pour un cas avancé non couvert par les helpers, l'emprunt direct reste possible, mais la restitution doit être systématique.

```python
from core.database.connection import get_connection, close_connection

connection = get_connection()
try:
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS total FROM article")
    total = cursor.fetchone()["total"]
    connection.commit()
finally:
    close_connection(connection)
```

!!! note "Préférer les helpers"
    Cet exemple montre la mécanique interne.

    Dans le code applicatif, `fetch_*`, `execute` et `insert` gèrent l'emprunt, le commit et la restitution à votre place.

## Voir aussi

- [Les helpers SQL dans Forge](db.md) : l'API publique qui s'appuie sur cet emprunt.
- [Les transactions dans Forge](transaction.md) : grouper des écritures sur une même connexion.
