"""`RBAC-DENIAL-AUDIT-COMPLETE-001` — les cinq gardes annoncent leurs refus.

`RBAC-DENIAL-AUDIT-001` a livré l'observation des refus, et sa ligne de roadmap
le dit honnêtement : « les **3** gardes annoncent ». Le paquet en compte cinq.

Les deux oubliées sont les deux qui comptent le plus.

`require_user_permission` se décrit dans sa propre docstring comme la garde
**canonique** (`SEC-RBAC-CANONICAL-GUARD-001`), celle que « les nouveaux projets
utilisent ». `require_instance_permission` refuse l'accès à l'objet d'un autre,
c'est à dire le refus qu'un exploitant veut précisément voir passer.

## Pourquoi c'est pire qu'un simple manque

Une application qui branche l'observateur sur `forge-mvc-audit` obtenait un
journal **qui paraissait complet**. Les refus contractuels y figuraient, ceux du
préfixe aussi, et ceux de la garde canonique manquaient sans que rien ne le
signale. Une énumération de droits menée contre des routes gardées par la garde
canonique ne laissait aucune trace.

La docstring de `denials.py` affirmait par ailleurs « Appelée par les gardes du
paquet », ce qui était faux pour deux d'entre elles.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest

pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac import (  # noqa: E402
    InstancePermissionDenied,
    clear_denial_observers,
    on_permission_denied,
    require_instance_permission,
    require_user_permission,
)


@pytest.fixture
def refus() -> "list[Any]":
    vus: "list[Any]" = []
    clear_denial_observers()
    on_permission_denied(vus.append)
    yield vus
    clear_denial_observers()


def _requete() -> Any:
    return SimpleNamespace(path="/factures/12", method="POST", headers={})


def _refuser_instance(requete: Any) -> None:
    require_instance_permission(
        requete, SimpleNamespace(owner_id=99),
        can=lambda permission: False,
        any_permission="facture.editer.toutes",
        own_permission="facture.editer.siennes",
        is_owner=lambda request, instance: False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# La garde canonique
# ─────────────────────────────────────────────────────────────────────────────


class TestGardeCanonique:

    def _appeler(self, requete: Any) -> Any:
        @require_user_permission(
            "facture.supprimer", permission_checker=lambda *a, **k: False)
        def route(request: Any) -> str:
            return "jamais atteint"

        with patch("forge_mvc_rbac.authorization.get_authenticated_user_id",
                   return_value=7):
            return route(requete)

    def test_le_refus_est_annonce(self, refus: "list[Any]") -> None:
        """Le manque le plus grave : c'est la garde des nouveaux projets."""
        self._appeler(_requete())

        assert len(refus) == 1

    def test_elle_refuse_toujours(self, refus: "list[Any]") -> None:
        """Annoncer ne doit rien changer à la décision."""
        assert self._appeler(_requete()).status == 403

    def test_l_evenement_nomme_la_garde(self, refus: "list[Any]") -> None:
        """`source` distingue un refus contractuel d'un refus de permissions
        chargées en base : les deux ne se corrigent pas au même endroit."""
        self._appeler(_requete())

        assert refus[0].source == "user-permissions"

    def test_l_evenement_porte_la_permission_et_la_route(
        self, refus: "list[Any]"
    ) -> None:
        self._appeler(_requete())

        assert refus[0].permission == "facture.supprimer"
        assert refus[0].path == "/factures/12"
        assert refus[0].method == "POST"

    def test_un_defaut_d_authentification_n_est_pas_un_refus_de_droit(
        self, refus: "list[Any]"
    ) -> None:
        """Un 401 dit « je ne sais pas qui vous êtes », pas « vous n'avez pas
        le droit ». Les confondre remplirait le journal d'accès de visiteurs
        anonymes et noierait les vrais refus."""
        @require_user_permission("facture.supprimer")
        def route(request: Any) -> str:
            return "jamais atteint"

        with patch("forge_mvc_rbac.authorization.get_authenticated_user_id",
                   return_value=None):
            reponse = route(_requete())

        assert reponse.status == 401
        assert refus == []

    def test_un_acces_autorise_n_annonce_rien(self, refus: "list[Any]") -> None:
        @require_user_permission(
            "facture.lire", permission_checker=lambda *a, **k: True)
        def route(request: Any) -> str:
            return "servi"

        with patch("forge_mvc_rbac.authorization.get_authenticated_user_id",
                   return_value=7):
            assert route(_requete()) == "servi"

        assert refus == []


