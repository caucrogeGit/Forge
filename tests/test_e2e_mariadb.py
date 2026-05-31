"""
Tests E2E-MARIADB-001 — Application SQL réelle sur MariaDB.

Activation :
    FORGE_E2E_MARIADB=1 pytest tests/test_e2e_mariadb.py

Variables d'environnement :
    FORGE_E2E_MARIADB=1                 active les tests (requis)
    FORGE_E2E_DB_HOST=127.0.0.1         hôte MariaDB (défaut: 127.0.0.1)
    FORGE_E2E_DB_PORT=3306              port MariaDB (défaut: 3306)
    FORGE_E2E_DB_NAME=forge_e2e_test    base de test (doit commencer par forge_e2e_)
    FORGE_E2E_DB_USER=forge_e2e_user    utilisateur MariaDB
    FORGE_E2E_DB_PASSWORD=              mot de passe

Sécurité :
    Si FORGE_E2E_DB_NAME ne commence pas par "forge_e2e_", les tests refusent
    de s'exécuter pour protéger une base applicative réelle.
    Les tables créées par les tests sont supprimées avant et après le module.

Cycle testé :
    1  connexion directe à MariaDB réussie
    2  génération d'entité Contact (make:entity --no-input)
    3  SQL généré par Forge (CREATE TABLE IF NOT EXISTS)
    4  application SQL réelle via apply_model_sql
    5  table contact présente dans la base
    6  colonne id vérifiée par introspection
    7  insertion simple et lecture simple
    8  nettoyage (DROP TABLE IF EXISTS contact)

Sans FORGE_E2E_MARIADB :
    Tous les tests sont ignorés proprement (SKIPPED).
"""
from __future__ import annotations

import contextlib
import os
from pathlib import Path

import pytest

# ── Garde : module désactivé par défaut ───────────────────────────────────────

if not os.environ.get("FORGE_E2E_MARIADB"):
    pytest.skip(
        "FORGE_E2E_MARIADB non défini — tests MariaDB ignorés. "
        "Lance avec : FORGE_E2E_MARIADB=1 pytest tests/test_e2e_mariadb.py",
        allow_module_level=True,
    )

# ── Garde : package mariadb requis ────────────────────────────────────────────

try:
    import mariadb as _mariadb_pkg  # noqa: F401
except ImportError:
    pytest.skip(
        "Package Python 'mariadb' non installé — tests MariaDB ignorés.",
        allow_module_level=True,
    )

# ── Variables E2E ─────────────────────────────────────────────────────────────

_DB_HOST     = os.environ.get("FORGE_E2E_DB_HOST", "127.0.0.1")
_DB_PORT     = int(os.environ.get("FORGE_E2E_DB_PORT", "3306"))
_DB_NAME     = os.environ.get("FORGE_E2E_DB_NAME", "")
_DB_USER     = os.environ.get("FORGE_E2E_DB_USER", "")
_DB_PASSWORD = os.environ.get("FORGE_E2E_DB_PASSWORD", "")
_SAFE_PREFIX = "forge_e2e_"

# ── Garde de sécurité : nom de base réservé aux tests ─────────────────────────
# Refuse (ValueError → erreur de collection pytest) si la base n'est pas sûre.

if not _DB_NAME.startswith(_SAFE_PREFIX):
    raise ValueError(
        f"Sécurité : FORGE_E2E_DB_NAME='{_DB_NAME}' doit commencer par '{_SAFE_PREFIX}'. "
        "Définit une base dédiée aux tests E2E (ex : forge_e2e_test). Tests annulés."
    )

# ── Imports Forge ─────────────────────────────────────────────────────────────

from forge_cli.entities.db_apply import apply_model_sql
from forge_cli.entities.make_entity import main as make_entity_main

# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _scaffold_project(root: Path) -> None:
    """Projet Forge minimal avec config.py lisant les variables FORGE_E2E_*."""
    _write(
        root / "config.py",
        "import os\n"
        "APP_NAME = 'TestForgeMariaDB'\n"
        "APP_ROUTES_MODULE = 'mvc.routes'\n"
        "DB_APP_HOST = os.environ.get('FORGE_E2E_DB_HOST', '127.0.0.1')\n"
        "DB_APP_PORT = int(os.environ.get('FORGE_E2E_DB_PORT', '3306'))\n"
        "DB_APP_LOGIN = os.environ.get('FORGE_E2E_DB_USER', '')\n"
        "DB_APP_PWD = os.environ.get('FORGE_E2E_DB_PASSWORD', '')\n"
        "DB_NAME = os.environ.get('FORGE_E2E_DB_NAME', '')\n",
    )
    _write(root / "app.py", "# app")
    (root / "mvc" / "controllers").mkdir(parents=True)
    (root / "mvc" / "views").mkdir(parents=True)
    (root / "mvc" / "entities").mkdir(parents=True)
    _write(
        root / "mvc" / "routes.py",
        "from core.http.router import Router\nrouter = Router()\n",
    )


