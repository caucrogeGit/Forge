# Erreurs de base de données portables

Ce document décrit `core/database/errors.py`, qui expose les erreurs de base de données qualifiées par Forge.

## Le problème

Chaque pilote signale un doublon ou une coupure à sa façon.
Une application qui attrape l'exception de son pilote n'est portable sur aucun autre backend, ce qui contredit le principe d'un cœur agnostique (ADR-054).

## Deux conditions qualifiées, pas une de plus

Forge ne traduit que ce qui a un usage évident pour l'appelant.

| Exception | Ce qu'elle dit | Réponse HTTP du cœur |
|---|---|---|
| `DatabaseError` | racine des erreurs qualifiées par Forge | sans objet |
| `UniqueViolationError` | une contrainte d'unicité a été violée | à l'application, typiquement une erreur de formulaire |
| `DatabaseUnavailableError` | aucune connexion utilisable, condition passagère | `503` avec `Retry-After` |

Toute autre exception remonte **inchangée** : le cœur n'enveloppe pas ce qu'il ne sait pas nommer.
Les violations de clé étrangère, de `NOT NULL` et de `CHECK` restent donc celles du pilote.
Elles n'ont pas d'usage métier assez net pour justifier une abstraction, et les qualifier à tort serait pire que de ne pas les qualifier.

## Le doublon

Les quatre backends officiels ont été mesurés.

| Backend | Exception du pilote | Signal discriminant |
|---|---|---|
| MariaDB | `mariadb.IntegrityError` | errno `1062` |
| SQLite | `sqlite3.IntegrityError` | message « UNIQUE constraint failed » |
| PostgreSQL | `psycopg.errors.UniqueViolation` | SQLSTATE `23505` |
| SQL Server | `pyodbc.IntegrityError` | numéro natif `2627` |

Le SQLSTATE ne suffit pas comme signal commun.
MariaDB et SQL Server renvoient tous deux `23000` pour un doublon, mais aussi pour une violation de clé étrangère ou de contrainte `NOT NULL`.
Une détection fondée sur le seul SQLSTATE serait donc fausse sur la moitié des backends.

```python
from core.database.errors import UniqueViolationError

try:
    user_id = create_user(form.value("email"))
except UniqueViolationError:
    form.add_error("email", "Cette adresse est déjà utilisée.")
```

Cette erreur ne dit pas **quelle** contrainte a été violée.
Sur une unicité composite, le nom de la contrainte n'est pas normalisé entre SGBD.
Une application qui doit distinguer plusieurs contraintes uniques sur la même table vérifie elle-même avant d'insérer.

## L'indisponibilité passagère

La question posée au backend est celle d'une **famille**, non d'une cause : le remède est-il d'attendre ?
Trois situations y répondent oui.

- **Le pool est saturé.** Aucune connexion ne s'est libérée dans le délai imparti.
- **La connexion était morte.** Le serveur l'avait fermée de son côté, et le pilote l'a remise en circulation sans le savoir.
- **La ressource est prise.** Un autre écrivain tient le verrou, cas d'un fichier SQLite ou d'une attente de verrou MariaDB.

| Backend | Signal discriminant |
|---|---|
| MariaDB | errno `2006` et `2013` (coupure), `2002`, `2003`, `2055` (serveur hors d'atteinte), `1205` (attente de verrou) |
| SQLite | codes `SQLITE_BUSY` et `SQLITE_LOCKED` |
| PostgreSQL | classe SQLSTATE `08`, arrêts `57P01` à `57P03`, `55P03` (attente de verrou bornée), et `OperationalError` sans SQLSTATE |
| SQL Server | classe SQLSTATE `08`, erreur native 1222 (attente de verrou bornée) |

L'attente de verrou n'est bornée que là où quelqu'un l'a bornée.
MariaDB plafonne à 50 secondes par défaut (`innodb_lock_wait_timeout`) ; PostgreSQL et SQL Server attendent indéfiniment tant que `lock_timeout` ou `SET LOCK_TIMEOUT` n'est pas posé ; SQLite suit `DB_POOL_TIMEOUT`.

Le cœur en fait un `503` avec `Retry-After`, jamais un `500`.
Un `500` annonce un bug du serveur et envoie chercher une erreur dans le code, là où le remède est d'élargir `DB_POOL_SIZE`, de raccourcir les requêtes, ou simplement d'attendre.

Une application peut aussi l'attraper pour dégrader un écran plutôt que le refuser.

```python
from core.database.errors import DatabaseUnavailableError

try:
    lignes = derniers_articles()
except DatabaseUnavailableError:
    lignes = []      # la page s'affiche sans sa liste
```

Cette erreur ne dit pas combien de temps attendre, ni laquelle des trois situations s'est produite.
Seul le fait qu'aucune connexion utilisable n'a pu servir la requête est établi.

Forge ne rejoue **pas** la requête à la place de l'appelant.
Réémettre en silence une écriture dont on ignore si le serveur l'a reçue serait la magie que le principe 3 refuse.
Le réessai appartient au client HTTP, que `Retry-After` renseigne.

### Ce qui n'entre pas dans la famille

L'interblocage est transitoire mais reste un `500` : errno `1213` en MariaDB, `40P01` en PostgreSQL, erreur native 1205 en SQL Server, qui n'a rien à voir avec l'errno 1205 de MariaDB malgré le numéro.
Le critère de la famille est « attendre suffit », or attendre n'y change rien.
Deux transactions ont pris leurs verrous dans des ordres incompatibles, et le remède est de revoir cet ordre.
Un `500` le laisse visible dans les journaux d'erreur, là où un `503` le rangerait parmi les conditions de routine.

Une panne de disque, de permission ou de corruption reste également un `500` : elle est durable.

## La traduction, et où elle a lieu

La reconnaissance appartient au **backend**, qui seul connaît son pilote, via `DatabaseBackend.is_unique_violation()` et `DatabaseBackend.is_unavailable()`.
Elle n'est pas sur `Dialect`, qui ne décrit que du SQL.

`core.database.qualify` interroge le backend actif et produit l'erreur portable correspondante.
Ce module a deux appelants, et c'est la raison de son existence : `core.database.db` qualifie l'échec d'une requête, `core.database.transaction` celui de la validation d'un bloc.
Tant que la traduction vivait dans le premier, un bloc transactionnel coupé en cours rendait l'exception du pilote.

L'exception d'origine reste accessible via `__cause__`, pour le diagnostic et la journalisation.

## Écrire un backend

Un backend tiers implémente `is_unique_violation(error)` et `is_unavailable(error)`.
La règle est d'être **strict** dans les deux cas : dans le doute, renvoyer faux.

Un faux positif d'unicité ferait passer une panne pour un doublon et afficherait à l'utilisateur une erreur de formulaire trompeuse.
Un faux positif d'indisponibilité masquerait une vraie panne derrière une invitation à réessayer.

Un backend n'est pas tenu de reconnaître toutes les causes, seulement de dire lesquelles il reconnaît.
SQLite n'a pas de connexion à perdre, les backends serveur n'ont pas de verrou de fichier.

Un backend qui n'implémente pas ces méthodes ne casse rien : l'exception d'origine remonte simplement telle quelle.

## Voir aussi

- [Les helpers SQL de Forge](db.md) : là où la traduction s'applique aux requêtes.
- [Les transactions dans Forge](transaction.md) : là où elle s'applique aux blocs.
