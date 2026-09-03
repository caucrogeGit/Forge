# pyright: strict
"""Store de session persistant adossé à la BDD (ex-MariaDbSessionStore, ADR-054).

Stocke les sessions dans la table `forge_sessions`, partagées entre processus
Forge via une base commune (utile en multi-worker). Le backend par défaut du
cœur reste `MemorySessionStore`.

Agnostique du SGBD : tout le SQL passe par `core.database.db`, dispatché vers le
backend BDD actif. Les horodatages (`created_at`, `updated_at`, comparaison
d'expiration) sont calculés côté Python **en UTC** et passés en paramètres, pour
éviter toute fonction SQL propriétaire (`NOW()` MariaDB, `GETDATE()` SQL Server,
`datetime('now')` SQLite) et rester portable. Python est l'unique autorité des
horodatages : le DDL ne pose pas de `DEFAULT CURRENT_TIMESTAMP` (pas de double
horloge SGBD/Python, retour terrain 016 F37).

Concurrence (retour terrain 016 F36) : chaque read-modify-write est protégé par
une **concurrence optimiste** portable. La table porte une colonne `version` ;
toute écriture est gardée par `WHERE session_id = ? AND version = ?` et
incrémente `version`. Si `rowcount` vaut 0, un autre writer a modifié la ligne
entre-temps : on recharge et on retente (pas de `SELECT ... FOR UPDATE`, non
portable). Cela garantit l'absence de lost-update et l'unicité du message flash.

Table requise : `forge_sessions`, à créer dans le projet avant usage (elle
n'est pas créée automatiquement). `forge sessions:init` copie la migration
embarquée dans `mvc/migrations/` ; `forge migration:apply` l'applique (ADR-071).
"""

from __future__ import annotations

from forge_mvc_sessions_db.ttl import (
    KIND_ANONYMOUS,
    KIND_AUTHENTICATED,
    normalize_kind,
    ttl_for,
)

import json
import re
import secrets

from core.sessions.contract import HANDLE_LENGTH, SessionSummary
from core.sessions.keys import SESSION_KEY_AUTH_USER_ID
import time
from datetime import datetime, timezone
from typing import Any, Callable, cast

# TTL par défaut du store, en secondes. Constante locale et neutre : un store
# persistant ne tire pas son défaut du module *mémoire* du cœur (retour 016 F37).
DEFAULT_SESSION_TTL = 3600

# Tentatives d'écriture sous garde de version avant d'abandonner (retour 016 F36).
# Un conflit exige deux écritures concurrentes sur la *même* session ; huit
# tentatives couvrent tout scénario réaliste.
_MAX_WRITE_RETRIES = 8

_SESSION_ID_RE = re.compile(r"^[0-9a-f]{64}$")

# Signatures des accesseurs DB injectables (tests) et de leurs défauts.
_FetchOne = Callable[[str, "tuple[Any, ...]"], "dict[str, Any] | None"]
_Execute = Callable[[str, "tuple[Any, ...]"], int]
_FetchAll = Callable[[str, "tuple[Any, ...]"], "list[dict[str, Any]]"]

# ── Requêtes SQL (portables : horodatages passés en paramètres, garde de version) ─

_SQL_INSERT = (
    "INSERT INTO forge_sessions"
    " (session_id, data, user_id, kind, expire_at, version, created_at, updated_at)"
    " VALUES (?, ?, ?, ?, ?, 0, ?, ?)"
)
_SQL_SELECT = (
    "SELECT data, version FROM forge_sessions WHERE session_id = ? AND expire_at > ?"
)
_SQL_UPDATE = (
    "UPDATE forge_sessions SET data = ?, user_id = ?, updated_at = ?,"
    " version = version + 1"
    " WHERE session_id = ? AND version = ?"
)
_SQL_UPDATE_EXPIRY = (
    "UPDATE forge_sessions SET data = ?, user_id = ?, expire_at = ?, updated_at = ?,"
    " version = version + 1"
    " WHERE session_id = ? AND version = ?"
)
_SQL_DELETE = "DELETE FROM forge_sessions WHERE session_id = ?"
_SQL_DELETE_VERSIONED = "DELETE FROM forge_sessions WHERE session_id = ? AND version = ?"
_SQL_CLEANUP = "DELETE FROM forge_sessions WHERE expire_at < ?"
_SQL_LIST_FOR_USER = (
    "SELECT session_id, created_at, expire_at FROM forge_sessions "
    "WHERE user_id = ? AND expire_at > ? ORDER BY expire_at DESC"
)
_SQL_DELETE_FOR_USER = "DELETE FROM forge_sessions WHERE user_id = ?"
_SQL_DELETE_FOR_USER_EXCEPT = (
    "DELETE FROM forge_sessions WHERE user_id = ? AND session_id <> ?"
)

