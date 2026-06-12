"""Tests documentaires — INSTALL-CORE-DEV-DOCS-AUDIT-001.

Verrouille le contrat de `docs/install/core-dev.md` après
consolidation : la page doit guider clairement un contributeur qui
modifie le **core Forge** lui-même (et non un utilisateur qui crée
une application avec Forge).

Critères :

- distingue explicitement utilisateur du framework vs développeur core ;
- couvre les 5 étapes canoniques (clone, venv, install editable,
  validations, CSS) ;
- documente les 5 validations canoniques avant commit (pytest,
  compileall, ruff, mkdocs --strict, git diff --check) ;
- ne recommande pas `pipx` comme méthode de développement du core ;
- explique honnêtement le rôle (limité) de `forge run` dans le dépôt
  core ;
- pointe vers les ressources annexes (contributing, ADR, release).
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

DOC = Path("docs/install/core-dev.md")
ROADMAP = Path("docs/roadmap/forge-roadmap.md")


def _text() -> str:
    return DOC.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Existence
# ---------------------------------------------------------------------------


class TestExistence:
    def test_fichier_existe(self):
        assert DOC.exists(), "docs/install/core-dev.md introuvable."

    def test_fichier_substantiel(self):
        assert len(_text()) > 2_000

    def test_titre_h1_explicite(self):
        first_h1 = next(
            line for line in _text().splitlines() if line.startswith("# ")
        )
        # Le H1 doit clairement annoncer le parcours core / contribution.
        assert "Mode développement" in first_h1
        assert "core" in first_h1.lower() or "contribuer" in first_h1.lower()


# ---------------------------------------------------------------------------
# Distinction utilisateur framework / développeur core
# ---------------------------------------------------------------------------


class TestUserVsCoreDistinction:
    def test_distinction_explicite_dans_la_page(self):
        text = _text()
        # Une section dédiée à la distinction.
        assert (
            "Utilisateur du framework vs développeur du core" in text
            or "utilisateur du framework" in text.lower()
            and "développeur du core" in text.lower()
        )

    def test_warn_contre_pipx_pour_core_dev(self):
        text = _text()
        normalized = " ".join(text.split())
        assert "Ne pas utiliser `pipx` pour développer le core" in normalized or (
            "ne pas utiliser" in normalized.lower()
            and "pipx" in normalized
            and "core" in normalized.lower()
        )

    def test_pipx_n_est_pas_la_methode_recommandee_pour_core(self):
        """`pipx install ... forge-mvc` apparaît au plus dans le tableau
        comparatif (côté utilisateur), jamais comme commande à exécuter
        pour le développement core."""
        text = _text()
        # Heuristique : `pipx install` apparaît au plus 1 fois (dans la
        # ligne du tableau qui dit ce que fait l'utilisateur).
        occurrences = text.count("pipx install")
        assert occurrences <= 1, (
            f"`pipx install` apparaît {occurrences} fois — `pipx` ne doit "
            "pas être présenté comme méthode de développement du core."
        )


# ---------------------------------------------------------------------------
# 5 étapes canoniques
# ---------------------------------------------------------------------------


class TestStepsCanoniques:
    def test_git_clone_present(self):
        text = _text()
        assert "git clone" in text
        assert "caucrogeGit/Forge" in text

    def test_venv_present(self):
        text = _text()
        assert "python -m venv" in text
        assert "source .venv/bin/activate" in text

    def test_install_editable_via_requirements_dev(self):
        """Le parcours principal passe par `requirements-dev.txt` (qui
        installe core + tools + opt-ins en éditable)."""
        text = _text()
        assert "pip install -r requirements-dev.txt" in text

    def test_install_editable_alternative_documentee(self):
        """`pip install -e .` doit aussi apparaître (variante minimale)."""
        text = _text()
        assert "pip install -e ." in text


# ---------------------------------------------------------------------------
# 5 validations canoniques avant commit
# ---------------------------------------------------------------------------


class TestValidationsCanoniques:
    def test_pytest(self):
        text = _text()
        assert "python -m pytest" in text

    def test_compileall(self):
        text = _text()
        assert "python -m compileall -q ." in text

    def test_ruff_check(self):
        text = _text()
        assert "ruff check ." in text

    def test_mkdocs_build_strict(self):
        text = _text()
        assert "mkdocs build --strict" in text

    def test_git_diff_check(self):
        text = _text()
        assert "git diff --check" in text


# ---------------------------------------------------------------------------
# Forge run dans le dépôt core — décision honnête
# ---------------------------------------------------------------------------


class TestForgeRunInCoreRepo:
    def test_forge_run_est_documente_avec_limites(self):
        text = _text()
        assert "forge run" in text
        normalized = " ".join(text.split())
        # La page doit clarifier le rôle limité de `forge run` dans le
        # dépôt core (validation manuelle, pas développement quotidien).
        assert (
            "Différence avec un projet généré" in normalized
            or "outil de validation manuelle" in normalized
            or "pas le point d'entrée principal" in normalized.lower()
        )

    def test_pas_le_workflow_quotidien_du_contributeur(self):
        """Le quotidien core-dev = pytest/ruff/mkdocs, pas `forge run`."""
        text = _text()
        normalized = " ".join(text.split())
        assert "pytest" in normalized and "ruff" in normalized
        # Et idéalement une phrase qui le dit explicitement.
        assert (
            "le quotidien du contributeur" in normalized.lower()
            or "le quotidien core-dev" in normalized.lower()
            or "pytest`, `ruff`," in normalized
        )

    def test_dogfood_explique(self):
        """Le fait que le dépôt contient `app.py` + `mvc/` (dogfooding)
        doit être expliqué pour ne pas surprendre."""
        text = _text()
        assert "app.py" in text and "mvc/" in text


# ---------------------------------------------------------------------------
# Opt-ins / packages
# ---------------------------------------------------------------------------


class TestOptins:
    def test_packages_dir_mentionne(self):
        text = _text()
        assert "packages/" in text or "packages/forge-mvc" in text

    def test_modules_opt_in_listes(self):
        text = _text()
        for module in [
            "forge-mvc-mfa",
            "forge-mvc-rbac",
            "forge-mvc-workflow",
            "forge-mvc-stats",
            "forge-mvc-images",
        ]:
            assert module in text, f"Module opt-in manquant : {module}"


# ---------------------------------------------------------------------------
# Tailwind / Node
# ---------------------------------------------------------------------------


class TestTailwindCss:
    def test_node_est_optionnel(self):
        text = _text()
        # Doit dire clairement que Node n'est pas requis pour pytest /
        # mkdocs (CSS déjà commité).
        normalized = " ".join(text.split())
        assert "tailwind.css" in text.lower()
        assert (
            "uniquement pour recompiler" in normalized.lower()
            or "déjà commité" in normalized
        )

    def test_build_css_commande(self):
        text = _text()
        assert "npm run build:css" in text


# ---------------------------------------------------------------------------
# Liens vers les ressources annexes
# ---------------------------------------------------------------------------


class TestLiensAnnexes:
    def test_lien_contributing(self):
        text = _text()
        assert "contributing.md" in text

    def test_lien_charter(self):
        text = _text()
        assert "charter.md" in text or "Charte" in text

    def test_lien_adr(self):
        text = _text()
        assert "adr/" in text

    def test_lien_pipx_pour_utilisateur(self):
        """La page renvoie vers la page poste Linux pour l'autre parcours."""
        text = _text()
        assert "poste-linux.md" in text

    def test_lien_install_windows_wsl(self):
        text = _text()
        assert "windows-wsl.md" in text


# ---------------------------------------------------------------------------
# Roadmap
# ---------------------------------------------------------------------------


class TestRoadmap:
    def test_ticket_present(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "INSTALL-CORE-DEV-DOCS-AUDIT-001" in text

    def test_ticket_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "INSTALL-CORE-DEV-DOCS-AUDIT-001" in line:
                assert "livré" in line.lower(), (
                    f"INSTALL-CORE-DEV-DOCS-AUDIT-001 non marqué comme livré : {line}"
                )
                return
        pytest.fail("Ligne INSTALL-CORE-DEV-DOCS-AUDIT-001 introuvable.")


# ---------------------------------------------------------------------------
# Build MkDocs strict — garde-fou final
# ---------------------------------------------------------------------------


class TestMkdocsBuild:
    def test_mkdocs_build_strict(self):
        import subprocess

        result = subprocess.run(
            ["mkdocs", "build", "--strict"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"mkdocs build --strict a échoué :\n{result.stderr}"
        )
