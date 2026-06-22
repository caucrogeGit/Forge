"""Tests — PIVOT-ADVANCED-003 : PivotAdvancedService.

Aucune connexion MariaDB réelle n'est requise : _FakePivotDB simule les
opérations SQL en mémoire via les callables injectables du service.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_pivot")
from forge_mvc_pivot import PivotAdvancedService, PivotRow


# ── Fausse base de données ────────────────────────────────────────────────────


class _FakePivotDB:
    """Simule fetch_one / fetch_all / execute / insert pour PivotAdvancedService."""

    def __init__(self):
        self.rows: list[dict] = []
        self.last_sql: str = ""
        self.last_params: tuple = ()
        self.last_insert_id: int = 0

    def _record(self, sql: str, params: tuple) -> None:
        self.last_sql = sql
        self.last_params = params

    def fetch_one(self, sql: str, params: tuple) -> dict | None:
        self._record(sql, params)
        for row in self.rows:
            if all(row.get(k) == v for k, v in zip(self._extract_where_keys(sql), params)):
                return dict(row)
        return None

    def fetch_all(self, sql: str, params: tuple) -> list[dict]:
        self._record(sql, params)
        source_val = params[0] if params else None
        keys = self._extract_where_keys(sql)
        if not keys:
            return [dict(r) for r in self.rows]
        return [dict(r) for r in self.rows if r.get(keys[0]) == source_val]

    def execute(self, sql: str, params: tuple) -> int:
        self._record(sql, params)
        sql_s = sql.strip().upper()
        if sql_s.startswith("UPDATE"):
            src_val, tgt_val = params[-2], params[-1]
            set_keys = self._extract_set_keys(sql)
            for r in self.rows:
                vals = list(r.values())
                if src_val in vals and tgt_val in vals:
                    for i, k in enumerate(set_keys):
                        if k in r:
                            r[k] = params[i]
                    return 1
            return 0
        if sql_s.startswith("DELETE"):
            src_val, tgt_val = params[0], params[1]
            before = len(self.rows)
            self.rows = [
                r for r in self.rows
                if not (src_val in r.values() and tgt_val in r.values())
            ]
            return before - len(self.rows)
        return 0

    def insert(self, sql: str, params: tuple) -> int:
        self._record(sql, params)
        cols = self._extract_insert_cols(sql)
        row = dict(zip(cols, params))
        self.rows.append(row)
        self.last_insert_id += 1
        return self.last_insert_id

    @staticmethod
    def _extract_where_keys(sql: str) -> list[str]:
        import re
        return re.findall(r"(\w+)\s*=\s*\?", sql.split("WHERE")[-1]) if "WHERE" in sql else []

    @staticmethod
    def _extract_set_keys(sql: str) -> list[str]:
        import re
        if "SET" not in sql:
            return []
        set_part = sql.split("SET")[1].split("WHERE")[0]
        return re.findall(r"(\w+)\s*=\s*\?", set_part)

    @staticmethod
    def _extract_insert_cols(sql: str) -> list[str]:
        import re
        m = re.search(r"\(([^)]+)\)\s*VALUES", sql)
        if not m:
            return []
        return [c.strip() for c in m.group(1).split(",")]


def _make_service(db: _FakePivotDB | None = None, pivot_fields=None):
    db = db or _FakePivotDB()
    svc = PivotAdvancedService(
        table="article_tag",
        source_key="article_id",
        target_key="tag_id",
        pivot_fields=pivot_fields if pivot_fields is not None else ["position", "note"],
        fetch_one=db.fetch_one,
        fetch_all=db.fetch_all,
        execute=db.execute,
        insert_fn=db.insert,
    )
    return svc, db


# ── Import ────────────────────────────────────────────────────────────────────


def test_import_pivot_advanced_service():
    from forge_mvc_pivot import PivotAdvancedService
    assert PivotAdvancedService is not None


def test_import_pivot_row():
    from forge_mvc_pivot import PivotRow
    assert PivotRow is not None


# ── Constructeur ──────────────────────────────────────────────────────────────


def test_constructeur_accepte_params_valides():
    svc, _ = _make_service()
    assert svc._table == "article_tag"
    assert svc._source_key == "article_id"
    assert svc._target_key == "tag_id"
    assert svc._pivot_fields == ("position", "note")


def test_constructeur_refuse_nom_table_dangereux():
    with pytest.raises(ValueError, match="table invalide"):
        PivotAdvancedService(
            table="article_tag; DROP TABLE articles--",
            source_key="article_id",
            target_key="tag_id",
        )


def test_constructeur_refuse_nom_colonne_dangereux():
    with pytest.raises(ValueError, match="source_key invalide"):
        PivotAdvancedService(
            table="article_tag",
            source_key="article_id; DROP TABLE",
            target_key="tag_id",
        )


def test_constructeur_refuse_nom_pivot_field_dangereux():
    with pytest.raises(ValueError, match="pivot_fields"):
        PivotAdvancedService(
            table="article_tag",
            source_key="article_id",
            target_key="tag_id",
            pivot_fields=["position", "bad field!"],
        )


def test_constructeur_pivot_fields_optionnel():
    svc, _ = _make_service(pivot_fields=[])
    assert svc._pivot_fields == ()


# ── attach ────────────────────────────────────────────────────────────────────


def test_attach_genere_insertion_parametree():
    svc, db = _make_service()
    svc.attach(12, 3, {"position": 1, "note": "Principal"})
    assert "INSERT INTO article_tag" in db.last_sql
    assert "?" in db.last_sql
    assert 12 in db.last_params
    assert 3 in db.last_params
    assert 1 in db.last_params


def test_attach_refuse_champ_pivot_inconnu():
    svc, _ = _make_service()
    with pytest.raises(ValueError, match="inconnus"):
        svc.attach(12, 3, {"position": 1, "inconnu": "x"})


def test_attach_sans_pivot_data_accepte():
    svc, db = _make_service(pivot_fields=[])
    svc.attach(12, 3)
    assert db.last_sql.startswith("INSERT INTO article_tag")


def test_attach_retourne_lastrowid():
    svc, db = _make_service()
    rid = svc.attach(12, 3, {"position": 1, "note": "test"})
    assert rid == 1


# ── list_for_source ───────────────────────────────────────────────────────────


def test_list_for_source_utilise_source_key():
    svc, db = _make_service()
    db.rows = [
        {"article_id": 12, "tag_id": 3, "position": 1, "note": "Principal"},
        {"article_id": 12, "tag_id": 5, "position": 2, "note": "Secondaire"},
        {"article_id": 99, "tag_id": 3, "position": 1, "note": "Autre"},
    ]
    result = svc.list_for_source(12)
    assert "article_id" in db.last_sql
    assert db.last_params == (12,)
    assert len(result) == 2


def test_list_for_source_retourne_pivot_rows():
    svc, db = _make_service()
    db.rows = [{"article_id": 12, "tag_id": 3, "position": 1, "note": "test"}]
    result = svc.list_for_source(12)
    assert len(result) == 1
    assert isinstance(result[0], PivotRow)
    assert result[0].source_id == 12
    assert result[0].target_id == 3
    assert result[0].pivot_data["position"] == 1


def test_list_for_source_retourne_liste_vide_si_aucune():
    svc, db = _make_service()
    db.rows = []
    result = svc.list_for_source(99)
    assert result == []


# ── get ───────────────────────────────────────────────────────────────────────


def test_get_utilise_source_key_et_target_key():
    svc, db = _make_service()
    db.rows = [{"article_id": 12, "tag_id": 3, "position": 1, "note": "test"}]
    svc.get(12, 3)
    assert "article_id" in db.last_sql
    assert "tag_id" in db.last_sql
    assert db.last_params == (12, 3)


def test_get_retourne_pivot_row_si_trouve():
    svc, db = _make_service()
    db.rows = [{"article_id": 12, "tag_id": 3, "position": 1, "note": "test"}]
    result = svc.get(12, 3)
    assert result is not None
    assert isinstance(result, PivotRow)


def test_get_retourne_none_si_absent():
    svc, db = _make_service()
    db.rows = []
    result = svc.get(12, 99)
    assert result is None


# ── update ────────────────────────────────────────────────────────────────────


def test_update_utilise_source_key_et_target_key():
    svc, db = _make_service()
    db.rows = [{"article_id": 12, "tag_id": 3, "position": 1, "note": "avant"}]
    svc.update(12, 3, {"note": "après"})
    assert "UPDATE article_tag" in db.last_sql
    assert "article_id" in db.last_sql
    assert "tag_id" in db.last_sql
    assert 12 in db.last_params
    assert 3 in db.last_params


def test_update_ne_modifie_que_champs_pivot():
    svc, db = _make_service()
    db.rows = [{"article_id": 12, "tag_id": 3, "position": 1, "note": "avant"}]
    svc.update(12, 3, {"note": "après"})
    assert "article_id = ?" not in db.last_sql.split("WHERE")[0]
    assert "tag_id = ?" not in db.last_sql.split("WHERE")[0]


def test_update_refuse_champ_inconnu():
    svc, _ = _make_service()
    with pytest.raises(ValueError, match="inconnus"):
        svc.update(12, 3, {"position": 1, "champ_inexistant": "x"})


def test_update_pivot_data_vide_retourne_zero():
    svc, db = _make_service()
    result = svc.update(12, 3, {})
    assert result == 0
    assert db.last_sql == ""


# ── detach ────────────────────────────────────────────────────────────────────


def test_detach_utilise_source_key_et_target_key():
    svc, db = _make_service()
    db.rows = [{"article_id": 12, "tag_id": 3, "position": 1, "note": "test"}]
    svc.detach(12, 3)
    assert "DELETE FROM article_tag" in db.last_sql
    assert "article_id" in db.last_sql
    assert "tag_id" in db.last_sql
    assert db.last_params == (12, 3)


def test_detach_supprime_association():
    svc, db = _make_service()
    db.rows = [{"article_id": 12, "tag_id": 3, "position": 1, "note": "test"}]
    result = svc.detach(12, 3)
    assert result >= 0


# ── Neutralité make:crud ──────────────────────────────────────────────────────


def test_service_ne_depend_pas_de_make_crud():
    import forge_mvc_pivot as mod
    src = mod.__file__
    text = open(src).read()
    assert "make_crud" not in text
    assert "import make_crud" not in text
    assert "CrudManyToManyRelation" not in text
    assert "from cli" not in text


# ── Généricité ────────────────────────────────────────────────────────────────


def test_service_generique_pas_specifique_article_tag():
    svc = PivotAdvancedService(
        table="project_user",
        source_key="project_id",
        target_key="user_id",
        pivot_fields=["role", "joined_at"],
    )
    assert svc._table == "project_user"
    assert svc._source_key == "project_id"
    assert svc._pivot_fields == ("role", "joined_at")
