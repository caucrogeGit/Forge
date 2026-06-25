# Sessions, Store de session Forge

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

## Vue d'ensemble

Forge gère les sessions HTTP via un backend de session (*session store*) configurable.
Le backend par défaut est `MemorySessionStore`, adapté au développement et aux tests,
sans dépendance externe.

Trois backends sont disponibles dans `core.sessions` :

| Backend | Stockage | Multi-processus | Usage recommandé |
|---|---|---|---|
| `MemorySessionStore` | Mémoire Python | Non | Développement, tests |
| `FileSessionStore` | Fichiers JSON sur disque | Non (verrou interne) | Développement persistant |
| `MariaDbSessionStore` | Table MariaDB `forge_sessions` | Oui | Production multi-worker |

---

## Configuration du store

```python
import core.forge as forge
from core.sessions import FileSessionStore

store = FileSessionStore(sessions_dir="storage/sessions")
forge.configure(session_store=store)
```

Comportement garanti par `forge.configure(session_store=...)` :

- si `session_store` est fourni, Forge l'utilise pour toutes les opérations de session ;
- si `session_store=None`, Forge revient au `MemorySessionStore` par défaut ;
- si la valeur ne respecte pas le protocole `SessionStore`, une `TypeError` est levée avec un message explicite ;
- le store configuré est résolu à chaque opération session, un `configure()` tardif (après import de `core.security.session`) est pris en compte.

---

## Contrat du store (protocole `SessionStore`)

Défini dans `core/sessions/contract.py` comme un `Protocol` Python (`runtime_checkable`).
Tout store personnalisé doit implémenter les dix méthodes suivantes.

### `create(data=None) -> str`

Crée une nouvelle session et retourne son identifiant (64 caractères hexadécimaux).

- `data` : données initiales à fusionner dans la session (optionnel)
- Les implémentations Forge ajoutent automatiquement `authenticated`, `user`, `csrf_token`, `expires_at`
- Un store personnalisé minimal peut omettre ces clés si `core/security/session.py` n'est pas utilisé directement

### `get(session_id) -> dict | None`

Retourne les données de la session ou `None` si absente ou expirée.

- Retourne `None` si `session_id` est invalide (format non conforme)
- Retourne `None` si la session a expiré (le comportement d'expiration est à la charge du store)

### `set(session_id, data) -> None`

Met à jour (*merge*) les données d'une session existante.

- Les clés de `data` sont ajoutées ou remplacées dans la session existante
- Les clés absentes de `data` sont conservées
- Si la session n'existe pas, ne fait rien (pas d'erreur)

### `replace(session_id, data) -> None`

Remplace intégralement les données de la session.

- Contrairement à `set()`, les clés absentes de `data` sont supprimées
- Si la session n'existe pas, ne fait rien

### `delete(session_id) -> None`

Supprime la session. Sans effet si la session n'existe pas.

### `regenerate(session_id) -> str`

Crée un nouveau `session_id` en conservant les données existantes, protège contre la fixation de session.

- Supprime l'ancienne session
- Retourne le nouveau `session_id`

### `authenticate(session_id, user_data, ttl_seconds) -> str | None`

Rotation atomique à l'authentification : invalide l'ancienne session, crée une nouvelle avec l'utilisateur et un nouveau CSRF.

- Retourne le nouveau `session_id`, ou `None` si la session source n'existe pas
- `user_data` est un dict libre (id, login, rôles, etc.)

### `touch_expiry(session_id, ttl_seconds) -> bool`

Repousse l'expiration de la session de `ttl_seconds` secondes.

- Retourne `True` si l'expiration a été repoussée
- Retourne `False` si la session n'existe pas ou est déjà expirée

### `set_flash(session_id, message, level="success") -> bool`

Stocke un message flash dans la session (affiché une seule fois).

- `level` : `"success"`, `"error"`, `"warning"`, `"info"` (la valeur est libre, Forge ne valide pas)
- Retourne `False` si la session n'existe pas

### `get_flash(session_id) -> dict | None`

Lit et supprime atomiquement le message flash.

- Retourne `{"message": ..., "level": ...}` ou `None` si absent
- Atomique : lecture + suppression en une seule opération

---

## Backends disponibles

### `MemorySessionStore`

```python
from core.sessions import MemorySessionStore

store = MemorySessionStore(ttl=3600)  # TTL en secondes, défaut 3600
forge.configure(session_store=store)
```

