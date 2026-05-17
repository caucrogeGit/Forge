"""Tests DOCS-LANDING-PAGE-3.0-001 : landing page actualisée pour Forge 3.0."""
from pathlib import Path
import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent  # depuis tests/meta/
LANDING_SOURCE = PROJECT_ROOT / "mvc" / "views" / "landing" / "index.html"
LANDING_GENERATED = PROJECT_ROOT / "docs" / "index.html"


class TestSourceFileExists:
    """Les fichiers source et généré existent."""

    def test_source_exists(self):
        assert LANDING_SOURCE.exists(), (
            "mvc/views/landing/index.html doit exister "
            "(source canonique de la landing)"
        )

    def test_generated_exists(self):
        assert LANDING_GENERATED.exists(), (
            "docs/index.html doit exister (généré via forge sync:landing)"
        )


class TestVersionBumped:
    """La version courante est bien mentionnée dans la landing."""

    def setup_method(self):
        import tomllib
        import re as _re
        self.source = LANDING_SOURCE.read_text(encoding="utf-8")
        self.generated = LANDING_GENERATED.read_text(encoding="utf-8")
        _v = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
        _sv = _re.sub(r"(\d+\.\d+\.\d+)b(\d+)$", r"\1-beta.\2", _v)
        self.version_strings = [f"v{_sv}", f"Forge {_sv}", "Python 3.12+"]

    def test_version_mentioned_in_source(self):
        for vs in self.version_strings:
            assert vs in self.source, (
                f"La source de la landing devrait mentionner '{vs}'."
            )

    def test_version_mentioned_in_generated(self):
        for vs in self.version_strings:
            assert vs in self.generated, (
                f"docs/index.html devrait mentionner '{vs}'."
            )


class TestNoObsoleteContent:
    """Les références obsolètes ne sont plus dans la landing."""

    def setup_method(self):
        self.source = LANDING_SOURCE.read_text(encoding="utf-8")

    @pytest.mark.parametrize("forbidden", [
        "v2.5.0",                   # Ancienne version Hero
        "Python 3.11+",             # Ancienne version minimum Python
        "Forge 2.2.0",              # Ancien label terminal + section État
        "MFA et OIDC",              # Carte Auth/User ancien texte
    ])
    def test_obsolete_not_in_source(self, forbidden):
        assert forbidden not in self.source, (
            f"La source de la landing contient encore '{forbidden}' "
            f"(obsolescence Forge 3.0)"
        )

    def test_no_oidc_mention_at_all(self):
        """OIDC supprimé en OIDC-REMOVE-OR-EXTRACT-001 — aucune mention."""
        for line in self.source.splitlines():
            assert "OIDC" not in line and " oidc " not in line, (
                f"OIDC ne devrait plus être mentionné dans la landing : "
                f"'{line.strip()}'"
            )


class TestNewElementsPresent:
    """Les nouveaux éléments de la landing 3.0 sont présents."""

    def setup_method(self):
        self.source = LANDING_SOURCE.read_text(encoding="utf-8")

    def test_hero_mentions_source_disponible(self):
        assert "Source disponible" in self.source, (
            "Le strip Hero doit mentionner 'Source disponible' — "
            "Forge est sous licence propriétaire / source disponible, pas open source (cf. LICENSE)"
        )

    def test_core_h2_renamed(self):
        assert "L'écosystème Forge" in self.source, (
            "Le H2 de la section Core devrait être 'L'écosystème Forge.'"
        )

    def test_modules_subsection_exists(self):
        assert 'id="modules"' in self.source, (
            "La sous-section Modules officiels devrait avoir id='modules' "
            "pour ancre nav"
        )
        assert "Modules officiels opt-in" in self.source, (
            "Le H3 'Modules officiels opt-in' devrait être présent"
        )

    @pytest.mark.parametrize("module_name", [
        "forge-mvc-mfa",
        "forge-mvc-rbac",
        "forge-mvc-workflow",
        "forge-mvc-stats",
    ])
    def test_all_modules_mentioned(self, module_name):
        assert module_name in self.source, (
            f"Le module {module_name} devrait être mentionné dans la landing"
        )

    def test_stack_section_exists(self):
        assert 'id="stack"' in self.source, (
            "La nouvelle section Stack devrait avoir id='stack'"
        )
        assert "La stack Forge" in self.source, (
            "Le H2 de la section Stack devrait être 'La stack Forge.'"
        )

    @pytest.mark.parametrize("stack_techno", [
        "Python",
        "MariaDB",
        "Jinja2",
        "HTMX",
        "Alpine.js",
        "Tailwind",
    ])
    def test_stack_mentions_all_technos(self, stack_techno):
        assert stack_techno in self.source, (
            f"La section Stack devrait mentionner {stack_techno}"
        )

    @pytest.mark.parametrize("stack_url", [
        "docs.python.org/3.12",
        "mariadb.org",
        "jinja.palletsprojects.com",
        "htmx.org",
        "alpinejs.dev",
        "tailwindcss.com",
    ])
    def test_stack_mentions_doc_urls(self, stack_url):
        assert stack_url in self.source, (
            f"La section Stack devrait avoir un lien vers {stack_url}"
        )

    def test_charter_button_exists(self):
        assert "CHARTE_DOC.md" in self.source, (
            "La section Documentation devrait avoir un bouton vers "
            "CHARTE_DOC.md sur GitHub"
        )

    def test_test_count_mentioned(self):
        assert "Plus de 9000 tests" in self.source, (
            "La mention de tests devrait dire 'Plus de 9000 tests' "
            "(au lieu de l'ancienne 'Plus de 8000 tests')"
        )


