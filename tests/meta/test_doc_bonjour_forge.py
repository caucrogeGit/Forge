"""Tests documentaires — DX-DOCS-BONJOUR-FORGE-CLOSE-001.

Verrouille le contrat de la page d'entrée `docs/bonjour-forge.md` après
renommage de l'ancien tutoriel `docs/15-minutes.md` (clôture phase
beta 11 DX). La page doit présenter le parcours développeur livré :

    forge run → route → contrôleur → Response.text → request.param
                → request.data → Response.debug → BaseController.render

Le ticket d'origine `DOC-15MIN-001` reste mentionné dans la roadmap
(historique). Le marqueur courant est `DX-DOCS-BONJOUR-FORGE-CLOSE-001`.
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

DOC = Path("docs/bonjour-forge.md")
OLD_DOC = Path("docs/15-minutes.md")
MKDOCS = Path("mkdocs.yml")
ROADMAP = Path("docs/roadmap/forge-roadmap.md")


def _text() -> str:
    return DOC.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Renommage : ancien fichier supprimé, nouveau fichier en place
# ---------------------------------------------------------------------------


class TestRename:
    def test_ancien_fichier_supprime(self):
        assert not OLD_DOC.exists(), (
            "docs/15-minutes.md doit avoir été renommé en docs/bonjour-forge.md "
            "(DX-DOCS-BONJOUR-FORGE-CLOSE-001)."
        )

    def test_nouveau_fichier_existe(self):
        assert DOC.exists(), "docs/bonjour-forge.md introuvable."

    def test_fichier_non_vide(self):
        assert len(_text()) > 500

    def test_titre_principal_bonjour_forge(self):
        first_h1 = next(
            line for line in _text().splitlines() if line.startswith("# ")
        )
        assert first_h1.strip() == "# Bonjour Forge", (
            f"Le titre H1 doit être « # Bonjour Forge », vu : {first_h1!r}"
        )


# ---------------------------------------------------------------------------
# Le parcours pédagogique attendu (8 points + différence text/render)
# ---------------------------------------------------------------------------


class TestParcoursPedagogique:
    def test_forge_run_introduit_en_premier(self):
        assert "forge run" in _text()

    def test_route_documentee(self):
        text = _text().lower()
        assert "route" in text and "mvc/routes.py" in _text()

    def test_controleur_documente(self):
        text = _text().lower()
        assert "contrôleur" in text or "controller" in text

    def test_response_text_bonjour_forge(self):
        assert 'Response.text("Bonjour Forge")' in _text()

    def test_request_param_documente(self):
        assert "request.param(" in _text()

    def test_request_data_documente(self):
        assert "request.data" in _text()

    def test_response_debug_documente(self):
        assert "Response.debug(request.data)" in _text()

    def test_base_controller_render_documente(self):
        assert "BaseController.render(" in _text()

    def test_difference_text_vs_render_explicite(self):
        text = _text()
        assert 'Response.text("Bonjour Forge")' in text
        assert 'BaseController.render("welcome/index.html"' in text

    def test_ordre_text_avant_render(self):
        """L'ordre des sections H2 dédiées doit suivre la progression
        pédagogique : Response.text → request.param → request.data →
        Response.debug → BaseController.render."""
        text = _text()
        idx_text_section = text.find("Retourner `Response.text")
        idx_render_section = text.find("Comprendre `BaseController.render")
        assert idx_text_section != -1, "Section dédiée à Response.text introuvable."
        assert idx_render_section != -1, (
            "Section dédiée à BaseController.render introuvable."
        )
        assert idx_text_section < idx_render_section, (
            "La section Response.text doit précéder la section "
            "BaseController.render dans la progression pédagogique."
        )


# ---------------------------------------------------------------------------
# Sécurité / masquage évoqué
# ---------------------------------------------------------------------------


class TestSecurite:
    def test_masquage_documente(self):
        text = _text().lower()
        assert "masqué" in text or "[masked]" in _text() or "masqu" in text

    def test_dev_vs_prod_response_debug(self):
        text = _text()
        assert "APP_ENV=dev" in text
        assert "APP_ENV=prod" in text


# ---------------------------------------------------------------------------
# Liens internes — points d'aiguillage vers la suite
# ---------------------------------------------------------------------------


class TestLiens:
    def test_lien_vers_starter_welcome(self):
        text = _text()
        assert "starters/welcome/index.md" in text

    def test_lien_vers_getting_started(self):
        text = _text()
        assert "getting-started.md" in text

    def test_lien_vers_guide(self):
        text = _text()
        assert "guide.md" in text

    def test_lien_vers_reference_http(self):
        text = _text()
        assert "reference/http.md" in text

    def test_lien_vers_cli_commands(self):
        text = _text()
        assert "reference/cli-commands.md" in text


# ---------------------------------------------------------------------------
# Aucune référence active à « 15 minutes » ne doit subsister
# ---------------------------------------------------------------------------


class TestNoLegacyMentions:
    def test_page_ne_mentionne_pas_15_minutes(self):
        text = _text()
        assert "15 minutes" not in text, (
            "La page bonjour-forge.md ne doit plus mentionner « 15 minutes »."
        )
        assert "15-minutes.md" not in text

    def test_getting_started_ne_pointe_plus_vers_15_minutes(self):
        text = Path("docs/getting-started.md").read_text(encoding="utf-8")
        assert "15-minutes.md" not in text
        assert "Bonjour Forge" in text or "bonjour-forge.md" in text

    def test_app_complete_tutorial_pointe_vers_bonjour_forge(self):
        text = Path("docs/app-complete-tutorial.md").read_text(encoding="utf-8")
        assert "15-minutes.md" not in text
        assert "bonjour-forge.md" in text


# ---------------------------------------------------------------------------
# Navigation MkDocs
# ---------------------------------------------------------------------------


class TestMkdocs:
    def test_nav_reference_bonjour_forge(self):
        mkdocs = MKDOCS.read_text(encoding="utf-8")
        assert "bonjour-forge.md" in mkdocs

    def test_nav_libelle_bonjour_forge(self):
        mkdocs = MKDOCS.read_text(encoding="utf-8")
        assert "Bonjour Forge:" in mkdocs

    def test_nav_ne_reference_plus_15_minutes(self):
        mkdocs = MKDOCS.read_text(encoding="utf-8")
        assert "15-minutes.md" not in mkdocs

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


# ---------------------------------------------------------------------------
# Roadmap — historique + nouveau marqueur
# ---------------------------------------------------------------------------


class TestRoadmap:
    def test_ticket_close_present(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "DX-DOCS-BONJOUR-FORGE-CLOSE-001" in text

    def test_ticket_close_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "DX-DOCS-BONJOUR-FORGE-CLOSE-001" in line:
                assert "livré" in line.lower(), (
                    f"DX-DOCS-BONJOUR-FORGE-CLOSE-001 non marqué comme livré : {line}"
                )
                return
        pytest.fail("Ligne DX-DOCS-BONJOUR-FORGE-CLOSE-001 introuvable.")

    def test_ticket_historique_doc_15min_conserve(self):
        # Le ticket fondateur reste tracé dans l'historique (phase 9).
        text = ROADMAP.read_text(encoding="utf-8")
        assert "DOC-15MIN-001" in text
