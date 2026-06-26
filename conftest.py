import os
import sys
from pathlib import Path

_packages_dir = Path(__file__).parent / "packages"
for _pkg in sorted(_packages_dir.iterdir()):
    if _pkg.is_dir():
        sys.path.insert(0, str(_pkg))


# ── Garde de collecte des tests `db` (TEST-DB-COLLECT-GUARD-001) ──────────────
# En CI, le job tests-db lance la suite avec FORGE_REQUIRE_DB=1 et une MariaDB
# réelle : tous les tests marqués `db` DOIVENT s'exécuter. Un skip (module sauté
# à l'import, base jugée injoignable, garde de sécurité) laisserait le job vert
# avec 0 test exécuté, masquant une régression d'infrastructure. Ce garde
# transforme tout skip d'un test `db` en échec de session quand FORGE_REQUIRE_DB
# est posé. En local (variable absente), il est inerte : les skips restent la
# façon normale de sauter les tests d'intégration sans base.

_REQUIRE_DB = os.environ.get("FORGE_REQUIRE_DB") == "1"
_skipped_db_tests: list[str] = []


def pytest_runtest_logreport(report: object) -> None:
    if not _REQUIRE_DB:
        return
    keywords = getattr(report, "keywords", {})
    if "db" not in keywords:
        return
    if getattr(report, "skipped", False):
        _skipped_db_tests.append(getattr(report, "nodeid", "<inconnu>"))


def pytest_sessionfinish(session: object, exitstatus: object) -> None:
    if not _REQUIRE_DB or not _skipped_db_tests:
        return
    import pytest

    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    unique = sorted(set(_skipped_db_tests))
    message = (
        "FORGE_REQUIRE_DB=1 mais "
        f"{len(unique)} test(s) `db` ont été sautés (attendu : tous exécutés) :\n  "
        + "\n  ".join(unique)
    )
    if reporter is not None:
        reporter.write_line(message, red=True)
    session.exitstatus = pytest.ExitCode.TESTS_FAILED
