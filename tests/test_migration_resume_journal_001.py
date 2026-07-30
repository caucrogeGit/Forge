"""MIGRATION-RESUME-JOURNAL-001 : une migration interrompue reprend, sans rejouer.

`MIGRATION-DDL-NON-TRANSACTIONAL-REVEAL-001` (cycle 3) avait dit la vérité :
sur MariaDB, une migration qui casse à l'instruction 3 laisse les deux
premières en base, hors journal, et la relance bute sur « already exists ».
Révélé, mais sans outil : l'opérateur devait défaire à la main. C'était le
dernier scénario connu où un projet Forge restait bloqué sans commande.

La cause est que Forge ne retenait pas où il s'était arrêté. Sur un backend qui
ne sait pas annuler la DDL, chaque instruction est désormais journalisée dans
`forge_migration_steps` et validée sitôt exécutée : le journal dit exactement
ce qui a pris effet. `migration:apply` reprend à la première instruction non
journalisée, bruyamment, après avoir vérifié que le préfixe déjà en base
correspond toujours au fichier : les instructions appliquées ne peuvent pas
être réécrites depuis le fichier, la base les a exécutées telles quelles.

Sur un backend transactionnel, rien ne change : l'annulation défait tout, la
migration reste atomique et aucun journal n'est tenu.

Fakes : la mécanique se prouve sans serveur. Le pendant sur serveur réel est
`tests/db/test_migration_resume_real_server_001.py`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("forge_mvc_entities")
from forge_mvc_entities import migrations as M  # noqa: E402


class _Cursor:
    def __init__(self, connection: "_Connexion") -> None:
        self._connection = connection

    def execute(self, sql: str, params: "tuple[Any, ...]" = ()) -> None:
        self._connection.executed.append((sql, params))
        premier_mot = sql.split(None, 1)[0].upper() if sql.split() else ""
        if premier_mot in {"CREATE", "ALTER", "DROP"}:
            # Le comportement MariaDB : la DDL valide implicitement.
            self._connection.commits.append("implicite")
        if self._connection.fautive is not None and self._connection.fautive in sql:
            raise RuntimeError(f"SQL fautif : {sql[:40]}")

    def fetchall(self) -> "list[tuple[Any, ...]]":
        return list(self._connection.step_rows)

    def close(self) -> None:
        return None


class _Connexion:
    """Connexion factice : enregistre tout, peut échouer sur un motif."""

    def __init__(self, fautive: "str | None" = None,
                 step_rows: "list[tuple[Any, ...]] | None" = None) -> None:
        self.executed: "list[tuple[str, tuple[Any, ...]]]" = []
        self.commits: "list[str]" = []
        self.rollbacks = 0
        self.fautive = fautive
        self.step_rows = step_rows or []

    def cursor(self) -> _Cursor:
        return _Cursor(self)

    def commit(self) -> None:
        self.commits.append("explicite")

    def rollback(self) -> None:
        self.rollbacks += 1


def _migration(tmp_path: Path, sql: str) -> M.MigrationFile:
    path = tmp_path / "20260730120000_probe.sql"
    path.write_text(sql, encoding="utf-8")
    return M.MigrationFile(
        version="20260730120000", name="probe",
        filename=path.name, checksum=M.migration_checksum(path), path=path,
    )


_SQL = (
    "CREATE TABLE a (id INT);\n"
    "CREATE TABLE b (id INT);\n"
    "CREATE TABLE c (id INT);\n"
)


def _sql_journalises(connexion: _Connexion) -> "list[tuple[str, tuple[Any, ...]]]":
    return [(s, p) for s, p in connexion.executed
            if s.startswith("INSERT INTO forge_migration_steps")]


# ── Le journal, pas à pas ────────────────────────────────────────────────────

def test_chaque_instruction_est_journalisee_puis_validee(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(M, "_ddl_is_transactional", lambda: False)
    monkeypatch.setattr(M, "_steps_table_ddl_active", lambda: "CREATE TABLE IF NOT EXISTS forge_migration_steps (probe INT)")
    connexion = _Connexion()

    M._apply_one_migration(connexion, _migration(tmp_path, _SQL),  # pyright: ignore[reportPrivateUsage]
                           recorded_steps={})

    pas = _sql_journalises(connexion)
    assert [p[1][1] for p in pas] == [1, 2, 3], "une ligne de journal par instruction"
    # Chaque pas est validé explicitement avant l'instruction suivante.
    assert connexion.commits.count("explicite") >= 4  # 3 pas + enregistrement final


def test_le_journal_est_efface_quand_la_migration_aboutit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(M, "_ddl_is_transactional", lambda: False)
    monkeypatch.setattr(M, "_steps_table_ddl_active", lambda: "CREATE TABLE IF NOT EXISTS forge_migration_steps (probe INT)")
    connexion = _Connexion()

    M._apply_one_migration(connexion, _migration(tmp_path, _SQL),  # pyright: ignore[reportPrivateUsage]
                           recorded_steps={})

    sqls = [s for s, _ in connexion.executed]
    position_delete = next(i for i, s in enumerate(sqls) if s.startswith("DELETE FROM forge_migration_steps"))
    position_record = next(i for i, s in enumerate(sqls) if s.startswith("INSERT INTO forge_migrations "))
    assert position_delete < position_record, "le journal s'efface avec l'enregistrement"


def test_un_echec_laisse_le_journal_du_prefixe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Le scénario du cycle 3 : casse à l'instruction 3, les pas 1 et 2 restent."""
    monkeypatch.setattr(M, "_ddl_is_transactional", lambda: False)
    monkeypatch.setattr(M, "_steps_table_ddl_active", lambda: "CREATE TABLE IF NOT EXISTS forge_migration_steps (probe INT)")
    connexion = _Connexion(fautive="TABLE c")

    with pytest.raises(M.MigrationError) as capture:
        M._apply_one_migration(connexion, _migration(tmp_path, _SQL),  # pyright: ignore[reportPrivateUsage]
                               recorded_steps={})

    assert [p[1][1] for p in _sql_journalises(connexion)] == [1, 2]
    assert "la reprise continuera à l'instruction 3" in str(capture.value)