@contextlib.contextmanager
def _in_dir(path: Path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def _direct_connect():
    """Connexion directe à MariaDB pour les assertions et le nettoyage."""
    import mariadb
    return mariadb.connect(
        host=_DB_HOST,
        port=_DB_PORT,
        user=_DB_USER,
        password=_DB_PASSWORD,
        database=_DB_NAME,
    )


def _table_exists(conn, table_name: str) -> bool:
    cursor = conn.cursor()
    try:
        cursor.execute("SHOW TABLES LIKE ?", (table_name,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()


def _get_columns(conn, table_name: str) -> list[str]:
    """Retourne les noms de colonnes (en minuscules) via DESCRIBE."""
    cursor = conn.cursor()
    try:
        cursor.execute(f"DESCRIBE `{table_name}`")
        return [row[0].lower() for row in cursor.fetchall()]
    finally:
        cursor.close()


def _get_pk_column(conn, table_name: str) -> str | None:
    """Retourne le nom exact de la colonne PRIMARY KEY."""
    cursor = conn.cursor()
    try:
        cursor.execute(f"DESCRIBE `{table_name}`")
        for row in cursor.fetchall():
            if row[3] == "PRI":
                return row[0]
        return None
    finally:
        cursor.close()


def _drop_table(conn, table_name: str) -> None:
    cursor = conn.cursor()
    try:
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
        conn.commit()
    finally:
        cursor.close()


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module", autouse=True)
def _cleanup_contact():
    """Supprime la table contact avant ET après tous les tests du module."""
    try:
        conn = _direct_connect()
        _drop_table(conn, "contact")
        conn.close()
    except Exception:
        pass  # toléré : la table n'existe peut-être pas encore
    yield
    try:
        conn = _direct_connect()
        _drop_table(conn, "contact")
        conn.close()
    except Exception:
        pass  # nettoyage best-effort


@pytest.fixture(scope="module")
def e2e_project(tmp_path_factory):
    """Projet Forge minimal avec entité Contact générée (make:entity --no-input)."""
    root = tmp_path_factory.mktemp("e2e_mariadb")
    _scaffold_project(root)
    with _in_dir(root):
        make_entity_main(["Contact", "--no-input"])
    return root


@pytest.fixture(scope="module")
def applied_project(e2e_project):
    """Projet avec SQL appliqué sur la base MariaDB de test."""
    with _in_dir(e2e_project):
        apply_model_sql(e2e_project / "mvc" / "entities")
    return e2e_project


# ── Connexion ─────────────────────────────────────────────────────────────────

class TestMariaDbConnection:
    def test_connection_succeeds(self):
        conn = _direct_connect()
        conn.close()

    def test_connection_to_correct_database(self):
        conn = _direct_connect()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DATABASE()")
            db = cursor.fetchone()[0]
            cursor.close()
        finally:
            conn.close()
        assert db == _DB_NAME


# ── Génération SQL ────────────────────────────────────────────────────────────

class TestEntitySqlGeneration:
    @pytest.fixture(autouse=True)
    def _setup(self, e2e_project):
        self.root = e2e_project

    def test_entity_json_created(self):
        assert (self.root / "mvc" / "entities" / "contact" / "contact.json").exists()

    def test_entity_sql_created(self):
        assert (self.root / "mvc" / "entities" / "contact" / "contact.sql").exists()

    def test_entity_sql_not_empty(self):
        content = (
            self.root / "mvc" / "entities" / "contact" / "contact.sql"
        ).read_text(encoding="utf-8")
        assert content.strip() != ""

    def test_entity_sql_contains_create_table(self):
        content = (
            self.root / "mvc" / "entities" / "contact" / "contact.sql"
        ).read_text(encoding="utf-8")
        assert "CREATE TABLE" in content.upper()

    def test_entity_sql_contains_table_name(self):
        content = (
            self.root / "mvc" / "entities" / "contact" / "contact.sql"
        ).read_text(encoding="utf-8")
        assert "contact" in content.lower()


# ── Application SQL ───────────────────────────────────────────────────────────

class TestDbApply:
    @pytest.fixture(autouse=True)
    def _setup(self, applied_project):
        self.root = applied_project

    def test_contact_table_created(self):
        conn = _direct_connect()
        try:
            assert _table_exists(conn, "contact")
        finally:
            conn.close()

    def test_contact_table_has_id_column(self):
        conn = _direct_connect()
        try:
            columns = _get_columns(conn, "contact")
        finally:
            conn.close()
        assert "id" in columns

    def test_contact_table_has_primary_key(self):
        conn = _direct_connect()
        try:
            pk = _get_pk_column(conn, "contact")
        finally:
            conn.close()
        assert pk is not None


# ── Insertion et lecture ──────────────────────────────────────────────────────

class TestInsertRead:
    @pytest.fixture(autouse=True)
    def _setup(self, applied_project):
        self.root = applied_project

    def test_insert_contact(self):
        conn = _direct_connect()
        try:
            cursor = conn.cursor()
            try:
                # Contact (make:entity --no-input) a un champ `title` requis :
                # l'INSERT doit le fournir, l'Id s'auto-incrémente.
                cursor.execute("INSERT INTO `contact` (`Title`) VALUES ('Contact e2e')")
                conn.commit()
                inserted_id = cursor.lastrowid
            finally:
                cursor.close()
        finally:
            conn.close()
        assert inserted_id > 0

    def test_read_contact(self):
        conn = _direct_connect()
        try:
            pk = _get_pk_column(conn, "contact")
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO `contact` (`Title`) VALUES ('Lecture e2e')")
                conn.commit()
                cursor.execute(
                    f"SELECT `{pk}` FROM `contact` WHERE `Title` = 'Lecture e2e' LIMIT 1"
                )
                row = cursor.fetchone()
            finally:
                cursor.close()
        finally:
            conn.close()
        assert row is not None
        assert row[0] > 0
