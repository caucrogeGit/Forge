"""RBAC-INSTANCE-PERMISSIONS-001 : permission portant sur une instance.

Les trois niveaux du paquet répondent tous à « cet utilisateur peut il modifier
des articles ». Aucun ne répondait à « peut il modifier **cet** article, parce
qu'il en est l'auteur ».

Chaque application réécrivait la condition à la main, et souvent de travers :
oublier que le modérateur passe outre la propriété, ou vérifier la propriété
avant la permission, donne un contrôle qui laisse passer ou qui bloque à tort.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac import (  # noqa: E402
    InstancePermissionDenied,
    has_instance_permission,
    require_instance_permission,
)

ANY = "article.edit.any"
OWN = "article.edit.own"


class Article:
    def __init__(self, auteur: str) -> None:
        self.auteur = auteur


def _can(*accordees: str):
    return lambda permission: permission in accordees


def _est_auteur(request: Any, article: Any) -> bool:
    return bool(article.auteur == request["user"])


ROGER = {"user": "roger"}
SIEN = Article("roger")
AUTRE = Article("alice")


class TestProprietaire:
    def test_l_auteur_peut_agir_sur_le_sien(self) -> None:
        assert has_instance_permission(
            ROGER, SIEN, can=_can(OWN),
            any_permission=ANY, own_permission=OWN, is_owner=_est_auteur,
        )

    def test_l_auteur_ne_peut_pas_agir_sur_celui_d_un_autre(self) -> None:
        assert not has_instance_permission(
            ROGER, AUTRE, can=_can(OWN),
            any_permission=ANY, own_permission=OWN, is_owner=_est_auteur,
        )

    def test_sans_aucun_droit_rien_n_est_permis(self) -> None:
        assert not has_instance_permission(
            ROGER, SIEN, can=_can(),
            any_permission=ANY, own_permission=OWN, is_owner=_est_auteur,
        )


class TestDroitGlobal:
    def test_le_moderateur_passe_outre_la_propriete(self) -> None:
        """Le lui refuser parce qu'il n'est pas l'auteur serait un contresens."""
        assert has_instance_permission(
            ROGER, AUTRE, can=_can(ANY),
            any_permission=ANY, own_permission=OWN, is_owner=_est_auteur,
        )

    def test_le_droit_global_n_interroge_pas_la_propriete(self) -> None:
        """Un appel de moins, souvent une requête de moins."""
        appels: list[int] = []

        has_instance_permission(
            ROGER, AUTRE, can=_can(ANY),
            any_permission=ANY, own_permission=OWN,
            is_owner=lambda r, o: bool(appels.append(1)),
        )
        assert appels == []

    def test_sans_permission_la_propriete_n_est_pas_interrogee(self) -> None:
        """Inutile d'aller en base pour qui n'a de toute façon aucun droit."""
        appels: list[int] = []

        has_instance_permission(
            ROGER, SIEN, can=_can(),
            own_permission=OWN,
            is_owner=lambda r, o: bool(appels.append(1)),
        )
        assert appels == []


class TestCompositionSeule:
    def test_sans_regle_de_propriete_le_controle_reste_global(self) -> None:
        """La composition sert aussi un contrôle ordinaire, sans cas particulier."""
        assert has_instance_permission(ROGER, SIEN, can=_can(ANY), any_permission=ANY)
        assert not has_instance_permission(ROGER, SIEN, can=_can(), any_permission=ANY)

    def test_seul_le_droit_de_proprietaire_suffit(self) -> None:
        assert has_instance_permission(
            ROGER, SIEN, can=_can(OWN), own_permission=OWN, is_owner=_est_auteur,
        )


class TestDeclarationsIncoherentes:
    def test_aucune_permission_declaree_est_refuse(self) -> None:
        """Le contrôle refuserait toujours, ce qui cacherait une faute de frappe."""
        with pytest.raises(ValueError, match="au moins une permission"):
            has_instance_permission(ROGER, SIEN, can=_can(ANY))

    def test_un_droit_de_proprietaire_sans_regle_est_refuse(self) -> None:
        """La propriété ne pourrait jamais être établie, ni le droit accordé."""
        with pytest.raises(ValueError, match="sans is_owner"):
            has_instance_permission(ROGER, SIEN, can=_can(OWN), own_permission=OWN)

    def test_le_message_dit_que_forge_ne_devine_pas(self) -> None:
        with pytest.raises(ValueError, match="ne devine pas"):
            has_instance_permission(ROGER, SIEN, can=_can(), own_permission=OWN)


class TestSourceDePermission:
    """Le module n'a pas sa propre source : il compose au dessus de celle donnée."""

    def test_la_source_est_celle_de_l_appelant(self) -> None:
        interrogees: list[str] = []

        def source(permission: str) -> bool:
            interrogees.append(permission)
            return False

        has_instance_permission(
            ROGER, SIEN, can=source,
            any_permission=ANY, own_permission=OWN, is_owner=_est_auteur,
        )
        assert interrogees == [ANY, OWN]

    def test_le_module_n_importe_aucune_source(self) -> None:
        from pathlib import Path

        from forge_mvc_rbac import instance

        source = Path(instance.__file__).read_text(encoding="utf-8")
        for interdit in ("has_contract_permission", "auth_user_can", "core.database"):
            assert interdit not in source, (
                f"{interdit} ferait de ce module un quatrième niveau"
            )


class TestLeveeExplicite:
    def test_le_refus_leve(self) -> None:
        with pytest.raises(InstancePermissionDenied):
            require_instance_permission(
                ROGER, AUTRE, can=_can(OWN),
                any_permission=ANY, own_permission=OWN, is_owner=_est_auteur,
            )

    def test_l_accord_ne_leve_pas(self) -> None:
        require_instance_permission(
            ROGER, SIEN, can=_can(OWN),
            any_permission=ANY, own_permission=OWN, is_owner=_est_auteur,
        )

    def test_le_message_nomme_les_permissions_attendues(self) -> None:
        with pytest.raises(InstancePermissionDenied, match=ANY):
            require_instance_permission(
                ROGER, AUTRE, can=_can(), any_permission=ANY, own_permission=OWN,
                is_owner=_est_auteur,
            )

    def test_aucune_reponse_http_n_est_rendue(self) -> None:
        """La forme du refus, page ou JSON, appartient à l'application."""
        from pathlib import Path

        from forge_mvc_rbac import instance

        source = Path(instance.__file__).read_text(encoding="utf-8")
        assert "Response" not in source
