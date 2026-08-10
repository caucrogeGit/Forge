import os
import sys
from pathlib import Path

_packages_dir = Path(__file__).parent / "packages"
for _pkg in sorted(_packages_dir.iterdir()):
    if _pkg.is_dir():
        sys.path.insert(0, str(_pkg))


# ── Backend BDD déterministe en test (ADR-054) ───────────────────────────────
# Le monorepo installe PLUSIEURS backends BDD en éditable (forge-mvc-mariadb,
# forge-mvc-sqlite). En usage réel un projet n'en installe qu'un ; ici le
# résolveur verrait deux entry points et appliquerait l'exclusivité mutuelle.
# On fixe donc le backend par défaut sur mariadb (cible des tests d'intégration
# tests/db). Les tests spécifiques à un autre backend posent DB_BACKEND eux-mêmes
# (monkeypatch) puis appellent reset_backend().
os.environ.setdefault("DB_BACKEND", "mariadb")


# ── Garde de collecte des tests `db` (TEST-DB-COLLECT-GUARD-001) ──────────────
# En CI, chaque job tests-db lance la suite avec le drapeau FORGE_REQUIRE_DB*
# de SON backend et un serveur réel : les tests de ce backend DOIVENT s'exécuter.
# Un skip (module sauté à l'import, base jugée injoignable, garde de sécurité)
# laisserait le job vert avec 0 test exécuté, masquant une régression
# d'infrastructure. Ce garde transforme tout skip d'un test requis en échec de
# session. En local (variables absentes), il est inerte : les skips restent la
# façon normale de sauter les tests d'intégration sans base.
# Backends (ADR-084) : `db` seul = MariaDB (FORGE_REQUIRE_DB=1) ; `db` combiné
# à `db_pg`/`db_mssql` = requis par FORGE_REQUIRE_DB_PG/FORGE_REQUIRE_DB_MSSQL
# uniquement. La combinaison reste porteuse : c'est elle qui dit à `_db_test_required`
# qu'un cas PostgreSQL n'est pas exigé du job MariaDB.
#
# Le job MariaDB ne les sélectionne plus pour autant (`CI-DB-JOB-SELECTOR-001`).
# Il employait `-m db`, donc les collectait puis les sautait, mais leur fixture
# tentait d'abord une connexion vers un serveur absent : 15 s par cas quand
# l'hôte ne répond pas, 2,5 s quand il refuse. Il emploie désormais
# `-m "db and not db_pg and not db_mssql"`. Aucune couverture n'est perdue, ces
# cas s'exécutant dans le job de leur propre backend.

# ── Garde des paramétrisations vides (TESTS-EMPTY-PARAMETRIZE-GUARD-001) ─────
# Une `@pytest.mark.parametrize` sur une liste vide ne produit pas zéro test :
# pytest en produit UN, marqué `skip`, avec le motif « got empty parameter set ».
# Le test devient donc invisible, alors que c'est souvent là qu'il compte le
# plus : les cliquets de dette de Forge se vident à mesure qu'elle est payée, et
# la liste vide est justement l'état qu'on veut voir tenir.
#
# Trois occurrences ont été trouvées à la main dans ce cycle, dont une que le
# relevé initial avait manquée faute de la bonne sélection. Ce garde les
# attrape toutes, présentes et futures, sans coûter une collecte séparée.


def pytest_collection_modifyitems(config: object, items: list) -> None:  # type: ignore[type-arg]
    vides = [
        item.nodeid
        for item in items
        for mark in item.iter_markers(name="skip")
        if "got empty parameter set" in str(mark.kwargs.get("reason", ""))
    ]
    if not vides:
        return
    import pytest

    pytest.exit(
        "Paramétrisation vide, donc test invisible "
        "(TESTS-EMPTY-PARAMETRIZE-GUARD-001) : écrivez une boucle dans le corps "
        "du test plutôt qu'un `parametrize` sur une liste qui peut se vider.\n  "
        + "\n  ".join(sorted(vides)),
        returncode=1,
    )


_REQUIRE_DB = os.environ.get("FORGE_REQUIRE_DB") == "1"
_REQUIRE_DB_PG = os.environ.get("FORGE_REQUIRE_DB_PG") == "1"
_REQUIRE_DB_MSSQL = os.environ.get("FORGE_REQUIRE_DB_MSSQL") == "1"
_skipped_db_tests: list[str] = []


def _db_test_required(keywords: object) -> bool:
    if "db_pg" in keywords:  # type: ignore[operator]
        return _REQUIRE_DB_PG
    if "db_mssql" in keywords:  # type: ignore[operator]
        return _REQUIRE_DB_MSSQL
    return _REQUIRE_DB


def pytest_runtest_logreport(report: object) -> None:
    keywords = getattr(report, "keywords", {})
    if "db" not in keywords:
        return
    if not _db_test_required(keywords):
        return
    if getattr(report, "skipped", False):
        _skipped_db_tests.append(getattr(report, "nodeid", "<inconnu>"))


def pytest_sessionfinish(session: object, exitstatus: object) -> None:
    if not _skipped_db_tests:
        return
    import pytest

    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    unique = sorted(set(_skipped_db_tests))
    message = (
        "FORGE_REQUIRE_DB* posé mais "
        f"{len(unique)} test(s) `db` requis ont été sautés (attendu : tous exécutés) :\n  "
        + "\n  ".join(unique)
    )
    if reporter is not None:
        reporter.write_line(message, red=True)
    session.exitstatus = pytest.ExitCode.TESTS_FAILED
