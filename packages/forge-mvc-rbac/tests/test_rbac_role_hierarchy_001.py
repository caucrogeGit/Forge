"""`RBAC-ROLE-HIERARCHY-001` (ADR-095) — l'héritage entre rôles.

Le contrat associait un rôle à une liste plate de permissions. Un projet à
trois rôles recopiait donc la liste du lecteur dans l'éditeur, puis les deux
dans l'admin.

Trois copies de la même règle, qui divergent au premier ajout : on ajoute une
permission à l'éditeur, on oublie l'admin, et l'administrateur se retrouve avec
**moins** de droits qu'un éditeur. Personne n'écrit un test vérifiant qu'un
administrateur peut faire ce qu'un éditeur peut faire.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac.contract import (  # noqa: E402
    RbacContractResult,
    get_contract_permissions,
)
from forge_mvc_rbac.export import to_markdown  # noqa: E402
from forge_mvc_rbac.hierarchy import (  # noqa: E402
    MAX_INHERITANCE_DEPTH,
    RoleHierarchyError,
    detect_cycle,
    expand_roles,
    inheritance_map,
    validate_hierarchy,
)

_TROIS_ROLES: "dict[str, Any]" = {
    "roles": {
        "lecteur": ["article.list"],
        "editeur": ["article.create"],
        "admin": ["article.destroy"],
    },
    "role_inherits": {"admin": ["editeur"], "editeur": ["lecteur"]},
}


def _resultat(contrat: "dict[str, Any]") -> RbacContractResult:
    return RbacContractResult(valid=True, exists=True, path="rbac.json", data=contrat)


class TestResolution:

    def test_l_heritage_est_transitif(self) -> None:
        """L'administrateur porte les droits de l'éditeur ET du lecteur."""
        permissions = get_contract_permissions(_resultat(_TROIS_ROLES), ["admin"])

        assert permissions == {"article.list", "article.create", "article.destroy"}

    def test_chaque_niveau_garde_les_siens(self) -> None:
        resultat = _resultat(_TROIS_ROLES)

        assert get_contract_permissions(resultat, ["editeur"]) == {
            "article.list", "article.create"
        }
        assert get_contract_permissions(resultat, ["lecteur"]) == {"article.list"}

    def test_sans_heritage_le_comportement_est_celui_d_avant(self) -> None:
        """Aucun projet existant n'a de geste à faire."""
        contrat = {"roles": {"admin": ["a.x"], "lecteur": ["a.y"]}}

        assert get_contract_permissions(_resultat(contrat), ["admin"]) == {"a.x"}

    def test_plusieurs_roles_portes_se_reunissent(self) -> None:
        contrat = {
            "roles": {"a": ["p.a"], "b": ["p.b"], "socle": ["p.socle"]},
            "role_inherits": {"a": ["socle"], "b": ["socle"]},
        }

        assert get_contract_permissions(_resultat(contrat), ["a", "b"]) == {
            "p.a", "p.b", "p.socle"
        }

    def test_deux_branches_qui_ne_se_dominent_pas(self) -> None:
        """Un ordre total imposerait une hiérarchie que le métier n'a pas."""
        contrat = {
            "roles": {"comptable": ["c.x"], "editeur": ["e.x"], "lecteur": ["l.x"]},
            "role_inherits": {"comptable": ["lecteur"], "editeur": ["lecteur"]},
        }
        resultat = _resultat(contrat)

        assert "e.x" not in get_contract_permissions(resultat, ["comptable"])
        assert "c.x" not in get_contract_permissions(resultat, ["editeur"])


class TestCycle:

    def test_il_est_detecte(self) -> None:
        table = inheritance_map({"role_inherits": {"a": ["b"], "b": ["a"]}})

        assert detect_cycle(table) is not None

    def test_il_est_nomme(self) -> None:
        """« admin puis editeur puis admin » se corrige, « hiérarchie
        invalide » ne se corrige pas."""
        table = inheritance_map(
            {"role_inherits": {"admin": ["editeur"], "editeur": ["admin"]}}
        )
        cycle = detect_cycle(table)

        assert cycle is not None
        assert "admin" in cycle and "editeur" in cycle

    def test_un_role_qui_herite_de_lui_meme_est_un_cycle(self) -> None:
        problemes = validate_hierarchy(
            {"roles": {"a": []}, "role_inherits": {"a": ["a"]}}
        )

        assert any("lui même" in p for p in problemes)

    def test_une_hierarchie_saine_n_a_pas_de_cycle(self) -> None:
        assert detect_cycle(inheritance_map(_TROIS_ROLES)) is None

    def test_expand_leve_sur_un_cycle(self) -> None:
        table = inheritance_map({"role_inherits": {"a": ["b"], "b": ["a"]}})

        with pytest.raises(RoleHierarchyError, match="cycle"):
            expand_roles(["a"], table)


