"""AUDIT-FILTERS-001 : borner un journal d'audit à une période.

Quatre filtres d'égalité existaient déjà, par acteur, action et cible. La
question qu'on pose le plus souvent à un journal n'avait aucune réponse : « que
s'est-il passé entre telle date et telle autre ».

Le filtre de période porte un piège silencieux, traité ici : une date seule en
borne de fin exclurait la journée entière si elle valait minuit.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

pytest.importorskip("forge_mvc_audit")

from forge_mvc_audit import AuditError, get_audit_log, iter_audit_rows  # noqa: E402


class _FauxDb:
    def __init__(self) -> None:
        self.sql: list[str] = []
        self.params: list[Any] = []

    def fetch_all(self, sql: str, params: Any) -> list[dict[str, Any]]:
        self.sql.append(sql)
        self.params.append(list(params))
        return []


def _clauses(faux: _FauxDb) -> str:
    """Clause WHERE de la requête, ou chaîne vide si la requête n'en a pas."""
    sql = faux.sql[0]
    if "WHERE" not in sql:
        return ""
    return sql[sql.index("WHERE"):sql.index("ORDER")]


def _lies(faux: _FauxDb) -> list[Any]:
    """Paramètres liés, hors la borne de pagination qui vient en dernier."""
    return faux.params[0][:-1]


class TestBornes:
    def test_les_deux_bornes_entrent_dans_la_requete(self) -> None:
        faux = _FauxDb()
        get_audit_log(since="2026-03-01 00:00:00", until="2026-03-05 23:59:59", db=faux)

        assert "created_at >= ?" in _clauses(faux)
        assert "created_at <= ?" in _clauses(faux)

    def test_les_bornes_partent_en_parametres_lies(self) -> None:
        """Une expression SQL de date ne tournerait que sur un backend."""
        faux = _FauxDb()
        get_audit_log(since="2026-03-01 00:00:00", db=faux)

        assert _lies(faux) == ["2026-03-01 00:00:00"]
        for interdit in ("NOW(", "GETDATE(", "CURRENT_TIMESTAMP", "DATE_SUB"):
            assert interdit not in faux.sql[0].upper()

    def test_une_seule_borne_est_permise(self) -> None:
        faux = _FauxDb()
        get_audit_log(since="2026-03-01 00:00:00", db=faux)

        assert "created_at >= ?" in _clauses(faux)
        assert "created_at <= ?" not in _clauses(faux)

    def test_sans_borne_aucune_clause_de_date(self) -> None:
        faux = _FauxDb()
        get_audit_log(db=faux)

        assert _clauses(faux) == "", "aucun filtre demandé, aucune clause"


class TestDateSeule:
    def test_une_date_de_debut_vaut_minuit(self) -> None:
        faux = _FauxDb()
        get_audit_log(since="2026-03-01", db=faux)

        assert _lies(faux) == ["2026-03-01 00:00:00"]

    def test_une_date_de_fin_inclut_la_journee_entiere(self) -> None:
        """Le piège du ticket : à minuit, la journée du 5 serait exclue."""
        faux = _FauxDb()
        get_audit_log(until="2026-03-05", db=faux)

        assert _lies(faux) == ["2026-03-05 23:59:59"]

    def test_une_periode_d_un_seul_jour_le_couvre_en_entier(self) -> None:
        faux = _FauxDb()
        get_audit_log(since="2026-03-05", until="2026-03-05", db=faux)

        assert _lies(faux) == ["2026-03-05 00:00:00", "2026-03-05 23:59:59"]


class TestFormesAcceptees:
    def test_un_datetime_est_accepte(self) -> None:
        """Un script manipule des dates, pas des chaînes formatées."""
        faux = _FauxDb()
        get_audit_log(since=datetime(2026, 3, 1, 14, 30, 0), db=faux)

        assert _lies(faux) == ["2026-03-01 14:30:00"]

    def test_un_horodatage_complet_est_conserve(self) -> None:
        faux = _FauxDb()
        get_audit_log(until="2026-03-05 12:00:00", db=faux)

        assert _lies(faux) == ["2026-03-05 12:00:00"]

    @pytest.mark.parametrize("vide", ["", "   "])
    def test_une_borne_vide_ne_filtre_pas(self, vide: str) -> None:
        """Un champ de formulaire laissé vide ne doit pas borner."""
        faux = _FauxDb()
        get_audit_log(since=vide, db=faux)

        assert "created_at" not in _clauses(faux)

    @pytest.mark.parametrize(
        "illisible", ["hier", "01/03/2026", "2026-13-01", "2026-03-01T14:30", "x"]
    )
    def test_une_borne_illisible_est_refusee(self, illisible: str) -> None:
        with pytest.raises(AuditError, match="illisible"):
            get_audit_log(since=illisible, db=_FauxDb())

    def test_le_refus_montre_les_formes_attendues(self) -> None:
        with pytest.raises(AuditError, match="2026-09-01"):
            get_audit_log(since="hier", db=_FauxDb())


class TestPeriodeInversee:
    def test_une_periode_inversee_est_refusee(self) -> None:
        """Zéro entrée sans motif ferait chercher un défaut ailleurs."""
        with pytest.raises(AuditError, match="période vide"):
            get_audit_log(since="2026-03-05", until="2026-03-01", db=_FauxDb())

    def test_le_refus_nomme_les_deux_bornes(self) -> None:
        with pytest.raises(AuditError, match="2026-03-05"):
            get_audit_log(since="2026-03-05", until="2026-03-01", db=_FauxDb())

    def test_des_bornes_egales_sont_permises(self) -> None:
        """Une date seule des deux côtés couvre la journée : rien d'inversé."""
        get_audit_log(since="2026-03-05", until="2026-03-05", db=_FauxDb())


class TestCombinaisonAvecLesAutresFiltres:
    def test_la_periode_s_ajoute_aux_filtres_d_egalite(self) -> None:
        faux = _FauxDb()
        get_audit_log(actor="roger", action="note.modifiee", since="2026-03-01", db=faux)

        clauses = _clauses(faux)
        assert "actor = ?" in clauses
        assert "action = ?" in clauses
        assert "created_at >= ?" in clauses
        assert clauses.count("AND") == 2


class TestExport:
    def test_l_export_accepte_aussi_la_periode(self) -> None:
        """Exporter tout le journal quand on cherche une semaine est le cas coûteux."""
        faux = _FauxDb()
        list(iter_audit_rows(since="2026-03-01", until="2026-03-05", db=faux))

        assert "created_at >= ?" in _clauses(faux)
        assert "created_at <= ?" in _clauses(faux)
