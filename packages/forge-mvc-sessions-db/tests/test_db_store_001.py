"""Tests comportementaux de DbSessionStore (ex-MariaDbSessionStore, ADR-054).

Aucune base réelle : _FakeDB simule fetch_one / execute en mémoire via les
callables injectables du store. Le SQL est portable (horodatages passés en
paramètres, garde de version), donc _FakeDB interprète les paramètres, pas des
fonctions SQL. Le schéma modélise la colonne `version` (concurrence optimiste,
retour terrain 016 F36).
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

pytestmark = pytest.mark.smoke

pytest.importorskip("forge_mvc_sessions_db")

from forge_mvc_sessions_db import DbSessionStore  # noqa: E402
from forge_mvc_sessions_db import store as store_mod  # noqa: E402

_FMT = "%Y-%m-%d %H:%M:%S"


def _ts(dt_str: str) -> float:
    return datetime.strptime(dt_str, _FMT).replace(tzinfo=timezone.utc).timestamp()


def _params_par_colonne(sql: str, params: tuple) -> dict:
    """Associe les paramètres d'un INSERT aux colonnes que le SQL déclare.

    Les colonnes littérales (`version` posée à `0`) ne consomment pas de
    marqueur : le rapprochement suit les `?`, dans l'ordre.
    """
    debut = sql.index("(") + 1
    colonnes = [c.strip() for c in sql[debut: sql.index(")", debut)].split(",")]
    valeurs_sql = sql[sql.upper().index("VALUES"):]
    debut_v = valeurs_sql.index("(") + 1
    jetons = [j.strip() for j in valeurs_sql[debut_v: valeurs_sql.index(")", debut_v)].split(",")]

    associe: dict = {}
    index = 0
    for colonne, jeton in zip(colonnes, jetons):
        if jeton == "?":
            associe[colonne] = params[index]
            index += 1
        else:
            associe[colonne] = jeton
    return associe


class _FakeDB:
    """Simule fetch_one / execute pour DbSessionStore, sans base réelle.

    Modélise la garde de version : une écriture ne s'applique que si la version
    attendue (dernier paramètre) correspond, et incrémente alors la version.
    """

    def __init__(self):
        # {session_id: {"data": json_str, "user_id": str|None,
        #               "expire_ts": float, "version": int}}
        # `user_id` suit la colonne indexée ajoutée par
        # SESSIONS-DELETE-FOR-USER-001 : le double reste fidèle au schéma réel.
        self.rows: dict[str, dict] = {}

    def fetch_one(self, sql: str, params: tuple) -> dict | None:
        sid = params[0] if params else None
        row = self.rows.get(sid)
        if row is None:
            return None
        # SELECT ... WHERE expire_at > ? : params[1] porte le "maintenant".
        if "expire_at > ?" in sql and row["expire_ts"] <= _ts(params[1]):
            return None
        return {"data": row["data"], "version": row["version"]}

    def execute(self, sql: str, params: tuple = ()) -> int:
        s = sql.strip()
        if s.startswith("INSERT"):
            # Les positions sont lues DANS le SQL, pas écrites à la main.
            # Elles l'étaient, et l'ajout de la colonne `kind`
            # (SESSIONS-TTL-PER-KIND-001) a fait lire une nature de session là
            # où le double attendait une date. Un vrai pilote lit l'ordre de la
            # requête ; le double le fait maintenant aussi, et une prochaine
            # colonne ne le cassera plus.
            valeurs = _params_par_colonne(sql, params)
            sid = valeurs["session_id"]
            self.rows[sid] = {
                "data": valeurs["data"],
                "user_id": valeurs["user_id"],
                "kind": valeurs.get("kind"),
                "expire_ts": _ts(valeurs["expire_at"]),
                "version": 0,
            }
            return 1
        if s.startswith("UPDATE"):
            if "expire_at = ?" in sql:  # data, user_id, expire, updated, sid, version
                data_json, user_id, expire_dt = params[0], params[1], params[2]
                sid, exp_ver = params[4], params[5]
                row = self.rows.get(sid)
                if row is not None and row["version"] == exp_ver:
                    row["data"] = data_json
                    row["user_id"] = user_id
                    row["expire_ts"] = _ts(expire_dt)
                    row["version"] += 1
                    return 1
                return 0
            # data, user_id, updated, sid, version
            data_json, user_id, sid, exp_ver = params[0], params[1], params[3], params[4]
            row = self.rows.get(sid)
            if row is not None and row["version"] == exp_ver:
                row["data"] = data_json
                row["user_id"] = user_id
                row["version"] += 1
                return 1
            return 0
        if s.startswith("DELETE") and "expire_at < ?" in sql:  # cleanup : params[0] = now
            now_ts = _ts(params[0])
            expired = [k for k, v in self.rows.items() if v["expire_ts"] <= now_ts]
            for k in expired:
                del self.rows[k]
            return len(expired)
        if s.startswith("DELETE") and "WHERE user_id" in sql:
            # `session_id <> ?` épargne la session courante (MFA-SESSION-INVALIDATION-001).
            epargnee = params[1] if "session_id <> ?" in sql else None
            vises = [
                k for k, v in self.rows.items()
                if v.get("user_id") == params[0] and k != epargnee
            ]
            for k in vises:
                del self.rows[k]
            return len(vises)
        if s.startswith("DELETE") and "WHERE session_id" in sql:
            sid = params[0]
            if "version = ?" in sql:  # DELETE gardé par version
                exp_ver = params[1]
                row = self.rows.get(sid)
                if row is not None and row["version"] == exp_ver:
                    del self.rows[sid]
                    return 1
                return 0
            return 1 if self.rows.pop(sid, None) is not None else 0
        return 0


def _make_store(ttl: int = 3600):
    db = _FakeDB()
    return DbSessionStore(fetch_one=db.fetch_one, execute=db.execute, ttl=ttl), db


# ── Importabilité / contrat ───────────────────────────────────────────────────

def test_store_implements_protocol():
    from core.sessions import SessionStore
    store, _ = _make_store()
    assert isinstance(store, SessionStore)


def test_store_sql_has_no_proprietary_date_fn():
    for sql in (
        store_mod._SQL_INSERT, store_mod._SQL_SELECT, store_mod._SQL_UPDATE,
        store_mod._SQL_UPDATE_EXPIRY, store_mod._SQL_DELETE,
        store_mod._SQL_DELETE_VERSIONED, store_mod._SQL_CLEANUP,
    ):
        assert "NOW()" not in sql and "GETDATE()" not in sql and "datetime('now')" not in sql


# ── Création ──────────────────────────────────────────────────────────────────

def test_create_returns_64_hex():
    store, _ = _make_store()
    sid = store.create()
    assert isinstance(sid, str) and len(sid) == 64
    assert all(c in "0123456789abcdef" for c in sid)


def test_create_inserts_row():
    store, db = _make_store()
    assert store.create() in db.rows


def test_create_standard_structure():
    store, _ = _make_store()
    data = store.get(store.create())
    assert data is not None
    assert data["authenticated"] is False
    assert data["user"] is None
    assert "csrf_token" in data and "expires_at" in data


# ── Lecture ───────────────────────────────────────────────────────────────────

def test_get_returns_data():
    store, _ = _make_store()
    assert store.get(store.create()) is not None


def test_get_unknown_returns_none():
    store, _ = _make_store()
    assert store.get("a" * 64) is None


def test_get_invalid_id_returns_none():
    store, _ = _make_store()
    assert store.get("invalid") is None and store.get("") is None


def test_get_invalid_no_sql_call():
    calls = []
    store = DbSessionStore(
        fetch_one=lambda s, p: calls.append(s),
        execute=lambda s, p=(): calls.append(s) or 0,
    )
    store.get("../bad/../id")
    store.get("")
    store.get("G" * 64)
    assert calls == []


# ── Modification ──────────────────────────────────────────────────────────────

def test_set_updates_data():
    store, _ = _make_store()
    sid = store.create()
    store.set(sid, {"custom_key": "custom_value"})
    data = store.get(sid)
    assert data is not None and data["custom_key"] == "custom_value"
    assert data["authenticated"] is False


def test_set_unknown_is_noop():
    store, db = _make_store()
    store.set("a" * 64, {"x": 1})
    assert "a" * 64 not in db.rows


def test_set_bumps_version():
    store, db = _make_store()
    sid = store.create()
    assert db.rows[sid]["version"] == 0
    store.set(sid, {"x": 1})
    assert db.rows[sid]["version"] == 1


def test_replace_drops_absent_keys():
    store, _ = _make_store()
    sid = store.create()
    store.set(sid, {"a": 1, "b": 2})
    store.replace(sid, {"a": 9})
    data = store.get(sid)
    assert data is not None and data == {"a": 9}


def test_touch_expiry_repousse():
    store, db = _make_store(ttl=1)
    sid = store.create()
    assert store.touch_expiry(sid, 3600) is True
    assert db.rows[sid]["expire_ts"] > time.time() + 3000


# ── Flash ─────────────────────────────────────────────────────────────────────

def test_flash_set_then_get_once():
    store, _ = _make_store()
    sid = store.create()
    assert store.set_flash(sid, "coucou", "info") is True
    first = store.get_flash(sid)
    assert first == {"message": "coucou", "level": "info"}
    # Deuxième lecture : le flash a été consommé.
    assert store.get_flash(sid) is None


# ── Concurrence optimiste (F36) ───────────────────────────────────────────────

def test_set_retries_on_version_conflict_without_lost_update():
    store, db = _make_store()
    sid = store.create()
    real_execute = db.execute
    state = {"raced": False}

    def racing_execute(sql: str, params: tuple = ()) -> int:
        # Au 1er UPDATE de `set`, on simule un writer concurrent qui pose une
        # clé ET incrémente la version, périmant la garde de `set` (rc == 0).
        if sql.strip().startswith("UPDATE") and not state["raced"]:
            state["raced"] = True
            row = db.rows[sid]
            merged = json.loads(row["data"])
            merged["concurrent"] = 1
            row["data"] = json.dumps(merged)
            row["version"] += 1
            return 0
        return real_execute(sql, params)

    store._execute = racing_execute
    store.set(sid, {"mine": 2})
    data = store.get(sid)
    assert data is not None
    assert data["concurrent"] == 1  # l'écriture concurrente n'est pas perdue
    assert data["mine"] == 2        # la nôtre est appliquée par-dessus (retry)


def test_get_flash_returned_once_under_race():
    store, db = _make_store()
    sid = store.create()
    store.set_flash(sid, "unique", "warning")
    # Simule deux lectures concurrentes : la première consomme, la seconde perd
    # la garde de version puis recharge (flash déjà parti).
    winners = []

    def racing_execute(sql: str, params: tuple = ()) -> int:
        if sql.strip().startswith("UPDATE") and not winners:
            winners.append(True)
            # Une lecture concurrente consomme le flash avant nous.
            row = db.rows[sid]
            data = json.loads(row["data"])
            data.pop("flash", None)
            row["data"] = json.dumps(data)
            row["version"] += 1
            return 0
        return _FakeDB.execute(db, sql, params)

    store._execute = racing_execute
    assert store.get_flash(sid) is None  # le concurrent l'a eu ; nous, rien


# ── Suppression ───────────────────────────────────────────────────────────────

def test_delete_removes_session():
    store, db = _make_store()
    sid = store.create()
    store.delete(sid)
    assert store.get(sid) is None and sid not in db.rows


def test_delete_unknown_is_noop():
    store, _ = _make_store()
    store.delete("a" * 64)


# ── Régénération / authentification ───────────────────────────────────────────

def test_regenerate_returns_new_id_and_preserves_data():
    store, _ = _make_store()
    sid = store.create()
    store.set(sid, {"user_key": "user_val"})
    nouveau = store.regenerate(sid)
    assert nouveau != sid and len(nouveau) == 64
    data = store.get(nouveau)
    assert data is not None and data["user_key"] == "user_val"
    assert store.get(sid) is None


def test_authenticate_rotates_and_marks():
    store, _ = _make_store()
    sid = store.create()
    nouveau = store.authenticate(sid, {"id": 7}, 3600)
    assert nouveau is not None and nouveau != sid
    data = store.get(nouveau)
    assert data is not None and data["authenticated"] is True and data["user"] == {"id": 7}
    assert store.get(sid) is None


# ── Expiration / nettoyage ────────────────────────────────────────────────────

def test_expired_returns_none():
    store, _ = _make_store(ttl=0)
    sid = store.create()
    time.sleep(1.01)
    assert store.get(sid) is None


def test_cleanup_removes_expired_keeps_valid():
    store_short, db = _make_store(ttl=0)
    store_long, _ = _make_store(ttl=3600)
    store_long._execute = db.execute
    store_long._fetch_one = db.fetch_one
    store_short.create()
    sid_valid = store_long.create()
    time.sleep(1.01)
    assert store_short.cleanup_expired() == 1
    assert sid_valid in db.rows


def test_cleanup_empty_returns_zero():
    store, _ = _make_store()
    assert store.cleanup_expired() == 0


# ── Horodatage UTC + TTL découplé (F37) ───────────────────────────────────────

def test_timestamps_are_utc_based():
    now_str = store_mod._now_str()
    parsed = datetime.strptime(now_str, _FMT).replace(tzinfo=timezone.utc)
    delta = abs((datetime.now(timezone.utc) - parsed).total_seconds())
    assert delta < 5


def test_default_ttl_is_local_constant_not_memory_store():
    assert store_mod.__file__ is not None
    source = Path(store_mod.__file__).read_text(encoding="utf-8")
    assert "core.sessions.memory_store" not in source
    assert store_mod.DEFAULT_SESSION_TTL == 3600


# ── JSON corrompu ─────────────────────────────────────────────────────────────

def test_corrupted_json_returns_none_and_deletes():
    deleted = []

    def fake_run(sql, params=()):
        if "WHERE session_id" in sql:
            deleted.append(params[0] if params else None)
        return 0

    store = DbSessionStore(
        fetch_one=lambda s, p: {"data": "invalid json{{{"},
        execute=fake_run,
        ttl=3600,
    )
    assert store.get("a" * 64) is None
    assert len(deleted) == 1


def test_wrong_type_returns_none():
    store, db = _make_store()
    sid = store.create()
    db.rows[sid]["data"] = '["liste", "pas", "dict"]'
    assert store.get(sid) is None


# ── Sérialiseurs interdits ────────────────────────────────────────────────────

_BANNED_WORDS = ["pic" + "kle", "mar" + "shal", "ev" + "al(", "ex" + "ec("]


def test_banned_serializers_absent_from_store():
    assert store_mod.__file__ is not None
    source = Path(store_mod.__file__).read_text(encoding="utf-8")
    for word in _BANNED_WORDS:
        assert word not in source, f"mot interdit dans store.py : {word}"
