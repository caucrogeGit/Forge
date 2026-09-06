"""RBAC-CONTRACT-DEGRADE-MUET-001 : un contrat non examiné ne passe plus pour sain.

`load_rbac_contract` se rabat sur un mode dégradé quand la machinerie de
validation par schéma n'est pas disponible : dossier de schémas introuvable,
registre ou validateur JSON absents.

Ce repli rendait `valid=True` sans **aucun** contrôle, sans champ pour le dire
et sans une ligne de journal. Un contrat portant un cycle d'héritage, que ce
paquet déclare pourtant inexploitable, passait donc pour sain, et `rbac:audit`
en donnait quitus.

Deux choses changent. La cohérence de la hiérarchie est vérifiée quand même :
elle est en Python pur et ne demande aucun schéma, rien ne justifiait de la
sauter. Et le mode dégradé s'annonce, dans le drapeau comme dans le journal.

Se rabattre est acceptable ; se taire ne l'est pas, et sur un contrat d'accès
moins qu'ailleurs.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

pytest.importorskip("forge_mvc_rbac")

import forge_mvc_rbac.contract as contrat  # noqa: E402

CYCLE = {
    "schema_version": "1.0",
    "roles": {"admin": [], "editeur": []},
    "role_inherits": {"admin": ["editeur"], "editeur": ["admin"]},
}
SAIN = {
    "schema_version": "1.0",
    "roles": {"admin": [], "editeur": []},
    "role_inherits": {"admin": ["editeur"]},
}


@pytest.fixture
def projet(tmp_path: Path):
    def _ecrire(donnees: dict) -> Path:
        (tmp_path / "mvc" / "security").mkdir(parents=True, exist_ok=True)
        (tmp_path / "mvc" / "security" / "rbac.json").write_text(
            json.dumps(donnees), encoding="utf-8")
        return tmp_path

    return _ecrire


class TestModeDegrade:
    """Chacune des trois portes du repli mène au même refus."""

    @pytest.mark.parametrize("cible", [
        "_find_schemas_dir", "_build_registry", "_make_validator",
    ])
    def test_un_cycle_est_vu_meme_sans_schema(self, projet, cible: str) -> None:
        racine = projet(CYCLE)

        with patch.object(contrat, cible, return_value=None):
            resultat = contrat.load_rbac_contract(racine)

        assert resultat.degraded, "le repli doit se déclarer"
        assert not resultat.valid, "un cycle ne peut pas passer pour sain"
        assert any("cycle" in e.message for e in resultat.errors)

    def test_le_repli_se_declare(self, projet) -> None:
        racine = projet(SAIN)

        with patch.object(contrat, "_find_schemas_dir", return_value=None):
            resultat = contrat.load_rbac_contract(racine)

        assert resultat.degraded

    def test_le_repli_est_journalise_avec_sa_raison(
        self, projet, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Un drapeau que personne ne lit ne vaut pas mieux que le silence."""
        racine = projet(SAIN)

        with patch.object(contrat, "_find_schemas_dir", return_value=None), \
             caplog.at_level(logging.WARNING, logger="forge.rbac"):
            contrat.load_rbac_contract(racine)

        assert "NON validé" in caplog.text
        assert "schémas introuvable" in caplog.text

    def test_un_contrat_sain_reste_accepte(self, projet) -> None:
        """Le repli ne doit pas devenir un refus général."""
        racine = projet(SAIN)

        with patch.object(contrat, "_find_schemas_dir", return_value=None):
            resultat = contrat.load_rbac_contract(racine)

        assert resultat.valid


class TestValidationNormale:
    """Ce qui marchait déjà doit continuer."""

    def test_le_cycle_est_refuse(self, projet) -> None:
        resultat = contrat.load_rbac_contract(projet(CYCLE))

        assert not resultat.valid
        assert not resultat.degraded

    def test_un_contrat_sain_passe(self, projet) -> None:
        resultat = contrat.load_rbac_contract(projet(SAIN))

        assert resultat.valid
        assert not resultat.degraded


class TestFormeDeLaHierarchie:
    """Le schéma ferme ces formes ; la couche sémantique ne les tait plus.

    `RBAC-HIERARCHY-FORME-SILENCIEUSE-001` : `validate_hierarchy` examinait la
    table **déjà normalisée**, donc jamais ce que la normalisation avait jeté.
    Sur le chemin de la CLI le schéma les refuse déjà ; en mode dégradé, il n'y
    a plus que cette couche.
    """

    @pytest.mark.parametrize("declaration,motif", [
        ({"admin": "editeur"}, "liste"),
        ({"admin": [123]}, "nom de rôle"),
    ])
    def test_une_forme_invalide_est_signalee(
        self, declaration: dict, motif: str
    ) -> None:
        from forge_mvc_rbac.hierarchy import validate_hierarchy

        problemes = validate_hierarchy({"role_inherits": declaration})

        assert problemes, "une déclaration sans effet doit être dite"
        assert motif in problemes[0]

    def test_role_inherits_qui_n_est_pas_un_objet_est_signale(self) -> None:
        from forge_mvc_rbac.hierarchy import validate_hierarchy

        assert validate_hierarchy({"role_inherits": ["admin"]})

    @pytest.mark.parametrize("declaration", [
        {"admin": ["editeur"]}, {}, {"admin": []},
    ])
    def test_une_forme_valide_ne_declenche_rien(self, declaration: dict) -> None:
        from forge_mvc_rbac.hierarchy import validate_hierarchy

        assert validate_hierarchy({"role_inherits": declaration}) == []