# ── La reprise ───────────────────────────────────────────────────────────────

def _pas(sql: str, *positions: int) -> "list[tuple[int, str]]":
    statements = M.split_sql_statements(sql)
    return [(p, M._statement_checksum(statements[p - 1]))  # pyright: ignore[reportPrivateUsage]
            for p in positions]


def test_la_reprise_ne_rejoue_pas_le_prefixe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(M, "_ddl_is_transactional", lambda: False)
    monkeypatch.setattr(M, "_steps_table_ddl_active", lambda: "CREATE TABLE IF NOT EXISTS forge_migration_steps (probe INT)")
    connexion = _Connexion()

    M._apply_one_migration(  # pyright: ignore[reportPrivateUsage]
        connexion, _migration(tmp_path, _SQL),
        recorded_steps={"20260730120000": _pas(_SQL, 1, 2)},
    )

    sqls = [s for s, _ in connexion.executed]
    assert not any("TABLE a" in s for s in sqls), "l'instruction 1 ne doit pas être rejouée"
    assert not any("TABLE b" in s for s in sqls), "l'instruction 2 ne doit pas être rejouée"
    assert any("TABLE c" in s for s in sqls), "l'instruction 3 doit s'exécuter"
    assert "[REPRISE]" in capsys.readouterr().out, "la reprise est bruyante"


def test_la_reprise_tolere_le_reformatage_du_prefixe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sauts de ligne entre les mots et commentaires ne changent pas le SQL déjà appliqué.

    L'empreinte normalise les blancs entre les mots, et le découpeur canonique
    ôte les commentaires. Un espace introduit à l'intérieur d'un mot ou d'une
    parenthèse reste en revanche un changement : l'empreinte ne devine pas.
    """
    monkeypatch.setattr(M, "_ddl_is_transactional", lambda: False)
    monkeypatch.setattr(M, "_steps_table_ddl_active", lambda: "CREATE TABLE IF NOT EXISTS forge_migration_steps (probe INT)")
    reformate = (
        "-- reprise après correction\n"
        "CREATE TABLE\n    a (id INT);\n"
        "CREATE TABLE b\n    (id INT);\n"
        "CREATE TABLE c (id INT);\n"
    )
    connexion = _Connexion()

    M._apply_one_migration(  # pyright: ignore[reportPrivateUsage]
        connexion, _migration(tmp_path, reformate),
        recorded_steps={"20260730120000": _pas(_SQL, 1, 2)},
    )

    assert any("TABLE c" in s for s, _ in connexion.executed)


def test_un_prefixe_reecrit_est_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """La base a exécuté l'instruction telle quelle : le fichier ne peut pas la réécrire."""
    monkeypatch.setattr(M, "_ddl_is_transactional", lambda: False)
    reecrit = _SQL.replace("CREATE TABLE a (id INT)", "CREATE TABLE a (id BIGINT)")
    connexion = _Connexion()

    with pytest.raises(M.MigrationError, match="reprise refusée") as capture:
        M._apply_one_migration(  # pyright: ignore[reportPrivateUsage]
            connexion, _migration(tmp_path, reecrit),
            recorded_steps={"20260730120000": _pas(_SQL, 1)},
        )

    assert "l'instruction 1" in str(capture.value)
    assert connexion.executed == [], "rien ne doit s'exécuter sur un préfixe réécrit"


def test_un_journal_incoherent_est_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Position hors du fichier ou trou dans la séquence : on n'invente pas."""
    monkeypatch.setattr(M, "_ddl_is_transactional", lambda: False)
    connexion = _Connexion()

    with pytest.raises(M.MigrationError, match="incohérent"):
        M._apply_one_migration(  # pyright: ignore[reportPrivateUsage]
            connexion, _migration(tmp_path, _SQL),
            recorded_steps={"20260730120000": [(7, "abc")]},
        )


# ── Le backend transactionnel ne change pas ──────────────────────────────────

def test_un_backend_transactionnel_ne_journalise_rien(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """L'annulation défait tout : la migration reste atomique, sans journal."""
    monkeypatch.setattr(M, "_ddl_is_transactional", lambda: True)
    connexion = _Connexion()

    M._apply_one_migration(connexion, _migration(tmp_path, _SQL))  # pyright: ignore[reportPrivateUsage]

    sqls = [s for s, _ in connexion.executed]
    assert not any("forge_migration_steps" in s for s in sqls)
    assert connexion.commits.count("explicite") == 1, "un seul commit : l'atomicité"