class TestRefusSilencieux:
    """Les deux refus qui évitent une dégradation invisible."""

    def test_une_hierarchie_fautive_n_accorde_rien(self) -> None:
        """Accorder les droits directs en ignorant l'héritage donnerait un
        contrôle d'accès dégradé sans que rien ne le signale."""
        contrat = {
            "roles": {"admin": ["a.destroy"], "editeur": ["a.create"]},
            "role_inherits": {"admin": ["editeur"], "editeur": ["admin"]},
        }

        assert get_contract_permissions(_resultat(contrat), ["admin"]) == set()

    def test_un_role_herite_inconnu_est_signale(self) -> None:
        """Une faute de frappe n'accorderait rien du tout, et la cause serait
        introuvable dans un fichier de cinquante lignes."""
        problemes = validate_hierarchy(
            {"roles": {"admin": []}, "role_inherits": {"admin": ["editur"]}}
        )

        assert any("editur" in p for p in problemes)

    def test_un_heritier_absent_de_roles_est_signale(self) -> None:
        problemes = validate_hierarchy(
            {"roles": {"lecteur": []}, "role_inherits": {"fantome": ["lecteur"]}}
        )

        assert any("fantome" in p for p in problemes)

    def test_une_hierarchie_saine_ne_signale_rien(self) -> None:
        assert validate_hierarchy(_TROIS_ROLES) == []

    def test_un_contrat_sans_heritage_ne_signale_rien(self) -> None:
        assert validate_hierarchy({"roles": {"a": []}}) == []


class TestProfondeur:

    def test_elle_est_bornee(self) -> None:
        """Au delà, une revue de sécurité ne peut plus suivre la chaîne."""
        chaine = {
            f"r{i}": (f"r{i + 1}",) for i in range(MAX_INHERITANCE_DEPTH + 3)
        }

        with pytest.raises(RoleHierarchyError, match="niveaux"):
            expand_roles(["r0"], chaine)

    def test_juste_en_dessous_c_est_permis(self) -> None:
        chaine = {f"r{i}": (f"r{i + 1}",) for i in range(MAX_INHERITANCE_DEPTH - 1)}

        assert len(expand_roles(["r0"], chaine)) == MAX_INHERITANCE_DEPTH


class TestRienN_estDeduit:

    def test_aucune_hierarchie_n_est_deduite_d_un_nom(self) -> None:
        """« admin » ne domine pas « editeur » parce qu'il s'appelle ainsi.

        Une déduction fausse sur un contrôle d'accès ne se répare pas après
        coup.
        """
        contrat = {"roles": {"admin": ["a.x"], "editeur": ["e.x"]}}

        assert get_contract_permissions(_resultat(contrat), ["admin"]) == {"a.x"}

    def test_la_cle_est_facultative(self) -> None:
        assert inheritance_map({"roles": {"a": []}}) == {}

    def test_une_declaration_mal_formee_est_ignoree(self) -> None:
        assert inheritance_map({"role_inherits": "pas un objet"}) == {}


class TestExport:

    def test_il_rend_les_permissions_effectives(self) -> None:
        """Rendre les seules permissions directes ferait croire à un
        administrateur privé de droits qu'il possède, et c'est exactement ce
        qu'une revue de sécurité ne doit pas conclure.
        """
        contrat = {
            "roles": {
                "lecteur": {"Article": ["index"]},
                "editeur": {"Article": ["create"]},
                "admin": {"User": ["destroy"]},
            },
            "role_inherits": {"admin": ["editeur"], "editeur": ["lecteur"]},
        }

        rendu = to_markdown(contrat)

        assert "| `admin` | `Article` | create, index |" in rendu
        assert "| `admin` | `User` | destroy |" in rendu

    def test_les_actions_se_reunissent_par_entite(self) -> None:
        """Remplacer le bloc d'une entité ferait perdre les actions propres au
        rôle héritier."""
        contrat = {
            "roles": {"base": {"A": ["lire"]}, "sup": {"A": ["ecrire"]}},
            "role_inherits": {"sup": ["base"]},
        }

        assert "| `sup` | `A` | ecrire, lire |" in to_markdown(contrat)

    def test_sans_heritage_l_export_est_inchange(self) -> None:
        rendu = to_markdown({"roles": {"a": {"A": ["x"]}}})

        assert "| `a` | `A` | x |" in rendu
