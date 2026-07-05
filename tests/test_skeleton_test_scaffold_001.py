"""SKELETON-STANDARDS-CONFORMANCE-001 / T2 (ADR-063) — socle de test du squelette.

`forge new` livre par défaut de quoi tester le projet dès la première minute :
`pytest.ini` (marqueurs stricts), `tests/conftest.py` (constante partagée
`PROJECT_ROOT`), un smoke test qui prouve que l'application se charge, et
`requirements-dev.txt` épinglant `forge-mvc-testing` (ADR-041).

Le smoke test du squelette importe `mvc.routes`, qui n'existe que dans un projet
généré : il ne doit donc jamais être collecté par la suite de Forge elle-même
(testpaths = « tests packages »).
"""
from __future__ import annotations

from pathlib import Path

SKELETON = Path(__file__).parent.parent / "cli" / "skeleton" / "data"


# ── pytest.ini : marqueurs stricts et déclarés ───────────────────────────────

def test_squelette_livre_pytest_ini():
    ini = SKELETON / "pytest.ini"
    assert ini.is_file(), "cli/skeleton/data/pytest.ini attendu (ADR-063)"
    content = ini.read_text(encoding="utf-8")
    assert "--strict-markers" in content
    assert "testpaths = tests" in content
    for marker in ("meta:", "smoke:", "db:"):
        assert marker in content, f"marqueur {marker} manquant dans pytest.ini"


# ── conftest partagé ─────────────────────────────────────────────────────────

def test_conftest_expose_project_root():
    conftest = SKELETON / "tests" / "conftest.py"
    assert conftest.is_file()
    assert "PROJECT_ROOT" in conftest.read_text(encoding="utf-8")


# ── Smoke test livré ─────────────────────────────────────────────────────────

def test_smoke_livre_et_marque():
    smoke = SKELETON / "tests" / "test_smoke_001.py"
    assert smoke.is_file(), "un smoke test doit être livré (ADR-063)"
    content = smoke.read_text(encoding="utf-8")
    assert "from mvc.routes import router" in content
    assert "@pytest.mark.smoke" in content


# ── requirements-dev.txt : outillage qualité épinglé ─────────────────────────

def test_requirements_dev_livre_outillage():
    reqs = SKELETON / "requirements-dev.txt"
    assert reqs.is_file(), "cli/skeleton/data/requirements-dev.txt attendu (ADR-063)"
    content = reqs.read_text(encoding="utf-8")
    assert "forge-mvc-testing==" in content, "forge-mvc-testing doit être épinglé (ADR-041)"
    for tool in ("pytest", "ruff", "pyright"):
        assert tool in content, f"{tool} attendu dans requirements-dev.txt"