- Backend par défaut, utilisé sans appel à `forge.configure()`
- Sessions stockées en mémoire Python (dictionnaire)
- Sessions perdues au redémarrage du processus
- Thread-safe via `threading.RLock` (reentrant), voir section [Thread-safety et limites](#thread-safety-et-limites-de-memorysessionstore)
- **Non adapté au multi-processus** : chaque worker a son propre espace mémoire
- Nettoyage automatique des sessions expirées à la création (`_cleanup()`)

### `FileSessionStore`

```python
from core.sessions import FileSessionStore

store = FileSessionStore(sessions_dir="storage/sessions", ttl=3600)
forge.configure(session_store=store)
```

- Chaque session est un fichier `<sessions_dir>/<session_id>.json`
- Persiste entre les redémarrages du processus
- Thread-safe (RLock interne)
- **Non adapté au multi-processus concurrent** sur le même dossier sans verrou externe
- Le format `session_id` est validé (`^[0-9a-f]{64}$`) avant tout accès disque, pas de traversée de chemin possible
- Méthode supplémentaire : `cleanup_expired() -> int` (supprime les fichiers expirés, retourne le nombre supprimé)
- Dossier créé automatiquement si absent

### `MariaDbSessionStore`

```python
from core.sessions import MariaDbSessionStore

store = MariaDbSessionStore(ttl=3600)
forge.configure(session_store=store)
```

**Prérequis** : la table `forge_sessions` doit exister dans la base de données.
Script de création : `mvc/models/sql/forge_sessions.sql`

```sql
CREATE TABLE IF NOT EXISTS forge_sessions (
    session_id CHAR(64)     NOT NULL,
    data       LONGTEXT     NOT NULL,
    expire_at  DATETIME     NOT NULL,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id),
    INDEX idx_forge_sessions_expire_at (expire_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

- Sessions partagées entre processus via MariaDB
- Persiste après redémarrage
- L'expiration est gérée par la clause `expire_at > NOW()` dans les requêtes SQL
- Méthode supplémentaire : `cleanup_expired() -> int` (supprime les lignes expirées)
- Les callables `fetch_one` et `execute` sont injectables pour les tests sans MariaDB réelle
- Utilise la connexion Forge configurée via `core.database.db`

---

## Thread-safety et limites de MemorySessionStore

### Ce que garantit le verrou interne

`MemorySessionStore` utilise un `threading.RLock` (verrou réentrant). Ce verrou
protège l'intégralité de ses dix méthodes publiques (`create`, `get`, `set`,
`replace`, `delete`, `regenerate`, `authenticate`, `touch_expiry`, `set_flash`,
`get_flash`) ainsi que les opérations internes (`_cleanup`, `purge_all`).

Dans un même processus Python, les garanties sont les suivantes :

- deux threads peuvent créer des sessions simultanément sans générer d'IDs dupliqués ;
- un thread peut lire une session pendant qu'un autre l'écrit, aucun état partiel n'est observable ;
- la suppression et la régénération sont atomiques, pas de session fantôme, pas de double suppression silencieuse ;
- `create()` peut appeler `_cleanup()` en interne sans deadlock (propriété du `RLock` réentrant).

Ces garanties sont confirmées par `tests/test_concurrency_session_001.py`, qui exécute
50 threads en parallèle sur les opérations `create`, `get`, `set`, `delete`,
`regenerate`, `authenticate`, `set_flash` et `get_flash`.

### Ce que le verrou ne garantit pas

Le verrou interne est **intra-processus uniquement**. Il ne couvre pas :

- **le partage entre processus**, chaque worker (Gunicorn, uWSGI) a son propre espace
  mémoire ; les sessions créées par un worker ne sont pas visibles des autres ;
- **la persistance**, les sessions sont perdues au redémarrage du processus ;
- **la cohérence entre instances**, plusieurs objets `MemorySessionStore` dans le même
  programme ne partagent pas leurs données.

### Contextes d'usage

| Contexte | Acceptabilité | Raison |
|---|---|---|
| Développement local | **Acceptable** | Un seul processus, sessions non critiques |
| Tests automatisés | **Recommandé** | Isolation garantie, aucune dépendance externe |
| Usage mono-processus simple | **Acceptable avec réserve** | Sessions perdues au redémarrage |
| Production mono-worker | **Déconseillé** | Sessions perdues au redémarrage |
| Production multi-worker (Gunicorn, uWSGI) | **Ne pas utiliser** | Sessions non partagées entre workers |
| Production multi-processus | **Ne pas utiliser** | Sessions non partagées entre processus |
| Besoin de persistance entre redémarrages | **Ne pas utiliser** | Utiliser `FileSessionStore` ou `MariaDbSessionStore` |

### Alternatives recommandées

Pour un usage persistant ou multi-worker, deux backends sont disponibles sans
dépendance externe supplémentaire :

- **`FileSessionStore`**, persiste entre les redémarrages, adapté à un seul processus
  ou à un développement persistant local ;
- **`MariaDbSessionStore`**, sessions partagées entre workers via MariaDB, adapté à la
  production multi-processus.

```python
from core.sessions import MariaDbSessionStore
import core.forge as forge

forge.configure(session_store=MariaDbSessionStore(ttl=3600))
```

Leur documentation complète est dans la section [Backends disponibles](#backends-disponibles)
ci-dessus.

---

## Exemple de store personnalisé

Un store personnalisé doit implémenter les dix méthodes du protocole `SessionStore`.
L'implémentation minimale fonctionnelle :

```python
import secrets
import time
from core.sessions import SessionStore


class DictSessionStore:
    """Store en mémoire minimal — exemple pédagogique."""

    def __init__(self, ttl: int = 3600) -> None:
        self._data: dict[str, dict] = {}
        self._ttl = ttl

    def create(self, data: dict | None = None) -> str:
        sid = secrets.token_hex(32)
        self._data[sid] = {**(data or {}), "expires_at": time.time() + self._ttl}
        return sid

    def get(self, session_id: str) -> dict | None:
        s = self._data.get(session_id)
        if s is None or time.time() > s.get("expires_at", 0):
            return None
        return s

    def set(self, session_id: str, data: dict) -> None:
        if session_id in self._data:
            self._data[session_id].update(data)

    def replace(self, session_id: str, data: dict) -> None:
        if session_id in self._data:
            self._data[session_id] = data

    def delete(self, session_id: str) -> None:
        self._data.pop(session_id, None)

    def regenerate(self, session_id: str) -> str:
        new_id = secrets.token_hex(32)
        self._data[new_id] = self._data.pop(session_id, {})
        return new_id

    def authenticate(self, session_id: str, user_data: dict, ttl_seconds: int) -> str | None:
        s = self._data.pop(session_id, None)
        if s is None:
            return None
        new_id = secrets.token_hex(32)
        self._data[new_id] = {**s, "authenticated": True, "user": user_data,
                               "expires_at": time.time() + ttl_seconds}
        return new_id

    def touch_expiry(self, session_id: str, ttl_seconds: int) -> bool:
        s = self._data.get(session_id)
        if s is None:
            return False
        s["expires_at"] = time.time() + ttl_seconds
        return True

    def set_flash(self, session_id: str, message: str, level: str = "success") -> bool:
        s = self._data.get(session_id)
        if s is None:
            return False
        s["flash"] = {"message": message, "level": level}
        return True

    def get_flash(self, session_id: str) -> dict | None:
        s = self._data.get(session_id)
        if s is None:
            return None
        return s.pop("flash", None)
```

Validation via `forge.configure()` :

```python
import core.forge as forge

forge.configure(session_store=DictSessionStore())
```

---

## Limites actuelles

- **Thread-safety mémoire** : voir section [Thread-safety et limites de MemorySessionStore](#thread-safety-et-limites-de-memorysessionstore), livrée par SESSIONS-MEMORY-THREADSAFE-DOC-001.
- **Double pile auth/session** : `core/security/session.py` (API legacy FR) et `core/auth/session.py` (API moderne EN) coexistent. La déduplication et la décision de l'API canonique sont traitées en Phase 4 (AUTH-SESSION-DEDUP-001).
- **Production hardening** : `MariaDbSessionStore` est fonctionnel mais sa robustesse production (reconnexion, pool, timeout) dépend de la configuration de `core.database.db`, non documentée dans ce ticket.
- **MFA/RBAC** : non concernés par les stores de session directement.

---

## Tickets liés

| Ticket | Description |
|---|---|
| SESSIONS-CONFIGURABLE-STORE-001 | `forge.configure(session_store=...)`, livré en Phase 3.1 |
| SESSIONS-STORE-CONTRACT-DOC-001 | Ce document, livré en Phase 3.2 |
| SESSIONS-MEMORY-THREADSAFE-DOC-001 | Documentation thread-safety MemorySessionStore, livré en Phase 3.3 |
| AUTH-SESSION-DEDUP-001 | Déduplication double pile auth/session, Phase 4 |
