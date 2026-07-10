# Le store (store.py)

Le module `forge_mvc_sessions_db.store` définit `DbSessionStore`, l'implémentation BDD du contrat `SessionStore`.

## Rôle

`DbSessionStore` stocke chaque session dans la table `forge_sessions` et délègue tout accès à la base aux exécuteurs injectés.

Il implémente l'intégralité du contrat `core.sessions.SessionStore`, donc il se configure comme n'importe quel autre store via `forge.configure(session_store=...)`.

## Constructeur

```python
DbSessionStore(fetch_one=None, execute=None, ttl=SESSION_TTL)
```

- `fetch_one` : callable `(sql, params) -> dict | None` ; par défaut `core.database.db.fetch_one`.
- `execute` : callable `(sql, params) -> int` ; par défaut `core.database.db.execute`.
- `ttl` : durée de vie d'une session en secondes ; par défaut `SESSION_TTL` du cœur.

Les callables injectables permettent de tester le store sans base réelle.

## Méthodes

| Méthode | Rôle |
|---|---|
| `create(data=None) -> str` | Crée une session (structure Forge standard : `authenticated`, `user`, `csrf_token`, `expires_at`) et retourne son identifiant hexadécimal de 64 caractères. |
| `get(session_id) -> dict | None` | Retourne les données de session, ou `None` si l'identifiant est invalide, la session absente, expirée ou corrompue. |
| `set(session_id, data) -> None` | Fusionne `data` dans une session existante non expirée. |
| `replace(session_id, data) -> None` | Remplace intégralement les données (les clés absentes disparaissent). |
| `delete(session_id) -> None` | Supprime la session. |
| `regenerate(session_id) -> str` | Génère un nouvel identifiant en préservant les données : protège contre la fixation de session. |
| `authenticate(session_id, user_data, ttl_seconds) -> str | None` | Rotation atomique : invalide l'ancienne session, en crée une nouvelle authentifiée. |
| `touch_expiry(session_id, ttl_seconds) -> bool` | Repousse l'expiration ; `False` si la session n'existe pas ou est expirée. |
| `set_flash(session_id, message, level="success") -> bool` | Stocke un message flash. |
| `get_flash(session_id) -> dict | None` | Lit et supprime atomiquement le message flash. |
| `cleanup_expired() -> int` | Supprime les sessions expirées, retourne le nombre de lignes supprimées. |

## Sécurité et robustesse

- L'identifiant de session est validé (`^[0-9a-f]{64}$`) avant tout accès à la base, ce qui écarte toute injection par l'identifiant.
- Une session au JSON corrompu est traitée comme absente et supprimée à la lecture.
- Les données sont sérialisées en JSON : aucun `pickle`, `marshal`, `eval` ni `exec`.

## Portabilité

Le SQL n'emploie aucune fonction date propriétaire : les horodatages sont calculés côté Python et passés en paramètres.

Le store fonctionne donc à l'identique sur tous les backends BDD (MariaDB, SQLite, PostgreSQL, SQL Server), via `core.database.db` (ADR-054).
