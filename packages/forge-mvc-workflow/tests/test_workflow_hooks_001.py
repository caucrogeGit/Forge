"""WORKFLOW-HOOKS-001 : appliquer une transition dans un ordre garanti.

Le paquet savait dire si une transition est **permise**, jamais l'appliquer.
Chaque application réécrivait le même enchaînement à la main : vérifier, agir
avant, écrire, agir après. Rien ne garantissait l'ordre, et rien n'empêchait
d'appeler l'action d'après quand celle d'avant avait refusé.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_workflow")

from forge_mvc_workflow import (  # noqa: E402
    TransitionEvent,
    WorkflowTransitionError,
    apply_transition,
    make_transition,
)

TRANSITIONS = [
    make_transition("draft", "published"),
    make_transition("published", "archived"),
]


class Refus(Exception):
    """Refus d'une règle métier, tel qu'une application le lèverait."""


class EchecEcriture(Exception):
    """Panne de la base, telle qu'un pilote la lèverait."""


@pytest.fixture
def journal() -> list[str]:
    return []


class TestOrdre:
    def test_les_trois_etapes_s_enchainent(self, journal: list[str]) -> None:
        apply_transition(
            TRANSITIONS, "draft", "published",
            before=lambda e: journal.append("avant"),
            commit=lambda e: journal.append("ecriture"),
            after=lambda e: journal.append("apres"),
        )
        assert journal == ["avant", "ecriture", "apres"]

    def test_le_statut_atteint_est_rendu(self) -> None:
        assert apply_transition(TRANSITIONS, "draft", "published") == "published"

    def test_sans_aucune_accroche_la_transition_reste_valide(self) -> None:
        assert apply_transition(TRANSITIONS, "published", "archived") == "archived"


class TestVeto:
    def test_un_refus_avant_empeche_l_ecriture(self, journal: list[str]) -> None:
        """Le point qui donne sa valeur au mécanisme."""
        def refuser(evenement: TransitionEvent) -> None:
            raise Refus("brouillon incomplet")

        with pytest.raises(Refus):
            apply_transition(
                TRANSITIONS, "draft", "published",
                before=refuser,
                commit=lambda e: journal.append("ecriture"),
                after=lambda e: journal.append("apres"),
            )
        assert journal == [], "ni l'écriture ni l'accroche d'après ne doivent avoir lieu"

    def test_le_refus_remonte_tel_quel(self) -> None:
        """Un message maquillé ferait perdre la cause."""
        def refuser(evenement: TransitionEvent) -> None:
            raise Refus("brouillon incomplet")

        with pytest.raises(Refus, match="brouillon incomplet"):
            apply_transition(TRANSITIONS, "draft", "published", before=refuser)

    def test_une_ecriture_en_echec_empeche_l_accroche_apres(
        self, journal: list[str]
    ) -> None:
        def echouer(evenement: TransitionEvent) -> None:
            raise EchecEcriture("base injoignable")

        with pytest.raises(EchecEcriture):
            apply_transition(
                TRANSITIONS, "draft", "published",
                commit=echouer,
                after=lambda e: journal.append("apres"),
            )
        assert journal == []

    def test_un_echec_apres_ne_defait_rien(self, journal: list[str]) -> None:
        """L'écriture a eu lieu : avaler l'exception cacherait un état changé."""
        def echouer(evenement: TransitionEvent) -> None:
            raise Refus("notification impossible")

        with pytest.raises(Refus):
            apply_transition(
                TRANSITIONS, "draft", "published",
                commit=lambda e: journal.append("ecriture"),
                after=echouer,
            )
        assert journal == ["ecriture"], "l'écriture faite reste faite"


class TestTransitionNonDeclaree:
    def test_une_transition_absente_est_refusee(self, journal: list[str]) -> None:
        with pytest.raises(WorkflowTransitionError, match="non déclarée"):
            apply_transition(
                TRANSITIONS, "draft", "archived",
                before=lambda e: journal.append("avant"),
            )
        assert journal == [], "la vérification précède toute accroche"

    def test_le_sens_inverse_n_est_pas_permis_de_soi_meme(self) -> None:
        with pytest.raises(WorkflowTransitionError):
            apply_transition(TRANSITIONS, "published", "draft")

    def test_le_message_nomme_les_deux_statuts(self) -> None:
        with pytest.raises(WorkflowTransitionError, match="draft.*archived"):
            apply_transition(TRANSITIONS, "draft", "archived")


class TestEvenement:
    def test_les_accroches_recoivent_les_deux_statuts(self) -> None:
        vus: list[TransitionEvent] = []
        apply_transition(
            TRANSITIONS, "draft", "published", before=vus.append, after=vus.append
        )

        assert len(vus) == 2
        assert all(e.from_status == "draft" and e.to_status == "published" for e in vus)

    def test_le_contexte_est_transmis(self) -> None:
        vus: list[TransitionEvent] = []
        apply_transition(
            TRANSITIONS, "draft", "published",
            before=vus.append, context={"auteur": "roger", "objet": 42},
        )
        assert vus[0].context == {"auteur": "roger", "objet": 42}

    def test_le_contexte_est_copie(self) -> None:
        """Une accroche ne doit pas modifier le dictionnaire de l'appelant."""
        origine = {"auteur": "roger"}
        apply_transition(
            TRANSITIONS, "draft", "published",
            before=lambda e: e.context.update({"ajoute": True}),
            context=origine,
        )
        assert origine == {"auteur": "roger"}

    def test_sans_contexte_il_est_vide(self) -> None:
        vus: list[TransitionEvent] = []
        apply_transition(TRANSITIONS, "draft", "published", before=vus.append)
        assert vus[0].context == {}

    def test_l_evenement_est_immuable(self) -> None:
        evenement = TransitionEvent("draft", "published")
        with pytest.raises(Exception):
            evenement.to_status = "archived"  # type: ignore[misc]


class TestSansPersistance:
    def test_le_paquet_n_ecrit_nulle_part(self) -> None:
        """L'application fournit l'écriture, seule à savoir où son statut est rangé."""
        from pathlib import Path

        from forge_mvc_workflow import hooks

        source = Path(hooks.__file__).read_text(encoding="utf-8")
        for interdit in ("import core.database", "from core.database", "INSERT", "UPDATE"):
            assert interdit not in source, f"{interdit} n'a rien à faire ici"

    def test_sans_commit_l_ordre_reste_annonce(self, journal: list[str]) -> None:
        """Le paquet ne peut alors pas savoir si l'écriture a eu lieu, et le dit."""
        apply_transition(
            TRANSITIONS, "draft", "published",
            before=lambda e: journal.append("avant"),
            after=lambda e: journal.append("apres"),
        )
        assert journal == ["avant", "apres"]
