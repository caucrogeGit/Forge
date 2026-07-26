# Erreurs de base de données portables

Ce document décrit `core/database/errors.py`, qui expose les erreurs de base de données qualifiées par Forge.

## Le problème

Chaque pilote signale une violation d'unicité à sa façon.
Une application qui attrape l'exception de son pilote n'est portable sur aucun autre backend, ce qui contredit le principe d'un cœur agnostique (ADR-054).

Les quatre backends officiels ont été mesurés :

| Backend | Exception du pilote | Signal discriminant |
|---|---|---|
| MariaDB | `mariadb.IntegrityError` | errno `1062` |
| SQLite | `sqlite3.IntegrityError` | message « UNIQUE constraint failed » |
| PostgreSQL | `psycopg.errors.UniqueViolation` | SQLSTATE `23505` |
| SQL Server | `pyodbc.IntegrityError` | numéro natif `2627` |

Le SQLSTATE ne suffit pas comme signal commun.
MariaDB et SQL Server renvoient tous deux `23000` pour un doublon, mais aussi pour une violation de clé étrangère ou de contrainte `NOT NULL`.
Une détection fondée sur le seul SQLSTATE serait donc fausse sur la moitié des backends.

## La réponse de Forge

La reconnaissance appartient au **backend**, qui connaît son pilote, via `DatabaseBackend.is_unique_violation()`.
Elle n'est pas sur `Dialect`, qui ne décrit que du SQL.

`core.database.db` consulte le backend actif et lève `UniqueViolationError` à la place de l'exception du pilote.
Toute exception que le backend ne confirme pas remonte **inchangée** : le cœur n'enveloppe pas ce qu'il ne sait pas qualifier.

## Exceptions exposées

| Exception | Rôle |
|---|---|
| `DatabaseError` | racine des erreurs qualifiées par Forge |
| `UniqueViolationError` | une contrainte d'unicité a été violée |

## Usage

```python
from core.database.errors import UniqueViolationError

try:
    user_id = create_user(form.value("email"))
except UniqueViolationError:
    form.add_error("email", "Cette adresse est déjà utilisée.")
```

L'exception d'origine du pilote reste accessible via `__cause__`, pour le diagnostic et la journalisation.

## Ce que cette erreur ne dit pas

Elle ne dit pas **quelle** contrainte a été violée.
Sur une unicité composite, le nom de la contrainte n'est pas normalisé entre SGBD.
Une application qui doit distinguer plusieurs contraintes uniques sur la même table vérifie elle-même avant d'insérer.

Seul le doublon est traduit.
Les violations de clé étrangère, de `NOT NULL` et de `CHECK` remontent telles que le pilote les a levées : elles n'ont pas d'usage métier assez net pour justifier une abstraction, et les qualifier à tort serait pire que de ne pas les qualifier.

## Écrire un backend

Un backend tiers implémente `is_unique_violation(error) -> bool`.
La règle est d'être **strict** : dans le doute, renvoyer faux.
Un faux positif ferait passer une panne pour un doublon et afficherait à l'utilisateur une erreur de formulaire trompeuse.

Un backend qui n'implémente pas la méthode ne casse rien : l'exception d'origine remonte simplement telle quelle.
