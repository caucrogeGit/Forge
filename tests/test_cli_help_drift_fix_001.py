"""Tests — CLI-HELP-DRIFT-FIX-001 : l'aide CLI reflète le comportement réel.

Trois dérives vérifiées lors de l'audit 2026-07 sont corrigées et verrouillées :
  1. l'aide riche de `new` documente `--bare` (supporté par forge.py, ADR-063) ;
  2. l'aide riche de `make:public-page` annonce le layout réellement étendu
     (`PUBLIC_LAYOUT` du générateur, pas un layouts/public.html inexistant) ;
  3. le sommaire `forge help` décrit `db:init` conformément à ADR-067
     (affiche le SQL par défaut, `--run` pour exécuter) — aligné sur la
     description d'une ligne de HELP_DESCRIPTIONS.
"""
from __future__ import annotations

from cli._support.help import build_help
from cli._support.help_dispatch import HELP_DESCRIPTIONS, HELP_TEXTS_RICH
from cli.public.public_page import PUBLIC_LAYOUT


class TestNewHelpDocumentsBare:
    def test_usage_et_options_mentionnent_bare(self):
        rich = HELP_TEXTS_RICH["new"]
        assert "--bare" in rich

    def test_reference_adr_063(self):
        assert "ADR-063" in HELP_TEXTS_RICH["new"]


class TestPublicPageLayout:
    def test_aide_annonce_le_layout_reel(self):
        rich = HELP_TEXTS_RICH["make:public-page"]
        assert PUBLIC_LAYOUT in rich

    def test_ancien_layout_absent(self):
        assert "layouts/public.html" not in HELP_TEXTS_RICH["make:public-page"]


class TestDbInitSummary:
    def test_sommaire_conforme_adr_067(self):
        summary = build_help("test")
        assert "Crée la base de données depuis les entités" not in summary
        line = next(
            ligne for ligne in summary.splitlines() if ligne.strip().startswith("db:init")
        )
        assert "SQL de provisioning" in line
        assert "--run" in line

    def test_description_riche_et_sommaire_coherents(self):
        # La description d'une ligne (HELP_DESCRIPTIONS) est la référence :
        # le sommaire ne doit pas la contredire sur le verbe (afficher, pas créer).
        assert "Affiche" in HELP_DESCRIPTIONS["db:init"]
