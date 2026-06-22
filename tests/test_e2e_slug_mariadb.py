"""
Tests E2E-SLUG-MARIADB (`BETA13-DOGFOOD-001`) — pipeline slug réel sur MariaDB.

Dogfood de la Phase 4 : valider, contre une **vraie** base MariaDB, le pipeline
slug complet de Forge tel qu'il est généré — pas en mémoire, pas en mock.

Activation (identique à test_e2e_mariadb.py) :
    FORGE_E2E_MARIADB=1 pytest tests/test_e2e_slug_mariadb.py

Variables d'environnement :
    FORGE_E2E_MARIADB=1                 active les tests (requis)
    FORGE_E2E_DB_HOST=127.0.0.1         hôte MariaDB (défaut: 127.0.0.1)
    FORGE_E2E_DB_PORT=3306              port MariaDB (défaut: 3306)
    FORGE_E2E_DB_NAME=forge_e2e_test    base de test (doit commencer par forge_e2e_)
    FORGE_E2E_DB_USER=forge_e2e_user    utilisateur MariaDB
    FORGE_E2E_DB_PASSWORD=              mot de passe

Sécurité :
    Si FORGE_E2E_DB_NAME ne commence pas par "forge_e2e_", les tests refusent de
    s'exécuter. La table `articles` est supprimée avant ET après le module.

Cycle testé (entité Article : `title` texte + `slug` auto depuis `title`) :
    1  l'entité passe le pipeline canonique réel (normalise → valide)
    2  Forge produit le DDL réel (build_entity_sql) : Slug VARCHAR(180) + UNIQUE
    3  application SQL réelle via apply_model_sql (chemin Forge db:apply)
    4  introspection : colonne Slug présente, VARCHAR(180), contrainte UNIQUE
    5  runtime : slugify(title) → INSERT (Title, Slug) → SELECT by Slug (get_by_slug)
    6  unicité : un second titre slugifiant à l'identique est rejeté par MariaDB

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
        "Lance avec : FORGE_E2E_MARIADB=1 pytest tests/test_e2e_slug_mariadb.py",
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

if not _DB_NAME.startswith(_SAFE_PREFIX):
    raise ValueError(
        f"Sécurité : FORGE_E2E_DB_NAME='{_DB_NAME}' doit commencer par '{_SAFE_PREFIX}'. "
        "Définit une base dédiée aux tests E2E (ex : forge_e2e_test). Tests annulés."
    )

# ── Imports Forge (pipeline réel) ─────────────────────────────────────────────

from core.http.slug import slugify
from cli.entities.canonical_model_normalizer import (
    normalize_canonical_entity_for_model_build,
)
from cli.entities.db_apply import apply_model_sql
from cli.entities.make_entity import build_entity_sql
from cli.entities.validation import validate_entity_definition

# ── Entité de test : Article avec slug auto-généré depuis title ───────────────

_ARTICLE_ENTITY = {
    "schema_version": "1.0",
    "name": "Article",
    "table": "articles",
    "fields": [
        {"name": "title", "type": "string", "max_length": 255, "required": True},
        {"name": "slug", "type": "slug", "source": "title", "unique": True, "required": True},
    ],
    "options": {"timestamps": False, "soft_delete": False},
}


def _article_definition() -> dict:
    """Définition canonique validée, via le pipeline réel (normalise → valide)."""
    return validate_entity_definition(
        normalize_canonical_entity_for_model_build(_ARTICLE_ENTITY),
        source="<e2e-slug>",
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _scaffold_project(root: Path) -> None:
    """Projet Forge minimal avec config.py lisant les variables FORGE_E2E_*."""
    _write(
        root / "config.py",
        "import os\n"
        "APP_NAME = 'TestForgeSlugMariaDB'\n"
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


def _describe(conn, table_name: str) -> dict[str, tuple]:
    """Retourne {nom_colonne_minuscule: (Field, Type, Null, Key, Default, Extra)}."""
    cursor = conn.cursor()
    try:
        cursor.execute(f"DESCRIBE `{table_name}`")
        return {row[0].lower(): tuple(row) for row in cursor.fetchall()}
    finally:
        cursor.close()


def _slug_column(conn) -> tuple:
    """La ligne DESCRIBE de la colonne slug (insensible à la casse du nom)."""
    return _describe(conn, "articles")["slug"]


def _drop_table(conn, table_name: str) -> None:
    cursor = conn.cursor()
    try:
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
        conn.commit()
    finally:
        cursor.close()


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module", autouse=True)
def _cleanup_articles():
    """Supprime la table articles avant ET après tous les tests du module."""
    try:
        conn = _direct_connect()
        _drop_table(conn, "articles")
        conn.close()
    except Exception:
        pass  # toléré : la table n'existe peut-être pas encore
    yield
    try:
        conn = _direct_connect()
        _drop_table(conn, "articles")
        conn.close()
    except Exception:
        pass  # nettoyage best-effort


@pytest.fixture(scope="module")
def applied_project(tmp_path_factory):
    """Projet scaffoldé + entité Article (slug) appliquée sur la base de test.

    Écrit le `.sql` produit par le **vrai** générateur Forge (build_entity_sql),
    puis applique via apply_model_sql (chemin Forge db:apply).
    """
    import json

    root = tmp_path_factory.mktemp("e2e_slug_mariadb")
    _scaffold_project(root)
    definition = _article_definition()
    entities_root = root / "mvc" / "entities"
    entity_dir = entities_root / "article"
    # Modèle complet attendu par check_model : .json (entité), .sql (DDL), relations.json.
    _write(entity_dir / "article.json", json.dumps(_ARTICLE_ENTITY, indent=2) + "\n")
    _write(entity_dir / "article.sql", build_entity_sql(definition))
    _write(
        entities_root / "relations.json",
        json.dumps({"schema_version": "1.0", "relations": []}, indent=2) + "\n",
    )
    # relations.sql attendu par collect_sql_files (vide = aucune relation).
    _write(entities_root / "relations.sql", "")
    with _in_dir(root):
        apply_model_sql(entities_root)
    return root


# ── 1-2. Pipeline canonique + DDL réel ────────────────────────────────────────

class TestSlugDdlGeneration:
    def test_definition_passes_real_pipeline(self):
        # normalise → valide sans lever : le contrat accepte slug + source.
        definition = _article_definition()
        names = [f["name"].lower() for f in definition["fields"]]
        assert "slug" in names

    def test_ddl_has_slug_varchar_180_and_unique(self):
        ddl = build_entity_sql(_article_definition()).upper()
        assert "SLUG VARCHAR(180) NOT NULL" in ddl
        assert "UNIQUE KEY" in ddl
        assert "SLUG" in ddl


# ── 3-4. Application réelle + introspection ───────────────────────────────────

class TestSlugTableApplied:
    @pytest.fixture(autouse=True)
    def _setup(self, applied_project):
        self.root = applied_project

    def test_articles_table_has_slug_column(self):
        conn = _direct_connect()
        try:
            columns = _describe(conn, "articles")
        finally:
            conn.close()
        assert "slug" in columns

    def test_slug_column_is_varchar_180(self):
        conn = _direct_connect()
        try:
            col = _slug_column(conn)
        finally:
            conn.close()
        # col[1] = Type, ex. 'varchar(180)'
        assert col[1].lower() == "varchar(180)"

    def test_slug_column_is_unique(self):
        conn = _direct_connect()
        try:
            col = _slug_column(conn)
        finally:
            conn.close()
        # col[3] = Key ; 'UNI' pour une contrainte d'unicité.
        assert col[3] == "UNI"


# ── 5. Runtime : slugify → INSERT → get_by_slug ───────────────────────────────

class TestSlugRuntime:
    @pytest.fixture(autouse=True)
    def _setup(self, applied_project):
        self.root = applied_project

    def test_insert_then_read_by_slug(self):
        title = "Mon Premier Été à Paris"
        slug = slugify(title)  # même fonction que le contrôleur généré
        assert slug == "mon-premier-ete-a-paris"

        conn = _direct_connect()
        try:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO `articles` (`Title`, `Slug`) VALUES (?, ?)",
                    (title, slug),
                )
                conn.commit()
                # Lecture par slug, comme le get_<entity>_by_<slug> généré.
                cursor.execute(
                    "SELECT `Title` FROM `articles` WHERE `Slug` = ? LIMIT 1",
                    (slug,),
                )
                row = cursor.fetchone()
            finally:
                cursor.close()
        finally:
            conn.close()
        assert row is not None
        assert row[0] == title


# ── 6. Unicité : doublon de slug rejeté par MariaDB ───────────────────────────

class TestSlugUniqueness:
    @pytest.fixture(autouse=True)
    def _setup(self, applied_project):
        self.root = applied_project

    def test_duplicate_slug_is_rejected(self):
        import mariadb

        # Deux titres distincts qui slugifient vers le MÊME slug.
        title_a = "Guide Forge"
        title_b = "guide   forge"
        slug = slugify(title_a)
        assert slugify(title_b) == slug  # collision attendue

        conn = _direct_connect()
        try:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO `articles` (`Title`, `Slug`) VALUES (?, ?)",
                    (title_a, slug),
                )
                conn.commit()
                with pytest.raises(mariadb.IntegrityError):
                    cursor.execute(
                        "INSERT INTO `articles` (`Title`, `Slug`) VALUES (?, ?)",
                        (title_b, slug),
                    )
                    conn.commit()
            finally:
                cursor.close()
        finally:
            conn.close()
