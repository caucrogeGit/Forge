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
    # ADR-032 : UPLOAD_ROOT est lu depuis l'environnement par forge-mvc-files.
    # Filet de sécurité : un défaut de session pointant vers un tmp, pour qu'aucun
    # test ne puisse écrire dans le storage réel du dépôt même sans isolation propre.
    # pytest.MonkeyPatch() (et non os.environ direct) pour bénéficier du teardown.
    mp = pytest.MonkeyPatch()
    mp.setenv("UPLOAD_ROOT", str(tmp_path_factory.mktemp("uploads")))
    yield
    mp.undo()


@pytest.fixture(autouse=True)
def clear_sessions():
    """Vide le store de sessions entre chaque test."""
    from core.sessions.manager import get_session_store
    get_session_store().purge_all()
    yield
    get_session_store().purge_all()


@pytest.fixture(autouse=True)
def clear_rate_limits():
    """Vide les compteurs de tentatives, anti-replay et échecs d'audit entre chaque test.

    Contrat dual-environnement :
    - En environnement core-only (forge-mvc seul installé), les modules optionnels
      (forge_mvc_mfa, forge_mvc_rbac, forge_mvc_workflow, forge_mvc_stats) sont absents.
    - Chaque fichier de test qui les importe commence par pytest.importorskip("forge_mvc_xxx")
      pour être automatiquement sauté (SKIPPED) plutôt que de produire une erreur de collecte.
    - Ce fixture reste compatible core-only via try/except ImportError sur forge_mvc_mfa.
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

    FILES-MOVE-PIPELINE-001 (ADR-019) : le rate-limit d'upload vit désormais dans
    forge_mvc_files (paquet opt-in résolu par le conftest racine). On vide le
    compteur du **vrai** module ; absent → no-op (core sans l'opt-in installé).
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
    """Retourne la classe FakeRequest pour construire des requêtes simulées dans les tests."""
    return FakeRequest
