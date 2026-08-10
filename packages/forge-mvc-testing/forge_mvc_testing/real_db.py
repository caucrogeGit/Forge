"""Fixtures d'intégration contre un serveur de base réel (TESTING-REAL-DB-FIXTURES-001).

Ces fixtures configurent Forge sur un serveur de test puis rendent la main : le
test qui les demande passe ensuite par la **vraie couche d'accès**,
`core.database.db`, celle que l'application utilise en production.

## Pourquoi elles vivent ici

Elles étaient dans `tests/db/conftest.py`, donc invisibles aux tests des paquets
opt-in, qui sont sous `packages/*/tests/`. Chacun de ces paquets avait donc
réécrit son propre adaptateur de connexion à la main. Un adaptateur fait main
court-circuite la traduction des marqueurs de paramètre et la **qualification
d'erreur** de Forge : les tests restaient verts sur du code qui ne l'était pas.
C'est ce qui a caché deux défauts du magasin anti-rejeu MFA pendant tout un
cycle. `forge-mvc-testing` est l'emplacement prévu pour l'infrastructure de test
partagée (ADR-041), et le principe 11 veut une seule façon officielle de monter
une base de test.

## Le choix du serveur

`real_backend_db` est paramétrée sur les trois serveurs, et **chaque paramètre
porte ses propres marqueurs**. Un test qui la demande produit donc trois cas,
que la CI sélectionne un par un avec `-m db`, `-m db_pg` et `-m db_mssql`, sans
que le test ait à être écrit trois fois. Un test qui veut un seul serveur
demande directement `real_db`, `real_pg_db` ou `real_mssql_db`.

## En l'absence de serveur

En local, le test est **sauté** avec le motif réel de l'échec de connexion. En
CI, `FORGE_REQUIRE_DB=1` (et ses variantes par backend) transforme le saut en
**échec** : la couche base ne doit jamais être verte par défaut.
"""
from __future__ import annotations

import contextlib
import os
from collections.abc import Iterator, Sequence
from typing import Any

import pytest

from forge_mvc_testing.db_probe import connection_failure_message

_REQUIRE_DB = os.environ.get("FORGE_REQUIRE_DB") == "1"
_REQUIRE_DB_PG = os.environ.get("FORGE_REQUIRE_DB_PG") == "1"
_REQUIRE_DB_MSSQL = os.environ.get("FORGE_REQUIRE_DB_MSSQL") == "1"

#: Nom de fixture à demander pour chaque backend paramétré.
_FIXTURE_PAR_BACKEND = {
    "mariadb": "real_db",
    "postgres": "real_pg_db",
    "mssql": "real_mssql_db",
}


def _nom_par_worker(base: str) -> str:
    """Base propre au worker pytest-xdist, ou la base telle quelle hors parallèle.

    `tables_temporaires` crée et jette des tables par leur **nom réel**, celui
    que le code sous test emploie : deux workers qui exercent deux paquets
    partageant une table se détruisent mutuellement leurs données. Mesuré sur
    la suite d'intégration sous `-n 4` : entre 7 et 26 échecs sur 135, à chaque
    passage (`TEST-DB-WORKER-ISOLATION-001`).

    Une base par worker rétablit l'isolation que le montage précédent obtenait
    en créant une base jetable par test. La CI n'était pas touchée, elle ne
    parallélise pas les jobs d'intégration : seul le développeur qui lance la
    suite entière avec `-n` voyait des échecs, et pouvait les prendre pour un
    aléa.
    """
    worker = os.environ.get("PYTEST_XDIST_WORKER")
    return f"{base}_{worker}" if worker else base


