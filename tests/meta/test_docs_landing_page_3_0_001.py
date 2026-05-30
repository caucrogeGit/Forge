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

    def test_positioning_phrase_present(self):
        assert "Forge génère un MVC CRUD explicite" in self.source, (
            "La phrase de positionnement CRUD doit apparaître dans la landing (LANDING-BETA6-MENU-001)"
        )

    # Section FAQ : SUPPRIMÉE VOLONTAIREMENT
    # (LANDING-PUBLIC-CONTRACT-REALIGN-001). La FAQ historique a été
    # retirée de la landing canonique. Si elle revient un jour, c'est
    # sous forme de page de documentation, pas sur la landing.

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

    def test_positioning_section_exists(self):
        assert 'id="positionnement"' in self.source, (
            "La section Positionnement devrait avoir id='positionnement' (LANDING-BETA6-MENU-001)"
        )

    # Bloc « Stack technos + liens externes » : SUPPRIMÉ VOLONTAIREMENT
    # (LANDING-PUBLIC-CONTRACT-REALIGN-001). La landing ne maintient
    # plus de section dédiée listant Python/MariaDB/Jinja2/HTMX/Alpine.js/
    # Tailwind avec leurs URLs documentaires. Le strip Hero garde
    # Python 3.12+ et MariaDB ; le reste est dans la grille
    # « Construire des applications MVC sans perdre la main ».

    def test_charter_link_exists(self):
        assert "CHARTE_DOC.md" in self.source, (
            "La landing devrait avoir un lien vers CHARTE_DOC.md sur GitHub"
        )

    # Compteur de tests sur la landing : SUPPRIMÉ VOLONTAIREMENT
    # (LANDING-PUBLIC-CONTRACT-REALIGN-001). Le chiffre évolue trop vite
    # pour être un contenu stable de landing publique.


class TestNavigationStructure:
    """La navigation a la structure beta.6 (7 entrées plates, sans dropdowns)."""

    def setup_method(self):
        self.source = LANDING_SOURCE.read_text(encoding="utf-8")

    # Test <details>/<summary> pour la FAQ : SUPPRIMÉ
    # (LANDING-PUBLIC-CONTRACT-REALIGN-001). FAQ retirée volontairement
    # de la landing — plus de bloc accordéon à vérifier.

    def test_nav_logo_present(self):
        """Le logo forge-logo.png remplace le texte >Forge< dans la nav (LANDING-WELCOME-POLISH-001)."""
        nav_end = self.source.find("</nav>")
        nav_section = self.source[:nav_end] if nav_end != -1 else self.source[:600]
        assert "forge-logo.png" in nav_section, (
            "La nav devrait contenir une image forge-logo.png (logo remplace le texte Forge)"
        )
        assert ">Forge<" not in nav_section, (
            "Le texte >Forge< ne devrait plus être dans la nav — remplacé par le logo"
        )

    def test_nav_logo_h32(self):
        """Le logo de navigation utilise h-32 w-auto object-contain (LANDING-NAV-COMPACT-001)."""
        nav_end = self.source.find("</nav>")
        nav_section = self.source[:nav_end] if nav_end != -1 else self.source[:600]
        assert "h-32" in nav_section, (
            "Le logo de navigation doit utiliser h-32 (taille lisible)"
        )
        assert "h-16" not in nav_section, (
            "La navbar ne devrait plus être en h-16"
        )
        assert "min-h-40" not in nav_section, (
            "La navbar ne devrait plus utiliser min-h-40 — remplacé par h-32 compacte"
        )

    @pytest.mark.parametrize("nav_label", [
        ">Démarrer<",
        ">CRUD<",
        ">API<",
        ">Starters<",
        ">Architecture<",
        ">Référence<",
        ">GitHub<",
    ])
    def test_nav_entry_present(self, nav_label):
        assert nav_label in self.source, (
            f"La nav devrait contenir l'entrée '{nav_label}' "
            f"(menu LANDING-BETA9-UPDATE-001)"
        )

    def test_no_briques_dropdown_in_nav(self):
        """Le dropdown 'Briques' a été supprimé du menu principal (LANDING-BETA6-MENU-001)."""
        nav_end = self.source.find("</nav>")
        nav_section = self.source[:nav_end] if nav_end != -1 else self.source[:500]
        assert ">Briques<" not in nav_section and "Briques\n" not in nav_section, (
            "Le dropdown Briques ne devrait plus être dans la nav (remplacé par CRUD, Architecture)"
        )

    def test_no_projet_dropdown_in_nav(self):
        """Le dropdown 'Projet' a été supprimé du menu principal (LANDING-BETA6-MENU-001)."""
        nav_end = self.source.find("</nav>")
        nav_section = self.source[:nav_end] if nav_end != -1 else self.source[:500]
        assert ">Projet<" not in nav_section and "Projet\n" not in nav_section, (
            "Le dropdown Projet ne devrait plus être dans la nav (GitHub direct en entrée)"
        )