_DATETIME_FMT = "%Y-%m-%d %H:%M:%S"


def _horodatage(valeur: object) -> "float | None":
    """Date de base en horodatage Unix, ou `None`.

    Les pilotes rendent un `datetime` ou une chaîne selon le backend : les deux
    formes sont acceptées, et une valeur illisible rend `None` plutôt que de
    faire échouer l'affichage d'une liste de sessions.
    """
    if valeur is None:
        return None
    if isinstance(valeur, (int, float)):
        return float(valeur)
    if isinstance(valeur, datetime):
        return valeur.timestamp()
    try:
        return datetime.strptime(str(valeur), _DATETIME_FMT).timestamp()
    except ValueError:
        return None


def _user_id_of(session: "dict[str, Any]") -> "str | None":
    """Identité authentifiée d'une session, rendue en texte, ou `None`.

    Recopiée dans la colonne `user_id` à chaque écriture pour que la révocation
    soit une requête indexée (SESSIONS-DELETE-FOR-USER-001). Le rendu en texte
    est délibéré : l'identité applicative peut être un entier comme une chaîne,
    et la colonne doit rester la même sur les quatre backends.
    """
    value = session.get(SESSION_KEY_AUTH_USER_ID)
    return None if value is None else str(value)


# ── Accesseurs DB par défaut (lazy — pas de connexion à l'import) ─────────────

def _default_fetch_one(sql: str, params: "tuple[Any, ...]") -> "dict[str, Any] | None":
    from core.database.db import fetch_one
    return fetch_one(sql, params)


def _default_fetch_all(sql: str, params: "tuple[Any, ...]") -> "list[dict[str, Any]]":
    from core.database.db import fetch_all

    return fetch_all(sql, list(params))


def _default_execute(sql: str, params: "tuple[Any, ...]" = ()) -> int:
    from core.database.db import execute
    return execute(sql, params)


def _dt(unix_ts: float) -> str:
    """Convertit un timestamp Unix en DATETIME UTC (format canonique portable)."""
    return datetime.fromtimestamp(unix_ts, timezone.utc).strftime(_DATETIME_FMT)


def _now_str() -> str:
    """Horodatage courant UTC, au même format que `_dt` (comparaisons cohérentes)."""
    return datetime.now(timezone.utc).strftime(_DATETIME_FMT)


# ── Store ─────────────────────────────────────────────────────────────────────

