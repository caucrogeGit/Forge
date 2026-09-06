"""Garde-fou GOV-CHANGELOG-COMPLETUDE-GARDEFOU-001.

Le pré-vol de release vérifiait que `CHANGELOG.md` **contient un titre** pour
la version publiée. La rc8 s'est préparée avec 51 des 106 tickets livrés
depuis la rc7 au journal : le titre existait, la section taisait la moitié de
ce qu'un exploitant doit lire avant de mettre à jour.

Ce garde-fou exerce la détection sur des entrées **fabriquées** plutôt que sur
le dépôt. La CI travaille sur un clone superficiel, sans tags ni journal : un
contrôle qui lirait l'historique réel s'y ignorerait en silence, et un test
ignoré n'est pas un test qui passe.

Le branchement au pré-vol est vérifié à part : un détecteur juste que personne
n'appelle ne protège rien.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTIL = PROJECT_ROOT / "tools" / "check_changelog_completeness.py"
PRE_VOL = PROJECT_ROOT / "tools" / "release-validate.sh"


def _module():
    """Charge l'outil par son chemin, `tools/` n'étant pas un paquet."""
    if not OUTIL.exists():
        pytest.fail(f"{OUTIL} est absent : le contrôle de complétude a disparu")
    spec = importlib.util.spec_from_file_location("check_changelog_completeness", OUTIL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestDetectionDesAbsents:
    """`tickets_absents` compare des sujets de commit à un journal."""

    def test_un_ticket_absent_est_signale(self):
        """Le cas qui a manqué à la rc8 : un ticket livré, aucune entrée."""
        module = _module()
        absents = module.tickets_absents(
            ["feat(deploy): refuser le demarrage muet (DEPLOY-CHECK-SESSIONS-WORKERS-001)"],
            "## [Non publié]\n\n### Corrigé\n\n- Autre chose.\n",
        )
        assert absents == ["DEPLOY-CHECK-SESSIONS-WORKERS-001"]

    def test_un_ticket_present_ne_lest_pas(self):
        """Un code cité n'importe où dans le journal suffit."""
        module = _module()
        absents = module.tickets_absents(
            ["fix(core): reparer (CORE-EXEMPLE-001)"],
            "- **Une entrée (`CORE-EXEMPLE-001`).**\n",
        )
        assert absents == []

    def test_plusieurs_absents_sont_tous_rendus_et_dedupliques(self):
        """Deux commits sur le même ticket ne le comptent qu'une fois."""
        module = _module()
        absents = module.tickets_absents(
            [
                "feat(a): un (AAA-BBB-001)",
                "fix(a): deux (AAA-BBB-001)",
                "docs(c): trois (CCC-DDD-002)",
            ],
            "",
        )
        assert absents == ["AAA-BBB-001", "CCC-DDD-002"]

    def test_un_sujet_sans_code_ne_produit_rien(self):
        """Un sujet hors convention ne fabrique pas d'accusation."""
        module = _module()
        assert module.tickets_absents(["chore: menage"], "") == []

    @pytest.mark.parametrize(
        "sujet",
        [
            "feat(x): sujet (minuscule-001)",
            "feat(x): sujet (SANSTIRET-001)",
            "feat(x): sujet (AAA-BBB-1)",
            "feat(x): sujet AAA-BBB-001",
        ],
    )
    def test_les_formes_hors_convention_ne_sont_pas_prises_pour_des_tickets(self, sujet):
        """Le motif accuse le format canonique, et lui seul.

        Un détecteur qui accuse à tort finit désactivé : la forme reconnue est
        celle que la convention de tickets impose, code entre parenthèses en
        fin de sujet.
        """
        module = _module()
        assert module.tickets_absents([sujet], "") == []


class TestHistoriqueManquant:
    """Sans historique, l'outil échoue au lieu de passer."""

    def test_un_intervalle_vide_leve(self):
        """Zéro commit entre le tag et HEAD veut dire journal tronqué."""
        module = _module()
        with pytest.raises(module.HistoriqueIndisponible):
            module.sujets_depuis("v0.0.0-inexistant")

    def test_le_code_retour_de_lhistorique_manquant_nest_pas_un_succes(self):
        """`main` rend 2, distinct du 1 des tickets absents et du 0 du succès."""
        module = _module()
        assert module.main(["outil", "v0.0.0-inexistant"]) == 2


class TestBranchementAuPreVol:
    """Le pré-vol de release appelle le contrôle."""

    def test_le_pre_vol_appelle_loutil(self):
        """Un détecteur que personne n'appelle ne protège rien."""
        source = PRE_VOL.read_text(encoding="utf-8")
        assert "tools/check_changelog_completeness.py" in source, (
            "release-validate.sh doit appeler check_changelog_completeness.py"
        )

    def test_lechec_du_controle_fait_echouer_le_pre_vol(self):
        """L'appel est branché sur `_fail`, pas sur un avertissement."""
        source = PRE_VOL.read_text(encoding="utf-8")
        debut = source.index("tools/check_changelog_completeness.py")
        bloc = source[debut : debut + 400]
        assert "_fail" in bloc, (
            "un contrôle branché sans _fail laisse publier ce qu'il vient de refuser"
        )