class TestNavigationStructure:
    """La navigation a la nouvelle structure (5 entrées + 2 dropdowns)."""

    def setup_method(self):
        self.source = LANDING_SOURCE.read_text(encoding="utf-8")

    def test_uses_details_for_dropdowns(self):
        """Les dropdowns sont implémentés avec <details>/<summary>."""
        details_count = self.source.count("<details")
        assert details_count >= 2, (
            f"La nav devrait contenir au moins 2 <details> (dropdowns "
            f"Briques et Projet), trouvé {details_count}"
        )

    @pytest.mark.parametrize("nav_label", [
        ">Forge<",                  # logo/marque
        ">Installation<",
        ">Starters<",
        "Briques",                  # summary du dropdown (multi-ligne avec SVG)
        ">Documentation<",
        "Projet",                   # summary du dropdown (multi-ligne avec SVG)
    ])
    def test_nav_entry_present(self, nav_label):
        assert nav_label in self.source, (
            f"La nav devrait contenir l'entrée '{nav_label}'"
        )

    def test_briques_dropdown_items(self):
        """Le dropdown Briques contient Core, Modules, CLI."""
        briques_pos = self.source.find("Briques")
        if briques_pos == -1:
            pytest.fail("Mention 'Briques' introuvable")
        following = self.source[briques_pos:briques_pos + 1200]
        assert ">Core<" in following, "Le dropdown Briques devrait contenir Core"
        assert ">Modules<" in following, "Le dropdown Briques devrait contenir Modules"
        assert ">CLI<" in following, "Le dropdown Briques devrait contenir CLI"

    def test_projet_dropdown_items(self):
        """Le dropdown Projet contient Roadmap et GitHub."""
        projet_pos = self.source.find("Projet")
        if projet_pos == -1:
            pytest.fail("Mention 'Projet' introuvable")
        following = self.source[projet_pos:projet_pos + 1500]
        assert ">Roadmap<" in following, "Le dropdown Projet devrait contenir Roadmap"
        assert ">GitHub<" in following, "Le dropdown Projet devrait contenir GitHub"


class TestStateSectionRefonte:
    """La section État a été refondue pour la version courante."""

    def setup_method(self):
        import tomllib
        import re as _re
        self.source = LANDING_SOURCE.read_text(encoding="utf-8")
        _v = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
        self._semver = _re.sub(r"(\d+\.\d+\.\d+)b(\d+)$", r"\1-beta.\2", _v)

    def test_state_mentions_current_version(self):
        assert f"Forge {self._semver}" in self.source, (
            f"Le bloc 'État actuel' devrait mentionner Forge {self._semver}"
        )

    def test_state_mentions_source_ouverture(self):
        assert "ouverture du code source" in self.source, (
            "Le bloc 'État actuel' devrait mentionner l'ouverture du code source "
            "(remplace 'open source' — cf. LANDING-LICENSE-WORDING-001)"
        )

    def test_state_mentions_modules_count(self):
        assert "4 modules officiels" in self.source, (
            "Le bloc 'État actuel' devrait mentionner les 4 modules officiels"
        )

    def test_state_no_obsolete_phases(self):
        assert "Phases 0 à 10" not in self.source, (
            "L'ancien texte 'Phases 0 à 10' ne devrait plus apparaître"
        )

    def test_after_3_0_section(self):
        assert "Après 3.0" in self.source, (
            "Le bloc droite devrait avoir le badge 'Après 3.0'"
        )

    def test_after_3_0_mentions_stabilization(self):
        assert "Stabilisation" in self.source, (
            "Le bloc 'Après 3.0' devrait parler de Stabilisation"
        )
        assert "Auth/User avancée" not in self.source, (
            "Le bloc 'Après 3.0' ne devrait plus dire 'Auth/User avancée' "
            "(MFA et RBAC sont déjà des modules)"
        )


class TestSyncedToDocsIndex:
    """docs/index.html est synchronisé avec la source."""

    def test_sync_header_present(self):
        content = LANDING_GENERATED.read_text(encoding="utf-8")
        assert "FICHIER GENERE PAR forge sync:landing" in content, (
            "docs/index.html devrait avoir l'en-tête indiquant qu'il est "
            "généré par forge sync:landing"
        )

    def test_version_synced(self):
        import tomllib
        import re as _re
        _v = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
        _sv = _re.sub(r"(\d+\.\d+\.\d+)b(\d+)$", r"\1-beta.\2", _v)
        tag = f"v{_sv}"
        source = LANDING_SOURCE.read_text(encoding="utf-8")
        generated = LANDING_GENERATED.read_text(encoding="utf-8")
        assert tag in source, f"La source landing doit mentionner {tag}."
        assert tag in generated, (
            f"docs/index.html devrait être synchronisé (contenir {tag}). "
            "Lancer `forge sync:landing` pour régénérer."
        )