class DbSessionStore:
    """Backend de session utilisant la table BDD `forge_sessions`.

    Sessions partagées entre processus Forge. Persiste les sessions après
    redémarrage. Ne devient pas le backend par défaut.

    Les read-modify-write (`set`, `replace`, `touch_expiry`, `set_flash`,
    `get_flash`, `regenerate`, `authenticate`) sont atomiques par concurrence
    optimiste (garde de `version` + retry), sans verrou SGBD propriétaire.

    Les callables fetch_one et execute sont injectables pour les tests.
    """

    def __init__(
        self,
        fetch_one: _FetchOne | None = None,
        execute: _Execute | None = None,
        ttl: int = DEFAULT_SESSION_TTL,
        fetch_all: "_FetchAll | None" = None,
    ) -> None:
        self._fetch_one = fetch_one or _default_fetch_one
        self._execute = execute or _default_execute
        # Ajouté en dernier, et nommé : les appels existants passent leurs
        # accesseurs par position (ADMIN-SESSIONS-VIEW-001).
        self._fetch_all = fetch_all or _default_fetch_all
        self._ttl = ttl

    # ── helpers ─────────────────────────────────────────────────────────────

    def _valid(self, session_id: str) -> bool:
        return bool(_SESSION_ID_RE.fullmatch(session_id))

    def _load(self, session_id: str) -> tuple[dict[str, Any], int] | None:
        """Charge une session non expirée : `(data, version)`.

        Retourne None si absente, expirée ou corrompue. Une donnée corrompue
        (JSON invalide ou non-dict) est purgée.
        """
        row = self._fetch_one(_SQL_SELECT, (session_id, _now_str()))
        if not row:
            return None
        try:
            data = json.loads(row["data"])
        except (json.JSONDecodeError, TypeError, ValueError, KeyError):
            self._execute(_SQL_DELETE, (session_id,))
            return None
        if not isinstance(data, dict):
            return None
        return cast("dict[str, Any]", data), int(row["version"])

    @staticmethod
    def _conflict_error(operation: str) -> RuntimeError:
        return RuntimeError(
            f"forge_sessions : conflit de version persistant sur {operation}"
            f" après {_MAX_WRITE_RETRIES} tentatives (contention anormale)."
        )

    # ── API publique ─────────────────────────────────────────────────────────

    def create(
        self, data: dict[str, Any] | None = None, *, kind: str = KIND_ANONYMOUS
    ) -> str:
        """Crée une session et retourne son identifiant.

        `kind` décide de la durée de vie (`SESSIONS-TTL-PER-KIND-001`). Une
        session créée sans être authentifiée est anonyme, et n'a pas à vivre
        aussi longtemps qu'une session d'utilisateur connecté.

        Le `ttl` passé au constructeur reste prioritaire quand il diffère du
        défaut historique : un projet qui l'avait réglé à la main garde son
        réglage, le retirer sous ses pieds serait une rupture silencieuse.
        """
        nature = normalize_kind(kind)
        session_id = secrets.token_hex(32)
        duree = self._ttl if self._ttl != DEFAULT_SESSION_TTL else ttl_for(nature)
        expires_at = time.time() + duree
        session = {
            **(data or {}),
            "authenticated": False,
            "user": None,
            "csrf_token": secrets.token_hex(16),
            "expires_at": expires_at,
        }
        now = _now_str()
        self._execute(
            _SQL_INSERT,
            (
                session_id, json.dumps(session), _user_id_of(session), nature,
                _dt(expires_at), now, now,
            ),
        )
        return session_id

    def get(self, session_id: str) -> dict[str, Any] | None:
        """Retourne les données de session ou None si absente, expirée ou corrompue."""
        if not self._valid(session_id):
            return None
        loaded = self._load(session_id)
        return loaded[0] if loaded is not None else None

    def set(self, session_id: str, data: dict[str, Any]) -> None:
        """Met à jour (merge) les données d'une session existante non expirée."""
        if not self._valid(session_id):
            return
        for _ in range(_MAX_WRITE_RETRIES):
            loaded = self._load(session_id)
            if loaded is None:
                return
            existing, version = loaded
            existing.update(data)
            rc = self._execute(
                _SQL_UPDATE,
                (json.dumps(existing), _user_id_of(existing), _now_str(), session_id, version),
            )
            if rc >= 1:
                return
        raise self._conflict_error("set")

    def replace(self, session_id: str, data: dict[str, Any]) -> None:
        """Remplace intégralement les données d'une session existante (sans merge).

        Contrairement à set(), les clés absentes de data sont supprimées.
        """
        if not self._valid(session_id):
            return
        for _ in range(_MAX_WRITE_RETRIES):
            loaded = self._load(session_id)
            if loaded is None:
                return
            _, version = loaded
            rc = self._execute(
                _SQL_UPDATE,
                (json.dumps(data), _user_id_of(data), _now_str(), session_id, version),
            )
            if rc >= 1:
                return
        raise self._conflict_error("replace")

    def delete(self, session_id: str) -> None:
        """Supprime la session."""
        if not self._valid(session_id):
            return
        self._execute(_SQL_DELETE, (session_id,))

    def list_for_user(
        self, user_id: object, *, current_session_id: "str | None" = None
    ) -> "list[SessionSummary]":
        """Résumés des sessions **non expirées** de `user_id`, la plus récente d'abord.

        Le filtre d'expiration est en SQL, pas en Python : une session expirée
        que la purge n'a pas encore retirée n'a pas à s'afficher comme active.

        Aucun identifiant n'est rendu : voir `SessionSummary`. L'identifiant
        sert ici à calculer le préfixe et à repérer la session courante, il ne
        sort pas de la méthode.
        """
        if user_id is None:
            return []
        lignes = self._fetch_all(_SQL_LIST_FOR_USER, (str(user_id), _now_str()))
        return [
            SessionSummary(
                handle=str(ligne["session_id"])[:HANDLE_LENGTH],
                created_at=_horodatage(ligne.get("created_at")),
                expires_at=_horodatage(ligne.get("expire_at")),
                is_current=str(ligne["session_id"]) == current_session_id,
            )
            for ligne in lignes
        ]

    def delete_for_user(
        self, user_id: object, *, except_session_id: "str | None" = None
    ) -> int:
        """Supprime les sessions de `user_id`. Retourne le nombre supprimé.

        Une seule requête, sur la colonne indexée `user_id` : contrairement aux
        stores mémoire et fichier, ce store est partagé entre processus et sa
        table peut être grande, si bien qu'un balayage se dégraderait avec le
        trafic.

        L'identité est comparée en texte, comme elle est écrite.
        """
        if user_id is None:
            return 0
        if except_session_id is None:
            return self._execute(_SQL_DELETE_FOR_USER, (str(user_id),))
        return self._execute(
            _SQL_DELETE_FOR_USER_EXCEPT, (str(user_id), except_session_id)
        )

    def regenerate(self, session_id: str) -> str:
        """Crée un nouveau session_id en préservant les données — protège contre la fixation."""
        for _ in range(_MAX_WRITE_RETRIES):
            existing: dict[str, Any] = {}
            version: int | None = None
            if self._valid(session_id):
                loaded = self._load(session_id)
                if loaded is not None:
                    existing, version = loaded
            if version is not None:
                rc = self._execute(_SQL_DELETE_VERSIONED, (session_id, version))
                if rc == 0:
                    continue  # un autre writer a modifié la session : on recharge
            nouveau_id = secrets.token_hex(32)
            expires_at = time.time() + self._ttl
            existing["expires_at"] = expires_at
            now = _now_str()
            self._execute(
                _SQL_INSERT,
                (
                    nouveau_id, json.dumps(existing), _user_id_of(existing),
                    KIND_ANONYMOUS, _dt(expires_at), now, now,
                ),
            )
            return nouveau_id
        raise self._conflict_error("regenerate")

    def authenticate(self, session_id: str, user_data: dict[str, Any], ttl_seconds: int) -> str | None:
        """Rotation atomique : invalide l'ancienne session, crée une nouvelle authentifiée."""
        if not self._valid(session_id):
            return None
        for _ in range(_MAX_WRITE_RETRIES):
            loaded = self._load(session_id)
            if loaded is None:
                return None
            existing, version = loaded
            rc = self._execute(_SQL_DELETE_VERSIONED, (session_id, version))
            if rc == 0:
                continue  # conflit : la session a changé, on recharge
            nouveau_id = secrets.token_hex(32)
            expires_at = time.time() + ttl_seconds
            new_session = {
                **existing,
                "authenticated": True,
                "user": user_data,
                "csrf_token": secrets.token_hex(16),
                "expires_at": expires_at,
            }
            now = _now_str()
            self._execute(
                _SQL_INSERT,
                (
                    nouveau_id, json.dumps(new_session), _user_id_of(new_session),
                    KIND_AUTHENTICATED, _dt(expires_at), now, now,
                ),
            )
            return nouveau_id
        raise self._conflict_error("authenticate")

    def touch_expiry(self, session_id: str, ttl_seconds: int) -> bool:
        """Repousse l'expiration. Retourne False si la session n'existe pas ou est expirée."""
        if not self._valid(session_id):
            return False
        for _ in range(_MAX_WRITE_RETRIES):
            loaded = self._load(session_id)
            if loaded is None:
                return False
            data, version = loaded
            expires_at = time.time() + ttl_seconds
            data["expires_at"] = expires_at
            rc = self._execute(
                _SQL_UPDATE_EXPIRY,
                (json.dumps(data), _user_id_of(data), _dt(expires_at), _now_str(), session_id, version),
            )
            if rc >= 1:
                return True
        raise self._conflict_error("touch_expiry")

    def set_flash(self, session_id: str, message: str, level: str = "success") -> bool:
        """Stocke un message flash. Retourne False si la session n'existe pas."""
        if not self._valid(session_id):
            return False
        for _ in range(_MAX_WRITE_RETRIES):
            loaded = self._load(session_id)
            if loaded is None:
                return False
            data, version = loaded
            data["flash"] = {"message": message, "level": level}
            rc = self._execute(
                _SQL_UPDATE,
                (json.dumps(data), _user_id_of(data), _now_str(), session_id, version),
            )
            if rc >= 1:
                return True
        raise self._conflict_error("set_flash")

    def get_flash(self, session_id: str) -> dict[str, Any] | None:
        """Lit et supprime le message flash. Retourne None si absent.

        Atomique par concurrence optimiste : deux lectures concurrentes ne
        peuvent pas obtenir le même flash. Le writer qui perd la garde de
        version recharge ; le flash étant déjà consommé, il obtient None. Le
        message est donc rendu **exactement une fois**.
        """
        if not self._valid(session_id):
            return None
        for _ in range(_MAX_WRITE_RETRIES):
            loaded = self._load(session_id)
            if loaded is None:
                return None
            data, version = loaded
            flash = data.get("flash")
            if flash is None:
                return None
            remaining = {key: value for key, value in data.items() if key != "flash"}
            rc = self._execute(
                _SQL_UPDATE,
                (json.dumps(remaining), _user_id_of(remaining), _now_str(), session_id, version),
            )
            if rc >= 1:
                return cast("dict[str, Any]", flash)
            # rc == 0 : lecture concurrente gagnante, on recharge (flash déjà parti).
        return None

    def cleanup_expired(self) -> int:
        """Supprime les sessions expirées. Retourne le nombre de lignes supprimées."""
        return self._execute(_SQL_CLEANUP, (_now_str(),)) or 0
