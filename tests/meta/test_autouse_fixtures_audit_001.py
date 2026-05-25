"""Garde-fou TESTS-AUTOUSE-FIXTURES-AUDIT-001.

Verrouille l'audit des fixtures ``pytest`` ``autouse=True`` du dépôt :

  * le rapport d'audit B10 existe et porte les sections attendues ;
  * **aucune** fixture ``autouse=True`` n'écrit directement dans
    ``os.environ[KEY] = VALUE`` (doit utiliser ``monkeypatch.setenv``) ;
  * **aucune** fixture ``autouse=True`` ne modifie ``sys.path`` ou
    n'utilise ``os.chdir`` ;
  * **aucune** fixture ``autouse=True`` ne déclare de variable globale
    (mot-clé ``global``) ;
  * chaque fixture ``autouse=True`` respecte au moins une convention
    sûre : ``yield``, ``monkeypatch``/``tmp_path``, ou setup local
    purement instanciel (``self.*``).

Le but n'est PAS d'interdire ``autouse=True`` — c'est un outil
légitime — mais d'empêcher qu'une nouvelle fixture introduise un risque
de contamination d'état global non documenté.

Source de vérité : ``docs/history/audits/audit-autouse-fixtures-b10.md``.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TESTS_DIR = _REPO_ROOT / "tests"
_AUDIT_REPORT = (
    _REPO_ROOT / "docs" / "history" / "audits"
    / "audit-autouse-fixtures-b10.md"
)


# ---------------------------------------------------------------------------
# Collecte AST des fixtures autouse=True
# ---------------------------------------------------------------------------


def _iter_test_files():
    for p in sorted(_TESTS_DIR.rglob("*.py")):
        if "__pycache__" in p.parts or ".pytest_cache" in p.parts:
            continue
        yield p


def _is_autouse_fixture(decorator: ast.expr) -> bool:
    """True si le décorateur est ``pytest.fixture(... autouse=True ...)``."""
    if not isinstance(decorator, ast.Call):
        return False
    func = decorator.func
    name = None
    if isinstance(func, ast.Attribute) and func.attr == "fixture":
        name = "fixture"
    elif isinstance(func, ast.Name) and func.id == "fixture":
        name = "fixture"
    if not name:
        return False
    for kw in decorator.keywords:
        if (
            kw.arg == "autouse"
            and isinstance(kw.value, ast.Constant)
            and kw.value.value is True
        ):
            return True
    return False


def _collect_autouse_fixtures() -> list[dict]:
    """Retourne la liste exhaustive des fixtures autouse=True."""
    out: list[dict] = []
    for path in _iter_test_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not any(_is_autouse_fixture(d) for d in node.decorator_list):
                continue
            body_src = ast.unparse(node)
            arg_names = {a.arg for a in node.args.args}
            out.append({
                "path": path,
                "lineno": node.lineno,
                "name": node.name,
                "body_src": body_src,
                "arg_names": arg_names,
            })
    return out


_AUTOUSE_FIXTURES = _collect_autouse_fixtures()


# ---------------------------------------------------------------------------
# Tests — existence et structure du rapport
# ---------------------------------------------------------------------------


class TestAuditReportExists:
    def test_report_file_present(self):
        assert _AUDIT_REPORT.is_file(), (
            f"Le rapport d'audit doit exister à "
            f"{_AUDIT_REPORT.relative_to(_REPO_ROOT)}."
        )

    @pytest.mark.parametrize("heading", [
        "# Audit fixtures autouse — B10",
        "## Résumé",
        "## Méthode",
        "## Nombre de fixtures autouse trouvées",
        "## Classement",
        "## Décision",
    ])
    def test_report_has_section(self, heading):
        text = _AUDIT_REPORT.read_text(encoding="utf-8")
        assert heading in text, (
            f"Le rapport d'audit doit contenir la section `{heading}`."
        )

    def test_report_states_b10_decision(self):
        text = _AUDIT_REPORT.read_text(encoding="utf-8")
        assert "GO B10" in text or "NO-GO B10" in text, (
            "Le rapport doit énoncer explicitement la décision : GO B10 ou NO-GO B10."
        )


# ---------------------------------------------------------------------------
# Tests — sanity de l'audit (nombre minimal de fixtures)
# ---------------------------------------------------------------------------


class TestAuditCoverage:
    def test_finds_significant_number_of_autouse_fixtures(self):
        assert len(_AUTOUSE_FIXTURES) >= 30, (
            f"L'audit AST trouve {len(_AUTOUSE_FIXTURES)} fixtures "
            "autouse=True — couverture suspecte si très faible."
        )


# ---------------------------------------------------------------------------
# Tests — interdictions hard
# ---------------------------------------------------------------------------


def _ids(fixtures):
    return [
        f"{f['path'].relative_to(_REPO_ROOT)}::{f['name']}"
        for f in fixtures
    ]


class TestNoDirectEnvironWrites:
    """Aucune fixture autouse ne doit écrire ``os.environ[KEY] = VALUE``
    en direct — utiliser ``monkeypatch.setenv`` à la place pour bénéficier
    du teardown automatique."""

    @pytest.mark.parametrize(
        "fixture", _AUTOUSE_FIXTURES, ids=_ids(_AUTOUSE_FIXTURES),
    )
    def test_no_direct_environ_assignment(self, fixture):
        # On cherche `os.environ[...] = ` — l'assignation directe.
        # `os.environ.get(...)` (lecture) reste autorisé.
        body = fixture["body_src"]
        # Pattern simple ; on filtre les faux positifs comme
        # `os.environ.pop(...)` qui sont OK (n'écrivent pas).
        assert "os.environ[" not in body or "os.environ[\"" not in body or "monkeypatch" in body, (
            f"`{fixture['name']}` ({fixture['path'].relative_to(_REPO_ROOT)}) "
            "écrit directement dans `os.environ[...]`. Utiliser "
            "`monkeypatch.setenv(...)` pour bénéficier du teardown automatique."
        )
        # Check plus strict : assignation directe via `os.environ[X] = Y`
        lines = body.splitlines()
        for line in lines:
            stripped = line.strip()
            if (
                stripped.startswith("os.environ[")
                and "=" in stripped
                and ".pop" not in stripped
                and ".get" not in stripped
                and "==" not in stripped
                and "!=" not in stripped
            ):
                if "monkeypatch" not in body:
                    pytest.fail(
                        f"`{fixture['name']}` ({fixture['path'].relative_to(_REPO_ROOT)}) "
                        f"écrit directement : `{stripped}`. Utiliser "
                        "`monkeypatch.setenv(...)` à la place."
                    )


class TestNoSysPathManipulation:
    """Aucune fixture autouse ne doit modifier ``sys.path``."""

    @pytest.mark.parametrize(
        "fixture", _AUTOUSE_FIXTURES, ids=_ids(_AUTOUSE_FIXTURES),
    )
    def test_no_sys_path(self, fixture):
        body = fixture["body_src"]
        assert "sys.path" not in body, (
            f"`{fixture['name']}` ({fixture['path'].relative_to(_REPO_ROOT)}) "
            "manipule `sys.path` — interdit dans une fixture autouse "
            "(à faire dans un conftest racine si nécessaire)."
        )


class TestNoChdir:
    """Aucune fixture autouse ne doit utiliser ``os.chdir``."""

    @pytest.mark.parametrize(
        "fixture", _AUTOUSE_FIXTURES, ids=_ids(_AUTOUSE_FIXTURES),
    )
    def test_no_chdir(self, fixture):
        body = fixture["body_src"]
        assert "chdir" not in body, (
            f"`{fixture['name']}` ({fixture['path'].relative_to(_REPO_ROOT)}) "
            "utilise `chdir` — change le working directory de tout le "
            "processus pytest. Préférer un chemin absolu calculé via tmp_path."
        )


class TestNoGlobalKeyword:
    """Aucune fixture autouse ne doit déclarer une variable globale."""

    @pytest.mark.parametrize(
        "fixture", _AUTOUSE_FIXTURES, ids=_ids(_AUTOUSE_FIXTURES),
    )
    def test_no_global_keyword(self, fixture):
        body = fixture["body_src"]
        for line in body.splitlines():
            stripped = line.strip()
            if stripped.startswith("global "):
                pytest.fail(
                    f"`{fixture['name']}` ({fixture['path'].relative_to(_REPO_ROOT)}) "
                    f"déclare `{stripped}` — interdit (pollue l'état global)."
                )


# ---------------------------------------------------------------------------
# Tests — chaque fixture respecte au moins une convention de sécurité
# ---------------------------------------------------------------------------


def _looks_local_setup(body_src: str, name: str) -> bool:
    """Heuristique : la fixture ne modifie que des attributs `self.*` ou
    des variables locales, sans toucher de symbole global identifiable.

    Conservatrice : la présence de `self.` suffit pour considérer le
    setup comme local (le pattern le plus fréquent dans les tests Forge).
    """
    return "self." in body_src or "Path(" in body_src or "tmp_path" in body_src


class TestEverySafetyConventionRespected:
    """Chaque fixture autouse doit respecter au moins une convention :

      * possède un ``yield`` (teardown explicite) ;
      * utilise ``monkeypatch`` (restauration automatique pytest) ;
      * utilise ``tmp_path`` / ``tmp_path_factory`` (sandbox) ;
      * setup purement local (attributs ``self.*``, ``Path(...)`` local).

    Le test évite d'imposer un dogme : il accepte largement, mais signale
    les fixtures qui ne rentrent dans AUCUNE de ces catégories — c'est le
    signal d'un risque potentiel à investiguer.
    """

    @pytest.mark.parametrize(
        "fixture", _AUTOUSE_FIXTURES, ids=_ids(_AUTOUSE_FIXTURES),
    )
    def test_respects_a_safety_convention(self, fixture):
        body = fixture["body_src"]
        args = fixture["arg_names"]
        has_yield = "yield" in body
        uses_monkeypatch = "monkeypatch" in args
        uses_tmp_path = bool(args & {"tmp_path", "tmp_path_factory"})
        looks_local = _looks_local_setup(body, fixture["name"])
        assert has_yield or uses_monkeypatch or uses_tmp_path or looks_local, (
            f"`{fixture['name']}` ({fixture['path'].relative_to(_REPO_ROOT)}) "
            "ne respecte aucune convention de sécurité pour une fixture "
            "autouse :\n"
            "  - pas de yield (donc pas de teardown explicite) ;\n"
            "  - pas de monkeypatch ;\n"
            "  - pas de tmp_path / tmp_path_factory ;\n"
            "  - pas de setup local visible (`self.*`, `Path(...)`).\n"
            "Soit ajouter `yield` + restauration, soit migrer vers "
            "`monkeypatch`, soit limiter le setup à l'instance de test, "
            "soit documenter dans le rapport d'audit B10."
        )
