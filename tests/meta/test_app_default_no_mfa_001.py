"""APP-DEFAULT-NO-MFA-001 : forge_mvc_mfa est optionnel dans mvc/."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent


def _top_level_imports(path: Path) -> list[str]:
    """Retourne les noms des modules importés au niveau module (hors try/except)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    return imports


class TestNoTopLevelMfaImport:
    """Aucun import forge_mvc_mfa au niveau module (hors try/except)."""

    @pytest.mark.parametrize("rel_path", [
        "mvc/controllers/auth_controller.py",
        "mvc/controllers/mfa_challenge_controller.py",
        "mvc/routes.py",
    ])
    def test_no_top_level_mfa_import(self, rel_path):
        path = PROJECT_ROOT / rel_path
        top = _top_level_imports(path)
        assert not any("forge_mvc_mfa" in m for m in top), (
            f"{rel_path} a un import forge_mvc_mfa au niveau module : {top}"
        )


class TestMfaAvailableExported:
    """auth_controller exporte mfa_available()."""

    def test_mfa_available_function_present(self):
        content = (PROJECT_ROOT / "mvc/controllers/auth_controller.py").read_text(encoding="utf-8")
        assert "def mfa_available" in content

    def test_neutral_routes_has_no_mfa_reference(self):
        """Le squelette neutre ne référence plus MFA (SKELETON-ROUTES-NEUTRAL-001).

        Le câblage /login/mfa est relocalisé dans le starter welcome-optin-mfa ;
        `mvc/routes.py` livré par défaut n'a aucune trace de MFA (§3, §8).
        """
        content = (PROJECT_ROOT / "mvc/routes.py").read_text(encoding="utf-8")
        assert "mfa" not in content.lower(), (
            "Le squelette neutre ne doit plus référencer MFA : "
            "le câblage vit dans welcome-optin-mfa/routes.py.snippet."
        )

    # test_mfa_wiring_lives_in_welcome_optin_mfa_snippet retiré : il lisait le
    # snippet du starter supprimé `welcome-optin-mfa`.


class TestMfaGuardInControllers:
    """Les contrôleurs ont les gardes _MFA_AVAILABLE."""

    def test_auth_controller_has_mfa_available_flag(self):
        content = (PROJECT_ROOT / "mvc/controllers/auth_controller.py").read_text(encoding="utf-8")
        assert "_MFA_AVAILABLE" in content

    def test_mfa_challenge_controller_has_guard(self):
        content = (PROJECT_ROOT / "mvc/controllers/mfa_challenge_controller.py").read_text(encoding="utf-8")
        assert "_MFA_AVAILABLE" in content
        assert "_mfa_unavailable_redirect" in content

    # test_mfa_routes_conditional_in_snippet retiré : il lisait le snippet du
    # starter supprimé `welcome-optin-mfa`.


class TestConftestMfaImportProtected:
    """tests/conftest.py ne doit pas importer forge_mvc_mfa sans try/except.

    Garde-fou TESTS-CONFTEST-NO-MFA-001 : sans cette protection, `pytest` plante
    au boot si forge-mvc-mfa n'est pas installé, même pour des tests qui n'ont
    rien à voir avec MFA.
    """

    def test_conftest_mfa_import_is_protected(self):
        """L'import forge_mvc_mfa dans conftest.py est dans un try/except ImportError."""
        source = (PROJECT_ROOT / "packages/forge-mvc-testing/forge_mvc_testing/plugin.py").read_text(encoding="utf-8")
        lines = source.splitlines()

        mfa_import_lines = []
        for lineno, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            if (stripped.startswith("from forge_mvc_mfa")
                    or stripped.startswith("import forge_mvc_mfa")):
                mfa_import_lines.append((lineno, line))

        assert mfa_import_lines, (
            "conftest.py n'importe plus forge_mvc_mfa — ce test devient inutile, "
            "retirer le garde-fou ou ajuster."
        )

        for lineno, line in mfa_import_lines:
            indent = len(line) - len(line.lstrip())
            assert indent > 0, (
                f"conftest.py:{lineno} importe forge_mvc_mfa au top-level : {line!r}"
            )

            found_try = False
            for back in range(max(0, lineno - 6), lineno - 1):
                prev = lines[back]
                prev_stripped = prev.lstrip()
                prev_indent = len(prev) - len(prev_stripped)
                if prev_stripped.startswith("try:") and prev_indent < indent:
                    found_try = True
                    break
            assert found_try, (
                f"conftest.py:{lineno} importe forge_mvc_mfa sans `try:` au-dessus : {line!r}"
            )

    def test_conftest_uses_explicit_noop_fallback(self):
        """Le fallback définit une fonction `_purge_replay` qui retourne None."""
        source = (PROJECT_ROOT / "packages/forge-mvc-testing/forge_mvc_testing/plugin.py").read_text(encoding="utf-8")
        assert "except ImportError" in source, (
            "conftest.py doit utiliser `except ImportError` pour protéger l'import MFA"
        )
        assert "def _purge_replay" in source, (
            "conftest.py doit définir un fallback `def _purge_replay()` en cas d'ImportError"
        )


