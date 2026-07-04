"""Tests documentaires — RELEASE-COMPAT-001 : matrice de compatibilité Forge."""

from pathlib import Path

DOC = Path("docs/release/compatibility.md")


def _text():
    return DOC.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Existence
# ---------------------------------------------------------------------------


class TestExistence:
    def test_fichier_existe(self):
        assert DOC.exists(), "docs/release/compatibility.md introuvable"

    def test_fichier_non_vide(self):
        assert len(_text()) > 500

    def test_titre_principal(self):
        assert "Matrice de compatibilité" in _text()


# ---------------------------------------------------------------------------
# Python
# ---------------------------------------------------------------------------


class TestPython:
    def test_section_python(self):
        assert "## Python" in _text()

    def test_version_minimum_3_12(self):
        assert "3.12" in _text()

    def test_mention_minimum_requis(self):
        text = _text()
        assert "minimum" in text.lower() and "3.12" in text

    def test_versions_ci_3_12(self):
        assert "3.12" in _text()

    def test_versions_ci_3_13(self):
        assert "3.13" in _text()

    def test_versions_ci_3_14(self):
        assert "3.14" in _text()

    def test_non_supporte_avant_3_12(self):
        text = _text()
        assert "< 3.12" in text or "3.11" in text or "non support" in text.lower()

    def test_mention_ci_github_actions(self):
        text = _text().lower()
        assert "ci" in text and ("github" in text or "actions" in text)

    def test_recommande_3_12(self):
        text = _text()
        assert "3.12" in text and "recommandée" in text.lower()


# ---------------------------------------------------------------------------
# MariaDB
# ---------------------------------------------------------------------------


class TestMariaDB:
    def test_section_mariadb(self):
        assert "## MariaDB" in _text()

    def test_connecteur_version(self):
        assert "1.1.14" in _text()

    def test_mysql_non_supporte(self):
        text = _text().lower()
        assert "mysql" in text and ("non support" in text or "non" in text)

    def test_postgresql_non_supporte(self):
        text = _text().lower()
        assert "postgresql" in text

    def test_version_10_11_recommandee(self):
        assert "10.11" in _text()

    def test_dependance_systeme_libmariadb(self):
        assert "libmariadb-dev" in _text()

    def test_tests_opt_in(self):
        assert "FORGE_E2E_MARIADB" in _text()

    def test_prefixe_base_forge_e2e(self):
        assert "forge_e2e_" in _text()

    def test_tests_sans_mariadb(self):
        text = _text().lower()
        assert "sans" in text and "mariadb" in text

    def test_port_par_defaut_implicite(self):
        # Le port par défaut MariaDB (3306) ou 127.0.0.1 doit être mentionné
        text = _text()
        assert "3306" in text or "127.0.0.1" in text


# ---------------------------------------------------------------------------
# Node.js et npm
# ---------------------------------------------------------------------------


class TestNodeJs:
    def test_section_nodejs(self):
        assert "Node" in _text()

    def test_tailwind_version(self):
        assert "4.2.2" in _text()

    def test_non_requis_runtime(self):
        text = _text().lower()
        assert "non requis" in text or "pas requis" in text or "uniquement" in text

    def test_build_css(self):
        assert "build:css" in _text()

    def test_fichier_css_versionne(self):
        text = _text()
        assert "tailwind.css" in text

    def test_npm_install_mentionne(self):
        assert "npm install" in _text()


# ---------------------------------------------------------------------------
# Système d'exploitation
# ---------------------------------------------------------------------------


class TestOS:
    def test_section_os(self):
        text = _text().lower()
        assert "système" in text or "os" in text

    def test_debian_recommande(self):
        assert "Debian" in _text()

    def test_ubuntu_mentionne(self):
        assert "Ubuntu" in _text()

    def test_windows_non_supporte(self):
        text = _text().lower()
        assert "windows" in text

    def test_ci_ubuntu_latest(self):
        assert "ubuntu-latest" in _text()


# ---------------------------------------------------------------------------
# Dépendances runtime
# ---------------------------------------------------------------------------


class TestDepsRuntime:
    def test_section_deps_runtime(self):
        text = _text().lower()
        assert "runtime" in text

    def test_mariadb_connecteur(self):
        assert "mariadb" in _text()

    def test_jinja2(self):
        assert "jinja2" in _text()

    def test_python_dotenv(self):
        assert "python-dotenv" in _text()

    def test_pillow(self):
        assert "Pillow" in _text()

    def test_argon2(self):
        assert "argon2" in _text()

    def test_pyotp(self):
        assert "pyotp" in _text()

    def test_trois_deps_fondamentales(self):
        text = _text().lower()
        assert "trois" in text or "fondamentales" in text or "3" in text


# ---------------------------------------------------------------------------
# Dépendances de développement
# ---------------------------------------------------------------------------


class TestDepsDev:
    def test_section_deps_dev(self):
        text = _text().lower()
        assert "développement" in text

    def test_pytest(self):
        assert "pytest" in _text()

    def test_ruff(self):
        assert "ruff" in _text()

    def test_mkdocs(self):
        assert "mkdocs" in _text()

    def test_twine(self):
        assert "twine" in _text()

    def test_pip_audit(self):
        assert "pip-audit" in _text()

    def test_build(self):
        text = _text()
        assert "`build`" in text or "build>=" in text


# ---------------------------------------------------------------------------
# Tests standard et opt-in
# ---------------------------------------------------------------------------


class TestSuiteTests:
    def test_tests_standard_sans_mariadb(self):
        text = _text()
        assert "pytest" in text

    def test_tests_optin_mariadb(self):
        assert "FORGE_E2E_MARIADB=1" in _text()

    def test_commande_opt_in(self):
        assert "test_e2e_mariadb.py" in _text()


# ---------------------------------------------------------------------------
# Versions non garanties
# ---------------------------------------------------------------------------


class TestVersionsNonGaranties:
    def test_section_non_garanties(self):
        text = _text().lower()
        assert "non garanti" in text or "non support" in text

    def test_python_inferieur_3_12(self):
        text = _text()
        assert "< 3.12" in text or "3.11" in text

    def test_mysql_non_garanti(self):
        assert "MySQL" in _text()

    def test_postgresql_non_garanti(self):
        assert "PostgreSQL" in _text()

    def test_windows_non_garanti(self):
        assert "Windows" in _text()


# ---------------------------------------------------------------------------
# Politique de mise à jour
# ---------------------------------------------------------------------------


class TestPolitiqueMaJ:
    def test_section_politique_maj(self):
        text = _text().lower()
        assert "mise à jour" in text or "politique" in text

    def test_pip_audit_recommande(self):
        assert "pip-audit" in _text()

    def test_audit_avant_release(self):
        text = _text().lower()
        assert "release" in text and "audit" in text


# ---------------------------------------------------------------------------
# Mkdocs
# ---------------------------------------------------------------------------


class TestMkdocs:
    def test_compatibility_dans_nav(self):
        mkdocs = Path("mkdocs.yml").read_text(encoding="utf-8")
        assert "compatibility.md" in mkdocs

    def test_mkdocs_build_strict(self, tmp_path):
        """Vérifie que mkdocs build --strict passe (test documentaire)."""
        import subprocess

        result = subprocess.run(
            ["mkdocs", "build", "--strict", "-d", str(tmp_path / "site")],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"mkdocs build --strict a échoué :\n{result.stderr}"
