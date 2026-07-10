# Aide-mémoire Sessions BDD

Synthèse de l'API de `forge-mvc-sessions-db`, à garder sous la main.

## Mise en place

| Étape | Effet |
|-------|-------|
| Créer la table | `forge sessions:init` puis `forge migration:apply`. |
| Brancher le store | `forge.configure(session_store=DbSessionStore(ttl=3600))`. |

La table n'est jamais créée automatiquement.
L'opt-in expose deux commandes CLI (`sessions:init`, `sessions:gc`) ; le store lui-même s'importe et se branche par `forge.configure`.

## Construire le store

| Appel | Résultat |
|-------|----------|
| `DbSessionStore()` | Store adossé à `core.database.db`, TTL par défaut (`SESSION_TTL`). |
| `DbSessionStore(ttl=3600)` | Store dont les sessions expirent au bout de 3600 secondes. |
| `DbSessionStore(fetch_one=..., execute=...)` | Store à exécuteurs injectés, utile en test. |

## Cycle de vie d'une session

| Appel | Résultat |
|-------|----------|
| `create(data=None)` | Crée une session, renvoie son identifiant. |
| `get(sid)` | Données de session, ou `None` si absente ou expirée. |
| `set(sid, data)` | Fusionne (merge) des données dans une session existante. |
| `replace(sid, data)` | Remplace intégralement les données, sans merge. |
| `delete(sid)` | Supprime la session. |
| `regenerate(sid)` | Nouvel identifiant, données préservées (anti-fixation). |
| `touch_expiry(sid, ttl_seconds)` | Repousse l'expiration ; `False` si absente ou expirée. |

## Authentification et messages

| Appel | Résultat |
|-------|----------|
| `authenticate(sid, user_data, ttl_seconds)` | Rotation atomique : nouvelle session authentifiée. |
| `set_flash(sid, message, level="success")` | Stocke un message flash ; `False` si session absente. |
| `get_flash(sid)` | Lit et supprime le message flash ; `None` si absent. |

## Entretien

| Appel | Résultat |
|-------|----------|
| `cleanup_expired()` | Supprime les sessions expirées, renvoie le nombre de lignes supprimées. |

À déclencher depuis un cron applicatif : Forge ne planifie rien tout seul.

## Quel store choisir

| Store | Quand l'utiliser |
|-------|------------------|
| `MemorySessionStore` (cœur) | Mono-processus, tests, prototype ; perdu au redémarrage. |
| `FileSessionStore` (cœur) | Persistance simple sur disque, sans base. |
| `DbSessionStore` (opt-in) | Multi-worker Gunicorn, persistance après redémarrage, état partagé en base. |

## Rappel

Forge Core ne dépend pas du paquet : il ne fournit que `MemorySessionStore` et `FileSessionStore`.
Le SQL est portable (horodatages Python, pas de fonction date propriétaire), donc `DbSessionStore` fonctionne sur tous les backends via `core.database.db` (ADR-054).
