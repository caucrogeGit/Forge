"""Garde-fou — CORE-AUTH-SECURITY-LAYERING-001 : pas de cycle auth↔security.

`core.security` importe `core.auth` au niveau module. Avant, `core.auth.session`
lisait la session via `core.security.session` par un import différé, créant un
cycle conceptuel qui ne tenait que par ces imports différés, non gardés par un
test (audit M2). La lecture de session est descendue dans `core.sessions.access`
(couche basse). Ce garde interdit le retour du cycle : `core.auth` ne doit
importer `core.security` ni au niveau module ni dans une fonction, et
`core.sessions` reste la couche basse (ni security ni auth).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent


def _imported_modules(path: Path) -> set[str]:
    """Tous les modules importés (niveau module ET dans les fonctions)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
    return modules


def _py_files(package: str) -> list[Path]:
    base = PROJECT_ROOT / "core" / package
    return [p for p in base.rglob("*.py") if "__pycache__" not in p.parts]


def test_core_auth_n_importe_pas_core_security():
    offenders: list[str] = []
    for path in _py_files("auth"):
        for module in _imported_modules(path):
            if module == "core.security" or module.startswith("core.security."):
                offenders.append(f"{path.relative_to(PROJECT_ROOT)} -> {module}")
    assert not offenders, (
        "core.auth ne doit importer core.security (le cycle est cassé via "
        f"core.sessions.access, CORE-AUTH-SECURITY-LAYERING-001) : {offenders}"
    )


def test_core_sessions_reste_couche_basse():
    offenders: list[str] = []
    for path in _py_files("sessions"):
        for module in _imported_modules(path):
            if module.startswith(("core.security", "core.auth")):
                offenders.append(f"{path.relative_to(PROJECT_ROOT)} -> {module}")
    assert not offenders, (
        "core.sessions est la couche basse : il ne doit dépendre ni de "
        f"core.security ni de core.auth : {offenders}"
    )


def test_facade_core_security_session_reexporte():
    # Le chemin d'import public reste inchangé pour les consommateurs (dont le
    # code généré) : core.security.session expose toujours ces symboles.
    from core.security import session as sec_session
    from core.sessions import access

    assert sec_session.get_session_id is access.get_session_id
    assert sec_session.get_session is access.get_session
    assert sec_session.SESSION_COOKIE_NAME == access.SESSION_COOKIE_NAME
