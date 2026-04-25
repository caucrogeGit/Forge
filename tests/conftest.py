import pytest
import core.forge as forge
from tests.fake_request import FakeRequest


@pytest.fixture(scope="session", autouse=True)
def configure_forge_kernel(tmp_path_factory):
    """Configure le noyau Forge pour tous les tests — vues et SQL dans tmp_path."""
    views_dir = tmp_path_factory.mktemp("views")
    sql_dir   = tmp_path_factory.mktemp("sql")
    forge.configure(
        app_name     = "TestForge",
        app_env      = "dev",
        views_dir    = str(views_dir),
        sql_dir      = str(sql_dir),
        db_host      = "localhost",
        db_port      = 3306,
        db_name      = "test_db",
        db_user      = "root",
        db_password  = "",
        db_pool_size = 1,
    )


@pytest.fixture(autouse=True)
def clear_sessions():
    """Vide le store de sessions entre chaque test."""
    from core.security import session as _s
    _s._sessions.clear()
    yield
    _s._sessions.clear()


@pytest.fixture(autouse=True)
def clear_rate_limits():
    """Vide le compteur de tentatives de connexion entre chaque test."""
    from core.security import hashing as _h
    _h._tentatives.clear()
    yield
    _h._tentatives.clear()


@pytest.fixture
def fake_request():
    """Retourne la classe FakeRequest pour construire des requêtes simulées dans les tests."""
    return FakeRequest