def _creer_base(nom: str) -> None:
    """Crée la base du worker si elle manque, par la connexion d'administration.

    Le SQL diffère : MariaDB accepte `IF NOT EXISTS`, PostgreSQL non et exige
    de regarder `pg_database`, SQL Server passe par `DB_ID`. `CREATE DATABASE`
    n'accepte de paramètre lié sur aucun des trois, mais le nom vient de
    l'environnement de test et de l'identifiant du worker, jamais d'une entrée
    utilisateur.
    """
    from core.database.backend import get_backend

    backend = get_backend()
    admin: Any = backend.get_admin_connection()
    try:
        try:
            admin.autocommit = True
        except Exception:  # noqa: BLE001 — tous les pilotes ne l'exposent pas
            pass
        cursor = admin.cursor()
        if backend.name == "postgres":
            # `?`, jamais `%s` : la connexion passe par l'enveloppe Forge, qui
            # traduit `?` vers le format du pilote et **double** tout `%`
            # littéral. Écrire `%s` ici le transformerait en `%%s`, un texte,
            # et rendrait « 0 marqueurs pour 1 paramètre ». C'est le défaut
            # même que `VIDEO-DML-PORTABLE-001` venait de corriger ailleurs.
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = ?", (nom,))
            if cursor.fetchone() is None:
                cursor.execute(f'CREATE DATABASE "{nom}"')
        elif backend.name == "mssql":
            cursor.execute(f"IF DB_ID(N'{nom}') IS NULL CREATE DATABASE [{nom}]")
        else:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{nom}`")
        cursor.close()
    finally:
        backend.close_connection(admin)


def _db_params() -> dict[str, object]:
    return {
        "host": os.environ.get("FORGE_TEST_DB_HOST", "127.0.0.1"),
        "port": int(os.environ.get("FORGE_TEST_DB_PORT", "3306")),
        "user": os.environ.get("FORGE_TEST_DB_USER", "root"),
        "password": os.environ.get("FORGE_TEST_DB_PASSWORD", ""),
        "name": _nom_par_worker(os.environ.get("FORGE_TEST_DB_NAME", "forge_test")),
    }


@pytest.fixture(scope="session")
def real_db() -> Iterator[None]:
    """Configure Forge sur la MariaDB de test et crée le pool UNE seule fois.

    Le connecteur mariadb tient un registre de pools nommés : recréer un pool de
    même nom lève « Pool already exists ». La fixture est donc à portée session :
    le pool est créé au premier test `db`, réutilisé par les suivants, puis fermé
    proprement en fin de session.
    """
    import core.forge as forge
    from core.database import connection
    from core.database.backend import reset_backend

    params = _db_params()
    # ADR-060 : le backend lit la config de connexion runtime dans l'environnement.
    #
    # Ces clés doivent être RESTAURÉES en fin de session. `monkeypatch` est à
    # portée fonction et ne convient pas ici (la fixture est à portée session
    # pour le pool nommé), d'où la sauvegarde manuelle. Sans elle, `DB_APP_LOGIN`
    # restait à `root` pour tous les tests suivants du même processus : le
    # contrôle de sécurité prod y voyait à juste titre l'application tournant
    # sous le compte d'administration, et échouait. Le défaut ne se voyait ni en
    # CI, qui sépare les jobs `db` et `not db`, ni en local sans base ; mais
    # `tools/release-validate.sh` lance la suite ENTIÈRE, donc le garde de
    # release pouvait échouer pour une raison étrangère à la release.
    overrides = {
        "DB_HOST": str(params["host"]),
        "DB_PORT": str(params["port"]),
        "DB_APP_LOGIN": str(params["user"]),
        "DB_APP_PWD": str(params["password"]),
        "DB_NAME": str(params["name"]),
        "DB_POOL_SIZE": "2",
        # Identifiants d'administration (ADR-033), nécessaires pour créer la
        # base du worker. Ce sont les mêmes qu'en test.
        "DB_ADMIN_LOGIN": str(params["user"]),
        "DB_ADMIN_PWD": str(params["password"]),
    }
    previous = {key: os.environ.get(key) for key in overrides}
    os.environ.update(overrides)
    forge.configure(app_name="forge_test")

    def _restore() -> None:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    try:
        _creer_base(str(params["name"]))
        probe = connection.get_connection()  # crée le pool nommé une fois
        connection.close_connection(probe)
    except Exception as error:  # noqa: BLE001 — la cause est classée, pas supposée
        _restore()
        message = connection_failure_message("MariaDB", error, env_prefix="FORGE_TEST_DB")
        if _REQUIRE_DB:
            pytest.fail(message + " (FORGE_REQUIRE_DB=1)")
        pytest.skip(message + " (test d'intégration sauté en local)")

    try:
        yield
    finally:
        # ADR-054 : le pool vit dans le backend actif. reset_backend() le ferme
        # proprement (close()) et force une nouvelle résolution ensuite.
        reset_backend()
        _restore()


@pytest.fixture()
def real_pg_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Configure Forge sur le PostgreSQL de test (backend actif : postgres).

    Portée fonction : psycopg n'utilise pas de pool nommé, et la fixture doit
    rendre le backend de la session (reset_backend + env restauré par
    monkeypatch) en sortant. Paramètres lus dans FORGE_TEST_PG_*, avec des
    valeurs par défaut adaptées au service PostgreSQL de la CI.
    """
    pytest.importorskip("psycopg", reason="psycopg (backend forge-mvc-postgres) absent")
    import core.forge as forge
    from core.database import connection
    from core.database.backend import reset_backend

    monkeypatch.setenv("DB_BACKEND", "postgres")
    monkeypatch.setenv("DB_HOST", os.environ.get("FORGE_TEST_PG_HOST", "127.0.0.1"))
    monkeypatch.setenv("DB_PORT", os.environ.get("FORGE_TEST_PG_PORT", "5432"))
    monkeypatch.setenv("DB_APP_LOGIN", os.environ.get("FORGE_TEST_PG_USER", "postgres"))
    monkeypatch.setenv("DB_APP_PWD", os.environ.get("FORGE_TEST_PG_PASSWORD", "forge_test_pg"))
    monkeypatch.setenv("DB_ADMIN_LOGIN", os.environ.get("FORGE_TEST_PG_USER", "postgres"))
    monkeypatch.setenv("DB_ADMIN_PWD", os.environ.get("FORGE_TEST_PG_PASSWORD", "forge_test_pg"))
    nom = _nom_par_worker(os.environ.get("FORGE_TEST_PG_NAME", "forge_test"))
    monkeypatch.setenv("DB_NAME", nom)
    forge.configure(app_name="forge_test")
    reset_backend()
    try:
        _creer_base(nom)
        probe = connection.get_connection()
        connection.close_connection(probe)
    except Exception as error:  # noqa: BLE001 — la cause est classée, pas supposée
        reset_backend()
        message = connection_failure_message("PostgreSQL", error, env_prefix="FORGE_TEST_PG")
        if _REQUIRE_DB_PG:
            pytest.fail(message + " (FORGE_REQUIRE_DB_PG=1)")
        pytest.skip(message + " (test d'intégration sauté en local)")

    yield

    reset_backend()


@pytest.fixture()
def real_mssql_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Configure Forge sur le SQL Server de test (backend actif : mssql).

    Le conteneur SQL Server ne crée aucune base au démarrage : la fixture crée
    la base de test au besoin via la connexion d'administration (master), hors
    transaction. Paramètres lus dans FORGE_TEST_MSSQL_*, avec des valeurs par
    défaut adaptées au service SQL Server de la CI.
    """
    pytest.importorskip("pyodbc", reason="pyodbc (backend forge-mvc-mssql) absent")
    import core.forge as forge
    from core.database import connection
    from core.database.backend import get_backend, reset_backend

    user = os.environ.get("FORGE_TEST_MSSQL_USER", "sa")
    password = os.environ.get("FORGE_TEST_MSSQL_PASSWORD", "Forge#Test#2026")
    db_name = _nom_par_worker(os.environ.get("FORGE_TEST_MSSQL_NAME", "forge_test"))
    monkeypatch.setenv("DB_BACKEND", "mssql")
    monkeypatch.setenv("DB_HOST", os.environ.get("FORGE_TEST_MSSQL_HOST", "127.0.0.1"))
    monkeypatch.setenv("DB_PORT", os.environ.get("FORGE_TEST_MSSQL_PORT", "1433"))
    monkeypatch.setenv("DB_APP_LOGIN", user)
    monkeypatch.setenv("DB_APP_PWD", password)
    monkeypatch.setenv("DB_ADMIN_LOGIN", user)
    monkeypatch.setenv("DB_ADMIN_PWD", password)
    monkeypatch.setenv("DB_NAME", db_name)
    forge.configure(app_name="forge_test")
    reset_backend()
    try:
        backend = get_backend()
        admin: Any = backend.get_admin_connection()  # base de maintenance master
        try:
            admin.autocommit = True
            cursor = admin.cursor()
            # db_name vient de l'environnement de test, jamais d'une entrée
            # utilisateur (CREATE DATABASE n'accepte pas de paramètre lié).
            cursor.execute(f"IF DB_ID(N'{db_name}') IS NULL CREATE DATABASE [{db_name}]")
            cursor.close()
        finally:
            backend.close_connection(admin)
        probe = connection.get_connection()
        connection.close_connection(probe)
    except Exception as error:  # noqa: BLE001 — la cause est classée, pas supposée
        reset_backend()
        message = connection_failure_message("SQL Server", error, env_prefix="FORGE_TEST_MSSQL")
        if _REQUIRE_DB_MSSQL:
            pytest.fail(message + " (FORGE_REQUIRE_DB_MSSQL=1)")
        pytest.skip(message + " (test d'intégration sauté en local)")

    yield

    reset_backend()


def _jeter(db: Any, noms: Sequence[str], backend_name: str) -> None:
    """Supprime les tables, y compris avant création : une exécution tuée en laisse."""
    for nom in noms:
        if backend_name == "mssql":
            # T-SQL n'a pas de `DROP TABLE IF EXISTS` avant SQL Server 2016, et
            # la forme conditionnelle reste la seule portable sur les images en
            # service dans la CI.
            db.execute(f"IF OBJECT_ID('{nom}') IS NOT NULL DROP TABLE {nom}")
        else:
            db.execute(f"DROP TABLE IF EXISTS {nom}")


@contextlib.contextmanager
def tables_temporaires(*definitions: Any) -> Iterator[Any]:
    """Crée les tables données par leur DDL dialectale, rend `core.database.db`, puis les jette.

    Les `definitions` sont des `TableDefinition` du socle
    `core.database.table_ddl` : la DDL est rendue par le dialecte du backend
    actif, donc ce geste vaut pour les quatre backends sans une ligne de SQL
    écrite à la main.

    Le module rendu est **la vraie couche d'accès**. C'est le point de tout :
    un test qui écrit son propre adaptateur de connexion court-circuite la
    traduction des marqueurs de paramètre et la qualification d'erreur, et
    reste vert sur du code qui ne l'est pas.

    À utiliser derrière `real_db` ou `real_backend_db`, qui configurent le
    backend. Sans backend configuré, l'appel échoue à la première requête.
    """
    from core.database import db
    from core.database.backend import get_backend
    from core.database.table_ddl import render_create_table

    backend = get_backend()
    noms = [definition.name for definition in definitions]
    _jeter(db, noms, backend.name)
    for definition in definitions:
        for sql in render_create_table(definition, backend.dialect):
            db.execute(sql)
    try:
        yield db
    finally:
        _jeter(db, noms, backend.name)


@pytest.fixture(
    params=[
        pytest.param("mariadb", marks=pytest.mark.db),
        pytest.param("postgres", marks=[pytest.mark.db, pytest.mark.db_pg]),
        pytest.param("mssql", marks=[pytest.mark.db, pytest.mark.db_mssql]),
    ]
)
def real_backend_db(request: pytest.FixtureRequest) -> str:
    """Monte Forge sur chacun des trois serveurs, et retourne le nom du backend.

    Un test qui demande cette fixture est exécuté trois fois, une par serveur.
    Chaque cas porte les marqueurs de son backend, donc les trois jobs de CI
    sélectionnent chacun le sien sans qu'aucun test soit écrit en triple.

    Le nom retourné sert à ce qu'un test peut avoir besoin d'exprimer par
    backend, un nettoyage par exemple. Il ne doit **pas** servir à contourner
    une différence de comportement : c'est précisément ce que ces tests
    cherchent à révéler.
    """
    request.getfixturevalue(_FIXTURE_PAR_BACKEND[str(request.param)])
    return str(request.param)
