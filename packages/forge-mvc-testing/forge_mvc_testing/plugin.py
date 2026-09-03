"""Plugin pytest de Forge (test-support, ADR-041).

Chargé automatiquement via le point d'entrée `pytest11` dès que
`forge-mvc-testing` est installé dans l'environnement de test. Fournit les
fixtures partagées autrefois dans `tests/conftest.py` : configuration du noyau,
nettoyage entre tests, et `fake_request`.

Réservé au développement : ce paquet n'est jamais une dépendance runtime, donc
ces fixtures (notamment l'autouse `configure_forge_kernel`) n'affectent pas les
suites de tests des utilisateurs de Forge.
"""
from __future__ import annotations

import pytest

import core.forge as forge

from forge_mvc_testing.fake_request import FakeRequest
from forge_mvc_testing.fixtures_support import (  # noqa: F401 — exposée comme fixture
    fixtures_loader,
)

# Fixtures d'intégration serveur réel (TESTING-REAL-DB-FIXTURES-001). Importées
# ici pour que le plugin les expose à toute la suite, y compris aux tests des
# paquets opt-in sous `packages/*/tests/`, qui n'avaient pas accès à celles de
# `tests/db/conftest.py` et réécrivaient donc chacun son adaptateur à la main.
from forge_mvc_testing.real_db import (  # noqa: F401 — exposées comme fixtures
    real_backend_db,
    real_db,
    real_mssql_db,
    real_pg_db,
    real_pg_db_sans_privilege,
)


@pytest.fixture(scope="session", autouse=True)
def configure_forge_kernel(tmp_path_factory):
    """Configure le noyau Forge pour tous les tests — vues et SQL dans tmp_path."""
    views_dir = tmp_path_factory.mktemp("views")
    sql_dir = tmp_path_factory.mktemp("sql")
    # ADR-060 : le cœur ne porte plus de config de connexion BDD ; un backend la
    # lit dans l'environnement. Les tests qui touchent la base posent eux-mêmes
    # les variables DB_* (voir test_sqlite_adapter_001).
    forge.configure(
        app_name="TestForge",
        app_env="dev",
        views_dir=str(views_dir),
        sql_dir=str(sql_dir),
    )
    # ADR-032 : UPLOAD_ROOT est lu depuis l'environnement par forge-mvc-files.
    # Filet de sécurité : un défaut pointant vers un tmp, pour qu'aucun test ne
    # puisse écrire dans le storage réel du dépôt même sans isolation propre.
    mp = pytest.MonkeyPatch()
    mp.setenv("UPLOAD_ROOT", str(tmp_path_factory.mktemp("uploads")))
    yield
    mp.undo()


@pytest.fixture(autouse=True)
def clear_sessions():
    """Vide le store de sessions entre chaque test."""
    from core.sessions.manager import get_session_store

    def _purge() -> None:
        # `purge_all` est une capacité réservée aux tests, portée par
        # MemorySessionStore et hors du protocole SessionStore : on l'appelle
        # uniquement si le store configuré l'expose.
        store = get_session_store()
        purge = getattr(store, "purge_all", None)
        if callable(purge):
            purge()

    _purge()
    yield
    _purge()


@pytest.fixture(autouse=True)
def clear_rate_limits():
    """Vide les compteurs de tentatives, anti-replay et échecs d'audit entre tests.

    Compatible core-only : si `forge_mvc_mfa` n'est pas installé, le purge
    anti-replay devient un no-op.
    """
    from core.auth.rate_limit import purge_all_attempts
    from core.auth.audit import reset_audit_failure_count

    try:
        from forge_mvc_mfa.totp_replay import purge_all as _purge_replay
    except ImportError:
        def _purge_replay():  # type: ignore[misc]
            """No-op : forge-mvc-mfa n'est pas installé."""
            return None

    purge_all_attempts()
    _purge_replay()
    reset_audit_failure_count()
    yield
    purge_all_attempts()
    _purge_replay()
    reset_audit_failure_count()


@pytest.fixture(autouse=True)
def clear_upload_rate_limits():
    """Vide le compteur d'uploads entre chaque test.

    Le rate-limit d'upload vit dans `forge_mvc_files` (ADR-019) ; absent → no-op.
    """
    try:
        from forge_mvc_files import rate_limit as _rl
    except ImportError:
        yield
        return
    _rl._compteurs.clear()
    yield
    _rl._compteurs.clear()


@pytest.fixture
def fake_request():
    """Retourne la classe `FakeRequest` pour construire des requêtes simulées."""
    return FakeRequest


@pytest.fixture
def make_client():
    """Fabrique un `ForgeTestClient` sur une `Application` Forge.

    ```python
    def test_page(make_client):
        client = make_client(application)
        assert client.get("/").status == 200
    ```

    Le client passe par `create_wsgi_app`, c'est à dire par le **vrai** chemin
    de production : un client qui reconstruirait sa propre boucle serait un
    jumeau, et passerait là où la production échoue.

    Les avertissements de production sont coupés : ils appartiennent au
    démarrage d'un vrai service, et pollueraient le journal de chaque test.
    """
    from core.app.wsgi import create_wsgi_app

    from forge_mvc_testing.client import ForgeTestClient

    def _fabrique(application, **kw):
        return ForgeTestClient(
            create_wsgi_app(application, emit_prod_warnings=False), **kw
        )

    return _fabrique