# ─────────────────────────────────────────────────────────────────────────────
# La garde de propriété
# ─────────────────────────────────────────────────────────────────────────────


class TestGardeDePropriete:

    def test_le_refus_est_annonce(self, refus: "list[Any]") -> None:
        with pytest.raises(InstancePermissionDenied):
            _refuser_instance(_requete())

        assert len(refus) == 1

    def test_l_evenement_nomme_la_garde(self, refus: "list[Any]") -> None:
        with pytest.raises(InstancePermissionDenied):
            _refuser_instance(_requete())

        assert refus[0].source == "instance"

    def test_les_deux_permissions_demandees_sont_dites(
        self, refus: "list[Any]"
    ) -> None:
        """N'en nommer qu'une ferait chercher au mauvais endroit : le refus
        vient de ce qu'aucune des deux ne s'applique."""
        with pytest.raises(InstancePermissionDenied):
            _refuser_instance(_requete())

        assert "facture.editer.toutes" in refus[0].permission
        assert "facture.editer.siennes" in refus[0].permission

    def test_le_proprietaire_n_est_pas_annonce(self, refus: "list[Any]") -> None:
        """Un accès accordé n'est pas un refus.

        Le propriétaire doit détenir `own_permission` **et** être propriétaire :
        la propriété seule n'accorde rien, elle restreint une permission déjà
        détenue.
        """
        require_instance_permission(
            _requete(), SimpleNamespace(owner_id=7),
            can=lambda permission: permission == "facture.editer.siennes",
            own_permission="facture.editer.siennes",
            is_owner=lambda request, instance: True,
        )

        assert refus == []


# ─────────────────────────────────────────────────────────────────────────────
# L'observateur ne peut pas casser un refus
# ─────────────────────────────────────────────────────────────────────────────


class TestIsolationDeLObservateur:
    """Un refus est déjà un chemin d'erreur : transformer un 403 en 500 parce
    que la base d'audit est indisponible ferait d'un contrôle d'accès qui
    fonctionne une panne du site."""

    def test_un_observateur_qui_leve_ne_change_pas_le_403(self) -> None:
        clear_denial_observers()
        on_permission_denied(lambda e: (_ for _ in ()).throw(RuntimeError("audit HS")))
        try:
            @require_user_permission(
                "facture.supprimer", permission_checker=lambda *a, **k: False)
            def route(request: Any) -> str:
                return "jamais atteint"

            with patch("forge_mvc_rbac.authorization.get_authenticated_user_id",
                       return_value=7):
                assert route(_requete()).status == 403
        finally:
            clear_denial_observers()

    def test_un_observateur_qui_leve_ne_change_pas_la_levee(self) -> None:
        clear_denial_observers()
        on_permission_denied(lambda e: (_ for _ in ()).throw(RuntimeError("audit HS")))
        try:
            with pytest.raises(InstancePermissionDenied):
                _refuser_instance(_requete())
        finally:
            clear_denial_observers()


# ─────────────────────────────────────────────────────────────────────────────
# Aucune garde ne reste muette
# ─────────────────────────────────────────────────────────────────────────────


class TestAucuneGardeMuette:

    def test_chaque_garde_du_paquet_annonce(self) -> None:
        """Lu par `ast` : une garde ajoutée sans notification ferait un journal
        qui paraît complet et ne l'est pas.

        Ne sont visées que les fonctions `require_*` du paquet, celles qui
        produisent elles mêmes le refus. Un `has_*` rend un booléen : c'est
        l'appelant qui décide, et lui seul sait s'il refuse.
        """
        import ast
        from pathlib import Path

        paquet = Path(__file__).resolve().parents[1] / "forge_mvc_rbac"
        muettes: "list[str]" = []
        for module in sorted(paquet.rglob("*.py")):
            if "__pycache__" in module.as_posix():
                continue
            arbre = ast.parse(module.read_text(encoding="utf-8"))
            for noeud in ast.walk(arbre):
                if not isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if not noeud.name.startswith("require_"):
                    continue
                appels = {
                    n.func.id for n in ast.walk(noeud)
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                }
                if "notify_permission_denied" not in appels:
                    muettes.append(f"{module.name}:{noeud.name}")

        assert not muettes, (
            "ces gardes refusent sans annoncer, et un observateur branché sur "
            "forge-mvc-audit recevrait un journal incomplet sans le savoir :\n  "
            + "\n  ".join(muettes))
