"""`ADMIN-BULK-ACTIONS-001` — supprimer plusieurs lignes en une fois.

Le back-office ne savait supprimer qu'une ligne à la fois : nettoyer deux cents
inscriptions de test demandait deux cents allers-retours, et deux cents
confirmations.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_admin")

from forge_mvc_admin.query import (  # noqa: E402
    BULK_MAX_ROWS,
    BulkActionError,
    delete_rows,
)
from forge_mvc_admin.resources import AdminResource  # noqa: E402


@pytest.fixture
def ressource() -> AdminResource:
    return AdminResource(
        entity="User", slug="u", label="Utilisateur", plural_label="Utilisateurs",
        list_fields=("id",), form_fields=("id",), table="users",
    )


class _Executeur:
    def __init__(self, affectees: "int | None" = None) -> None:
        self.appels: "list[tuple[str, tuple[Any, ...]]]" = []
        self.affectees = affectees

    def __call__(self, sql: str, params: "tuple[Any, ...]") -> int:
        self.appels.append((sql, params))
        return len(params) if self.affectees is None else self.affectees


class TestSuppressionGroupee:

    def test_une_seule_requete(self, ressource: AdminResource) -> None:
        executeur = _Executeur()

        delete_rows(ressource, executeur, pk_values=[1, 2, 3])

        assert len(executeur.appels) == 1

    def test_les_identifiants_partent_en_parametres_lies(
        self, ressource: AdminResource
    ) -> None:
        """Les concaténer serait une injection, et le fait qu'ils viennent de
        cases cochées n'y change rien : une case cochée est une donnée de
        requête comme une autre."""
        executeur = _Executeur()

        delete_rows(ressource, executeur, pk_values=[1, 2, 3])

        sql, params = executeur.appels[0]
        assert sql.count("?") == 3
        assert params == (1, 2, 3)
        assert "1, 2, 3" not in sql

    def test_une_valeur_hostile_ne_touche_pas_le_sql(
        self, ressource: AdminResource
    ) -> None:
        executeur = _Executeur()

        delete_rows(ressource, executeur, pk_values=["1); DROP TABLE users; --"])

        sql, params = executeur.appels[0]
        assert "DROP" not in sql
        assert params == ("1); DROP TABLE users; --",)

    def test_la_cle_primaire_de_la_ressource_est_employee(
        self, ressource: AdminResource
    ) -> None:
        executeur = _Executeur()

        delete_rows(ressource, executeur, pk_values=[1])

        assert f"WHERE {ressource.pk} IN" in executeur.appels[0][0]

    def test_le_nombre_reellement_supprime_est_rendu(
        self, ressource: AdminResource
    ) -> None:
        """Une ligne supprimée entre l'affichage et la validation n'est pas une
        erreur, et refuser toute la fournée pour cela ferait échouer une action
        correcte."""
        assert delete_rows(ressource, _Executeur(affectees=2), pk_values=[1, 2, 3]) == 2


class TestRefus:

    def test_une_selection_vide_est_refusee(self, ressource: AdminResource) -> None:
        """Une suppression groupée sans sélection effacerait la table entière
        si la clause était omise."""
        executeur = _Executeur()

        with pytest.raises(BulkActionError, match="aucune ligne"):
            delete_rows(ressource, executeur, pk_values=[])

        assert executeur.appels == []

    def test_au_dela_du_plafond_c_est_refuse(self, ressource: AdminResource) -> None:
        """Une sélection de cette taille vient plus souvent d'un « tout cocher »
        malencontreux que d'une intention."""
        with pytest.raises(BulkActionError, match="plafond"):
            delete_rows(
                ressource, _Executeur(), pk_values=list(range(BULK_MAX_ROWS + 1))
            )

    def test_pile_au_plafond_c_est_permis(self, ressource: AdminResource) -> None:
        executeur = _Executeur()

        delete_rows(ressource, executeur, pk_values=list(range(BULK_MAX_ROWS)))

        assert len(executeur.appels) == 1

    def test_le_plafond_se_regle(self, ressource: AdminResource) -> None:
        with pytest.raises(BulkActionError):
            delete_rows(ressource, _Executeur(), pk_values=[1, 2, 3], max_rows=2)
