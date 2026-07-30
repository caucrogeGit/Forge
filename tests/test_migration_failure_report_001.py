"""MIGRATION-DDL-NON-TRANSACTIONAL-REVEAL-001 : dire ce qui a vraiment eu lieu.

`_apply_one_migration` ouvre une transaction, exécute les instructions, inscrit
la migration au journal, valide, et sur erreur appelle `_rollback_quietly`. La
forme suppose l'atomicité. Vérifié sur les quatre serveurs avec une migration à
deux `CREATE TABLE` dont le second est fautif :

    PostgreSQL   annule les deux            atomique
    SQL Server   annule les deux            atomique
    SQLite       annule les deux            atomique
    MariaDB      garde la première table    **non atomique**

MariaDB valide implicitement autour de chaque instruction de définition : la
transaction est close à son insu et le `ROLLBACK` ne trouve plus rien à défaire.

La conséquence était muette et bloquante. La table existe, le journal
n'enregistre pas la migration, et relancer `migration:apply` rejoue la première
instruction qui échoue sur « already exists ». Aucune commande de rattrapage
n'existe, le jeu étant `status`/`apply`/`make`/`diff`.

Forge ne peut pas rendre transactionnel ce qui ne l'est pas. Il applique la
règle B, révéler avant de corriger : dire quelle instruction a échoué, ce qui
persiste, et pourquoi une relance échouera.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from core.database.backend import Dialect

pytest.importorskip("forge_mvc_entities")
from forge_mvc_entities import migrations as M  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ── La capacité au contrat ───────────────────────────────────────────────────

def test_le_contrat_porte_la_capacite() -> None:
    assert hasattr(Dialect, "supports_transactional_ddl")


def test_le_contrat_designe_mariadb_comme_l_exception() -> None:
    """Le relevé sur serveur réel vit dans le contrat, pas dans un test isolé."""
    doc = Dialect.supports_transactional_ddl.__doc__ or ""

    assert "MariaDB" in doc
    assert "PostgreSQL" in doc


def test_le_contrat_interdit_les_compensations_ecrites_a_l_aveugle() -> None:
    """La capacité informe le message, elle ne pilote pas une stratégie.

    Émettre des `DROP` compensatoires pour simuler une annulation serait la
    magie que le principe 3 refuse, et détruirait des données sur une migration
    qui touche à des tables existantes.
    """
    doc = Dialect.supports_transactional_ddl.__doc__ or ""

    assert "change pas" in doc


@pytest.mark.parametrize(
    ("module", "classe", "attendu"),
    [
        ("forge_mvc_mariadb.dialect", "MariaDBDialect", False),
        ("forge_mvc_sqlite.dialect", "SQLiteDialect", True),
        ("forge_mvc_postgres.dialect", "PostgreSQLDialect", True),
        ("forge_mvc_mssql.dialect", "MSSQLDialect", True),
    ],
)
def test_chaque_dialecte_repond_ce_qui_a_ete_mesure(
    module: str, classe: str, attendu: bool,
) -> None:
    importe = pytest.importorskip(module)

    assert getattr(importe, classe)().supports_transactional_ddl() is attendu


# ── Le rapport d'échec ───────────────────────────────────────────────────────

def _migration(tmp_path: Path, sql: str) -> "M.MigrationFile":
    chemin = tmp_path / "20260728_120000_essai.sql"
    chemin.write_text(sql, encoding="utf-8")
    return M.MigrationFile(
        path=chemin, version="20260728_120000", name="essai",
        filename=chemin.name, checksum="abc",
    )


SQL_TROIS = (
    "CREATE TABLE a (id INT);\n"
    "CREATE TABLE b (id INT);\n"
    "CREATE TABLE c (id NOTATYPE);\n"
)


def test_le_rapport_situe_l_instruction_fautive(tmp_path: Path) -> None:
    """Le message ne disait que le nom du fichier : illisible sur 40 instructions."""
    migration = _migration(tmp_path, SQL_TROIS)

    rapport = M._failed_migration_report(  # pyright: ignore[reportPrivateUsage]
        migration, ["un", "deux", "trois"], 2, RuntimeError("Unknown data type"),
    )

    assert "instruction 3 sur 3" in rapport
    assert "trois" in rapport
    assert "Unknown data type" in rapport


def test_le_rapport_nomme_le_fichier(tmp_path: Path) -> None:
    migration = _migration(tmp_path, SQL_TROIS)

    rapport = M._failed_migration_report(  # pyright: ignore[reportPrivateUsage]
        migration, ["un"], 0, RuntimeError("boum"),
    )

    assert "20260728_120000_essai.sql" in rapport


def test_un_echec_sur_la_toute_premiere_instruction(tmp_path: Path) -> None:
    """Rien n'a pris effet : le rapport ne doit pas annoncer de persistance."""
    migration = _migration(tmp_path, SQL_TROIS)

    rapport = M._failed_migration_report(  # pyright: ignore[reportPrivateUsage]
        migration, ["un", "deux"], 0, RuntimeError("boum"),
    )

    assert "instruction 1 sur 2" in rapport
    assert "PERSISTENT" not in rapport


def test_un_echec_a_l_enregistrement_au_journal(tmp_path: Path) -> None:
    """Toutes les instructions ont passé : l'index sort du tableau.

    Sans ce cas, le rapport lèverait un `IndexError` en tentant de citer une
    instruction inexistante, et l'erreur d'origine serait perdue.
    """
    migration = _migration(tmp_path, SQL_TROIS)

    rapport = M._failed_migration_report(  # pyright: ignore[reportPrivateUsage]
        migration, ["un", "deux"], 2, RuntimeError("journal indisponible"),
    )

    assert "journal" in rapport
    assert "2 instructions" in rapport