class TestRequirementsAreCorePure:
    """requirements.txt et pyproject.toml racine ne contiennent que les dépendances du core minimal.

    Garde-fou REQUIREMENTS-CORE-PURE-001 : `pyotp` est une dépendance MFA-only.
    Sa présence dans le core trahit un couplage : un utilisateur qui installe
    `forge-mvc` sans extras tirerait quand même pyotp. Cela viole le principe 8
    (« Noyau minimal, briques opt-in »).
    """

    CORE_REQUIREMENTS_PATH = PROJECT_ROOT / "requirements.txt"
    CORE_PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
    MFA_PYPROJECT_PATH = PROJECT_ROOT / "packages/forge-mvc-mfa/pyproject.toml"

    # CORE-DROP-PILLOW-001 (ADR-018) : Pillow a quitté le core (opt-in
    # forge-mvc-images) ; il ne fait plus partie des dépendances core attendues.
    EXPECTED_CORE = {
        "mariadb",
        "python-dotenv",
        "jinja2",
        "argon2-cffi",
    }
    MODULE_ONLY = {
        "pyotp",
    }

    @staticmethod
    def _parse_requirements(path: Path) -> set[str]:
        if not path.exists():
            return set()
        names: set[str] = set()
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            for sep in ("==", ">=", "<=", "~=", "<", ">"):
                if sep in line:
                    line = line.split(sep)[0]
                    break
            names.add(line.strip())
        return names

    @staticmethod
    def _parse_pyproject_core_deps(path: Path) -> set[str]:
        import tomllib
        if not path.exists():
            return set()
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        raw = data.get("project", {}).get("dependencies", [])
        names: set[str] = set()
        for entry in raw:
            for sep in ("==", ">=", "<=", "~=", "<", ">"):
                if sep in entry:
                    entry = entry.split(sep)[0]
                    break
            names.add(entry.strip())
        return names

    def test_requirements_txt_contains_no_module_only_deps(self):
        listed = self._parse_requirements(self.CORE_REQUIREMENTS_PATH)
        forbidden = listed & self.MODULE_ONLY
        assert not forbidden, (
            f"requirements.txt contient des dépendances opt-in : {forbidden}"
        )

    def test_requirements_txt_contains_expected_core(self):
        listed = self._parse_requirements(self.CORE_REQUIREMENTS_PATH)
        missing = self.EXPECTED_CORE - listed
        assert not missing, (
            f"requirements.txt manque des dépendances core : {missing}"
        )

    def test_pyproject_root_contains_no_module_only_deps(self):
        listed = self._parse_pyproject_core_deps(self.CORE_PYPROJECT_PATH)
        forbidden = listed & self.MODULE_ONLY
        assert not forbidden, (
            f"pyproject.toml racine déclare des dépendances opt-in : {forbidden}"
        )

    def test_mfa_module_declares_pyotp(self):
        assert self.MFA_PYPROJECT_PATH.exists()
        text = self.MFA_PYPROJECT_PATH.read_text(encoding="utf-8")
        assert "pyotp" in text, (
            f"{self.MFA_PYPROJECT_PATH} doit déclarer pyotp dans ses dependencies"
        )


class TestProjectCheckDetectsImportErrors:
    """project:check doit échouer si mvc/routes.py ne s'importe pas.

    Garde-fou PROJECT-CHECK-ROUTES-IMPORT-001 : avant ce ticket, `project:check`
    disait OK pendant que `routes:list` plantait. Le faux positif a induit en
    erreur au moins un audit pré-release (cf. CHANGELOG `PRE-RELEASE-AUDIT-3.0-001`).
    """

    def test_check_project_routes_does_not_only_ast_parse(self):
        """Le code source de check_project_routes appelle importlib, pas seulement ast.parse."""
        source = (PROJECT_ROOT / "cli/project/project_check.py").read_text(encoding="utf-8")
        assert "importlib.import_module" in source, (
            "check_project_routes doit faire un vrai import via importlib.import_module"
        )
        assert "ImportError" in source, (
            "check_project_routes doit gérer ImportError explicitement"
        )

    def test_check_project_routes_handles_missing_router_attr(self):
        """Le check rejette un fichier qui n'expose pas `router`."""
        source = (PROJECT_ROOT / "cli/project/project_check.py").read_text(encoding="utf-8")
        assert 'hasattr(module, "router")' in source or "hasattr(module, 'router')" in source, (
            "check_project_routes doit vérifier que le module expose un attribut router"
        )
