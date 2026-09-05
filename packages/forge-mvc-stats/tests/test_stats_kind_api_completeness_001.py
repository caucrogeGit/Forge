"""STATS-KIND-API-COMPLETENESS-001 : le type d'événement traverse l'API.

`STATS-EVENT-KIND-001` a introduit un vocabulaire fermé, `page_view` et
`action`, en expliquant que mille pages vues valent moins qu'une commande passée
et que les mélanger donne un chiffre que personne ne peut interpréter.

Le champ n'a atteint que deux fonctions sur treize : les deux constructeurs SQL
de l'agrégation. Relevé avant correction :

- `make_event` et `track_event`, les portes que la documentation fait employer,
  ne le prenaient pas. Toute vue de page suivie par le chemin documenté était
  donc écrite comme une **action**, et l'agrégat que le ticket existait pour
  rendre lisible était faux.
- `count_stats_events` ne le prenait pas non plus, alors que la référence
  documentait `count_stats_events(fetch_all, group_by="name", kind="page_view")`.
  Cet appel levait une `TypeError`.
- Côté administration, la requête ne **sélectionnait** même pas la colonne : un
  écran ne pouvait ni filtrer ni afficher le type.

Principe 10 : une API publique est un contrat de complétude.
"""
from __future__ import annotations

import inspect
from typing import Any

import pytest

pytest.importorskip("forge_mvc_stats")

import forge_mvc_stats as stats  # noqa: E402
from forge_mvc_stats import (  # noqa: E402
    EVENT_KINDS,
    KIND_ACTION,
    KIND_PAGE_VIEW,
    StatsEvent,
    StatsEventError,
    count_stats_events,
    get_stats_events_admin_sql,
    list_stats_events,
    make_event,
    normalize_stats_event_row,
    track_event,
)

#: Fonctions publiques qui portent un type d'événement, écriture puis lecture.
PORTES_DU_TYPE = (
    "make_event",
    "track_event",
    "get_stats_counts_sql",
    "prepare_stats_counts_params",
    "count_stats_events",
    "get_stats_events_admin_sql",
    "prepare_stats_events_admin_params",
    "list_stats_events",
)


class _Executeur:
    def __init__(self) -> None:
        self.appels: list[tuple[str, Any]] = []

    def __call__(self, sql: str, params: Any) -> list[dict[str, Any]]:
        self.appels.append((sql, params))
        return []


@pytest.mark.parametrize("nom", PORTES_DU_TYPE)
def test_chaque_porte_publique_accepte_le_type(nom: str) -> None:
    """Deux sur treize le portaient ; c'est le trou que ce ticket ferme."""
    parametres = inspect.signature(getattr(stats, nom)).parameters

    assert "kind" in parametres, f"{nom} ne prend pas kind"


class TestEcriture:

    def test_make_event_pose_le_type_demande(self) -> None:
        assert make_event(name="accueil", kind=KIND_PAGE_VIEW).kind == KIND_PAGE_VIEW

    def test_track_event_pose_le_type_demande(self) -> None:
        """La porte documentée écrivait toute vue de page comme une action."""
        execute = _Executeur()

        evenement = track_event(execute, "accueil", kind=KIND_PAGE_VIEW)

        assert evenement.kind == KIND_PAGE_VIEW
        assert KIND_PAGE_VIEW in execute.appels[0][1]

    def test_sans_type_demande_c_est_une_action(self) -> None:
        """Le défaut ne change pas : ce ticket ajoute, il ne renomme pas."""
        assert track_event(_Executeur(), "commande").kind == KIND_ACTION

    def test_un_type_invente_est_refuse_a_l_ecriture(self) -> None:
        with pytest.raises(StatsEventError):
            track_event(_Executeur(), "accueil", kind="consultation")


class TestStatsEventDejaConstruit:
    """Ces arguments étaient ignorés en silence, ce qui écrivait autre chose."""

    @pytest.mark.parametrize("argument,valeur", [
        ("kind", KIND_PAGE_VIEW),
        ("label", "Accueil"),
        ("category", "traffic"),
        ("metadata", {"a": 1}),
    ])
    def test_joindre_un_argument_de_forme_est_refuse(
        self, argument: str, valeur: Any
    ) -> None:
        evenement = StatsEvent(name="accueil", kind=KIND_ACTION)

        with pytest.raises(StatsEventError, match=argument):
            track_event(_Executeur(), evenement, **{argument: valeur})

    def test_seul_l_evenement_passe_sans_rien_d_autre(self) -> None:
        evenement = StatsEvent(name="accueil", kind=KIND_PAGE_VIEW)

        assert track_event(_Executeur(), evenement).kind == KIND_PAGE_VIEW


class TestLecture:

    def test_l_appel_documente_de_la_reference_fonctionne(self) -> None:
        """Il levait une TypeError, et la référence le montrait pourtant."""
        count_stats_events(_Executeur(), group_by="name", kind=KIND_PAGE_VIEW)

    def test_le_filtre_atteint_le_sql(self) -> None:
        execute = _Executeur()

        count_stats_events(execute, group_by="name", kind=KIND_PAGE_VIEW)
        sql, params = execute.appels[0]

        assert "kind = ?" in sql
        assert KIND_PAGE_VIEW in params

    def test_l_administration_selectionne_la_colonne(self) -> None:
        """Sans elle, aucun écran ne peut afficher le type d'un événement."""
        assert "kind" in get_stats_events_admin_sql()

    def test_l_administration_filtre_par_type(self) -> None:
        execute = _Executeur()

        list_stats_events(execute, kind=KIND_PAGE_VIEW)
        sql, params = execute.appels[0]

        assert "kind = ?" in sql
        assert KIND_PAGE_VIEW in params

    def test_la_ligne_normalisee_porte_le_type(self) -> None:
        ligne = normalize_stats_event_row({
            "id": 1, "name": "accueil", "label": "Accueil", "category": "general",
            "metadata": None, "kind": KIND_PAGE_VIEW, "created_at": "2026-01-01",
        })

        assert ligne["kind"] == KIND_PAGE_VIEW

    def test_une_ligne_ancienne_sans_colonne_vaut_action(self) -> None:
        """Écrite avant le champ, ou par un double de test qui ne le pose pas."""
        ligne = normalize_stats_event_row({
            "id": 1, "name": "accueil", "label": "Accueil", "category": "general",
            "metadata": None, "created_at": "2026-01-01",
        })

        assert ligne["kind"] == KIND_ACTION

    @pytest.mark.parametrize("invente", ["consultation", "PAGE-VIEW", ""])
    def test_un_type_invente_est_refuse_a_la_lecture(self, invente: str) -> None:
        """Un filtre qui rend zéro sans motif fait chercher le défaut ailleurs."""
        with pytest.raises(Exception):
            list_stats_events(_Executeur(), kind=invente)


def test_le_vocabulaire_reste_ferme_a_deux() -> None:
    assert EVENT_KINDS == frozenset({KIND_PAGE_VIEW, KIND_ACTION})