def test_une_instruction_longue_est_tronquee(tmp_path: Path) -> None:
    """Un `CREATE TABLE` de trente colonnes noierait le message."""
    migration = _migration(tmp_path, SQL_TROIS)
    longue = "CREATE TABLE t (" + ", ".join(f"col_{i} INT" for i in range(40)) + ")"

    rapport = M._failed_migration_report(  # pyright: ignore[reportPrivateUsage]
        migration, [longue], 0, RuntimeError("boum"),
    )

    assert "..." in rapport
    assert max(len(ligne) for ligne in rapport.splitlines()) < 200


def test_le_saut_de_ligne_de_l_instruction_est_aplati(tmp_path: Path) -> None:
    """Le SQL est écrit sur plusieurs lignes ; le rapport tient sur une."""
    migration = _migration(tmp_path, SQL_TROIS)

    rapport = M._failed_migration_report(  # pyright: ignore[reportPrivateUsage]
        migration, ["CREATE TABLE t (\n    id INT\n)"], 0, RuntimeError("boum"),
    )

    assert "CREATE TABLE t ( id INT )" in rapport


# ── L'avertissement de persistance, conditionné au backend ───────────────────

def test_le_backend_non_transactionnel_declenche_l_avertissement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(M, "_ddl_is_transactional", lambda: False)
    migration = _migration(tmp_path, SQL_TROIS)

    rapport = M._failed_migration_report(  # pyright: ignore[reportPrivateUsage]
        migration, ["CREATE TABLE a (id INT)", "CREATE TABLE b (id INT)",
                    "CREATE TABLE c (id INT)"], 2, RuntimeError("boum"),
    )

    assert "PERSISTENT" in rapport
    assert "2 instructions précédentes" in rapport


def test_une_migration_purement_dml_ne_menace_pas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sans DDL, le rollback annule tout, même sur MariaDB : rien ne persiste.

    Annoncer une persistance qui n'a pas eu lieu ferait défaire à la main des
    écritures déjà annulées.
    """
    monkeypatch.setattr(M, "_ddl_is_transactional", lambda: False)
    migration = _migration(tmp_path, SQL_TROIS)

    rapport = M._failed_migration_report(  # pyright: ignore[reportPrivateUsage]
        migration, ["INSERT INTO t VALUES (1)", "INSERT INTO t VALUES (2)"],
        1, RuntimeError("boum"),
    )

    assert "PERSISTENT" not in rapport


def test_l_avertissement_dit_comment_reprendre(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Le point qui débloque : relancer reprend, et le message le dit.

    Avant `MIGRATION-RESUME-JOURNAL-001`, il expliquait pourquoi relancer
    échouerait et demandait de défaire à la main. Le journal de reprise a
    retiré la cause : le conseil est devenu la marche à suivre.
    """
    monkeypatch.setattr(M, "_ddl_is_transactional", lambda: False)
    migration = _migration(tmp_path, SQL_TROIS)

    rapport = M._failed_migration_report(  # pyright: ignore[reportPrivateUsage]
        migration, ["CREATE TABLE a (id INT)", "CREATE TABLE b (id INT)"],
        1, RuntimeError("boum"),
    )

    assert "journal de reprise" in rapport
    assert "ne seront PAS rejouées" in rapport
    assert "la reprise continuera à l'instruction 2" in rapport
    assert "défaites à la main" not in rapport


def test_l_echec_d_enregistrement_dit_que_rien_ne_sera_rejoue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Toutes les instructions sont journalisées : la relance ne rejoue rien."""
    monkeypatch.setattr(M, "_ddl_is_transactional", lambda: False)
    migration = _migration(tmp_path, SQL_TROIS)

    rapport = M._failed_migration_report(  # pyright: ignore[reportPrivateUsage]
        migration, ["CREATE TABLE a (id INT)", "CREATE TABLE b (id INT)"],
        2, RuntimeError("journal indisponible"),
    )

    assert "rien ne sera rejoué" in rapport
    assert "Corrigez l'instruction" not in rapport


def test_un_backend_transactionnel_reste_silencieux(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sur PostgreSQL le rollback a fait son travail : rien à signaler."""
    monkeypatch.setattr(M, "_ddl_is_transactional", lambda: True)
    migration = _migration(tmp_path, SQL_TROIS)

    rapport = M._failed_migration_report(  # pyright: ignore[reportPrivateUsage]
        migration, ["un", "deux", "trois"], 2, RuntimeError("boum"),
    )

    assert "PERSISTENT" not in rapport


def test_sans_backend_on_suppose_l_atomicite(monkeypatch: pytest.MonkeyPatch) -> None:
    """Le choix prudent pour le message : ne pas menacer sans preuve.

    Un backend tiers antérieur à la capacité reste silencieux plutôt
    qu'alarmiste à tort.
    """
    def _pas_de_backend() -> object:
        raise RuntimeError("aucun backend installé")

    monkeypatch.setattr("core.database.backend.get_backend", _pas_de_backend)

    assert M._ddl_is_transactional() is True  # pyright: ignore[reportPrivateUsage]


def test_le_runner_appelle_bien_le_rapport() -> None:
    """Garde-fou de câblage : le message d'origine ne doit pas revenir."""
    source = (PROJECT_ROOT / "packages" / "forge-mvc-entities" / "forge_mvc_entities"
              / "migrations.py").read_text(encoding="utf-8")

    assert "_failed_migration_report(migration, statements, executed, exc)" in source
    assert "erreur SQL pendant l'application" not in source