class TestStateSectionRefonte:
    """La section positionnement contient les éléments clés de l'état du projet."""

    def setup_method(self):
        import tomllib
        import re as _re
        self.source = LANDING_SOURCE.read_text(encoding="utf-8")
        _v = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
        self._semver = _re.sub(r"(\d+\.\d+\.\d+)b(\d+)$", r"\1-beta.\2", _v)

    def test_state_mentions_current_version(self):
        assert f"Forge {self._semver}" in self.source, (
            f"La landing devrait mentionner Forge {self._semver}"
        )

    def test_state_mentions_source_ouverture(self):
        assert "ouverture du code source" in self.source, (
            "La landing devrait mentionner l'ouverture du code source "
            "(cf. LANDING-LICENSE-WORDING-001)"
        )

    def test_state_mentions_modules_count(self):
        # Six opt-ins officiels depuis beta.12 (cf. test_optins_count_consistency).
        assert "6 modules officiels" in self.source, (
            "La landing devrait mentionner les 6 modules officiels opt-in"
        )

    def test_state_no_obsolete_phases(self):
        assert "Phases 0 à 10" not in self.source, (
            "L'ancien texte 'Phases 0 à 10' ne devrait plus apparaître"
        )

    def test_trajectoire_section(self):
        # "Après 3.0" remplacé par "Trajectoire 1.0" (LANDING-CARDS-LINKS-ORDER-001)
        assert "Trajectoire 1.0" in self.source, (
            "La landing devrait avoir un bloc 'Trajectoire 1.0' (roadmap)"
        )

    def test_trajectoire_mentions_stabilization(self):
        assert "Stabilisation" in self.source, (
            "La landing devrait parler de Stabilisation (roadmap)"
        )
        assert "Auth/User avancée" not in self.source, (
            "La landing ne devrait plus dire 'Auth/User avancée' "
            "(MFA et RBAC sont déjà des modules)"
        )


class TestStartersSection:
    """La section starters affiche les 7 starters (LANDING-STARTERS-RESTORE-001)."""

    def setup_method(self):
        self.source = LANDING_SOURCE.read_text(encoding="utf-8")

    def test_starters_section_exists(self):
        assert 'id="starters"' in self.source

    def test_premier_pas_link_pointe_vers_welcome(self):
        assert "starters/welcome/" in self.source, (
            "La carte Premier pas doit pointer vers starters/welcome/ "
            "(LANDING-STARTERS-RESTORE-001)"
        )

    def test_premier_pas_ne_pointe_plus_vers_starters_generique(self):
        starters_idx = self.source.find('id="starters"')
        section = self.source[starters_idx:starters_idx + 3000] if starters_idx != -1 else self.source
        assert 'href="https://caucrogegit.github.io/Forge/starters/"' not in section, (
            "La carte Premier pas ne doit plus pointer vers la page starters générique"
        )

    @pytest.mark.parametrize("starter_url", [
        "starters/welcome/",
        "starters/contact-simple/",
        "starters/utilisateurs-auth/",
        "starters/auth-mfa/",
    ])
    def test_all_starter_urls_present(self, starter_url):
        assert starter_url in self.source, (
            f"La landing doit contenir le lien vers {starter_url} "
            "(LANDING-STARTERS-RESTORE-001)"
        )


class TestSyncedToDocsIndex:
    """docs/index.html est synchronisé avec la source."""

    def test_sync_header_present(self):
        content = LANDING_GENERATED.read_text(encoding="utf-8")
        assert "FICHIER GENERE PAR forge sync:landing" in content, (
            "docs/index.html devrait avoir l'en-tête indiquant qu'il est "
            "généré — ajouter le commentaire ou relancer forge sync:landing"
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
