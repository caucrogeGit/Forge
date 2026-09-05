"""AUDIT-RBAC-DENIALS-BRIDGE-001 : les refus d'accès entrent au journal.

`forge-mvc-rbac` annonçait ses refus, et sa documentation donnait la recette du
branchement en une ligne. Elle marche, et elle perd trois champs sur cinq :
`path` et `method` disent ce qui a été tenté, `source` nomme la garde qui a
refusé, distinction que `DenialEvent` déclare décisive puisqu'un refus
contractuel et un refus de permissions en base ne se corrigent pas au même
endroit.

Ce que fixent ces tests : le branchement porte les cinq champs, il ne se pose
qu'une fois, il ne casse pas la réponse quand la base tombe, et il tombe au
câblage plutôt qu'au premier refus quand le RBAC manque.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_audit")
pytest.importorskip("forge_mvc_rbac")

from forge_mvc_audit import (  # noqa: E402
    DENIAL_ACTION,
    DENIAL_TARGET_TYPE,
    audit_permission_denials,
    denial_details,
    permission_denials_audited,
    reset_denial_bridge,
)
from forge_mvc_rbac.denials import (  # noqa: E402
    DenialEvent,
    clear_denial_observers,
    notify_permission_denied,
)


class _DbEspion:
    """Retient les écritures. `record_audit` passe par `insert`."""

    def __init__(self) -> None:
        self.ecritures: list[tuple[str, Any]] = []

    def insert(self, sql: str, params: Any = ()) -> int:
        self.ecritures.append((sql, params))
        return len(self.ecritures)


class _DbEnPanne:
    def insert(self, sql: str, params: Any = ()) -> int:
        raise RuntimeError("base indisponible")


@pytest.fixture(autouse=True)
def _branchement_propre():
    clear_denial_observers()
    reset_denial_bridge()
    yield
    clear_denial_observers()
    reset_denial_bridge()


class _Requete:
    path = "/admin/eleves/12/supprimer"
    method = "POST"
    headers: dict[str, str] = {}


class TestBranchement:

    def test_rien_n_est_journalise_sans_branchement(self) -> None:
        """Le RBAC laisse le choix du destinataire ; l'audit ne s'impose pas."""
        espion = _DbEspion()

        notify_permission_denied("eleve.supprimer", source="contract")

        assert espion.ecritures == []
        assert not permission_denials_audited()

    def test_le_branchement_se_declare(self) -> None:
        audit_permission_denials(db=_DbEspion())

        assert permission_denials_audited()

    def test_un_refus_devient_une_ligne(self) -> None:
        espion = _DbEspion()
        audit_permission_denials(db=espion)

        notify_permission_denied("eleve.supprimer", request=_Requete(), source="contract")

        assert len(espion.ecritures) == 1

    def test_le_second_branchement_ne_double_pas_les_lignes(self) -> None:
        """Deux observateurs feraient compter les refus en double."""
        espion = _DbEspion()
        audit_permission_denials(db=espion)
        audit_permission_denials(db=espion)

        notify_permission_denied("eleve.supprimer", source="contract")

        assert len(espion.ecritures) == 1


class TestContenuDeLaLigne:

    @staticmethod
    def _parametres(espion: _DbEspion) -> Any:
        return espion.ecritures[0][1]

    def test_les_cinq_champs_du_refus_sont_portes(self) -> None:
        espion = _DbEspion()
        audit_permission_denials(db=espion)

        notify_permission_denied("eleve.supprimer", request=_Requete(), source="contract")
        params = str(self._parametres(espion))

        assert DENIAL_ACTION in params
        assert "eleve.supprimer" in params
        assert DENIAL_TARGET_TYPE in params
        assert "POST" in params
        assert "/admin/eleves/12/supprimer" in params
        assert "contract" in params

    def test_la_permission_est_la_cible_donc_filtrable(self) -> None:
        """`get_audit_log(target_type="permission")` doit suffire à les lister."""
        espion = _DbEspion()
        audit_permission_denials(db=espion)

        notify_permission_denied("note.modifier", source="user-permissions")
        params = list(self._parametres(espion))

        assert DENIAL_TARGET_TYPE in params
        assert "note.modifier" in params


class TestDetails:

    def test_le_texte_dit_ce_qui_a_ete_tente_et_par_quelle_garde(self) -> None:
        texte = denial_details(DenialEvent(
            permission="p", path="/x", method="GET", source="contract"))

        assert texte == "GET /x (garde : contract)"

    def test_un_champ_absent_est_omis_et_non_rendu_None(self) -> None:
        """Un journal ne doit pas afficher le mot None là où il n'y avait rien."""
        texte = denial_details(DenialEvent(permission="p", source="instance"))

        assert "None" not in texte
        assert texte == "(garde : instance)"

    def test_sans_rien_a_dire_le_texte_est_vide(self) -> None:
        assert denial_details(DenialEvent(permission="p")) == ""


class TestRobustesse:

    def test_une_base_en_panne_ne_transforme_pas_le_refus_en_panne(self) -> None:
        """Un contrôle d'accès qui fonctionne ne doit pas devenir une erreur 500."""
        audit_permission_denials(db=_DbEnPanne())

        notify_permission_denied("eleve.supprimer", source="contract")

    def test_un_acteur_anonyme_est_journalise_lui_aussi(self) -> None:
        """C'est souvent celui qu'on veut voir : une énumération de droits."""
        espion = _DbEspion()
        audit_permission_denials(db=espion)

        notify_permission_denied("eleve.supprimer", request=None, source="contract")

        assert len(espion.ecritures) == 1
