"""RBAC-EXPORT-FORME-CONTRAT-001 : l'export lit la forme que le schéma impose.

`contract_rows` lisait `roles` comme une table `rôle -> entité -> actions`.
Le schéma, qui fait autorité et que `rbac:audit` applique, déclare
`rôle -> liste de codes de permission`.

Les deux ne se rencontraient jamais. Chaque rôle était écarté, et
`forge rbac:export` rendait « Aucun rôle déclaré » sur **tout** contrat valide,
c'est à dire sur tous.

Ce qui a laissé vivre le défaut : le test de l'export employait la forme que le
schéma interdit. La fonction passait donc au vert sur une donnée qu'aucun
projet ne peut produire.

Le contrôle décisif est ici formulé comme la fin visée : **un contrat accepté
par le schéma produit un export non vide**. Il ne fige aucune forme, et tomberait
de nouveau si les deux repartaient chacune de leur côté.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac.export import contract_rows, to_csv, to_markdown  # noqa: E402

#: Contrat minimal, écrit comme le schéma l'exige.
CONTRAT: "dict[str, Any]" = {
    "schema_version": "1.0",
    "roles": {
        "lecteur": ["article.lire"],
        "editeur": ["article.publier"],
        "admin": ["article.supprimer"],
    },
    "role_inherits": {"admin": ["editeur"], "editeur": ["lecteur"]},
    "entities": {
        "Article": {
            "permissions": {
                "lire": "article.lire",
                "publier": "article.publier",
                "supprimer": "article.supprimer",
            }
        }
    },
}


def _valide_au_schema(contrat: "dict[str, Any]") -> bool:
    """Le contrat passe-t-il le schéma embarqué du paquet ?"""
    jsonschema = pytest.importorskip("jsonschema")
    chemin = Path(__file__).resolve().parents[1] / "forge_mvc_rbac" / "schemas"
    schema = json.loads((chemin / "rbac.schema.json").read_text(encoding="utf-8"))
    validateur = jsonschema.Draft202012Validator(schema)
    return not list(validateur.iter_errors(contrat))


class TestLeContratDEssaiEstRealiste:
    """Sans cela, tout le reste du fichier prouverait quelque chose d'autre."""

    def test_il_passe_le_schema(self) -> None:
        assert _valide_au_schema(CONTRAT)

    def test_l_ancienne_forme_ne_le_passe_pas(self) -> None:
        """C'est celle que le test de l'export employait."""
        ancienne = {
            "schema_version": "1.0",
            "roles": {"admin": {"Article": ["index"]}},
        }

        assert not _valide_au_schema(ancienne)


class TestUnContratValideProduitUnExport:

    def test_les_lignes_ne_sont_pas_vides(self) -> None:
        """Le contrôle décisif : c'est ce que le défaut rendait faux."""
        assert contract_rows(CONTRAT)

    def test_le_markdown_ne_dit_pas_qu_il_n_y_a_rien(self) -> None:
        assert "Aucun rôle déclaré" not in to_markdown(CONTRAT)

    def test_le_csv_porte_plus_que_son_en_tete(self) -> None:
        assert len(to_csv(CONTRAT).strip().splitlines()) > 1

    def test_chaque_role_declare_apparait(self) -> None:
        roles_rendus = {ligne[0] for ligne in contract_rows(CONTRAT)}

        assert roles_rendus == {"lecteur", "editeur", "admin"}


class TestLHeritageEstRendu:
    """Rendre les seules permissions directes ferait croire un administrateur
    privé de droits qu'il possède."""

    def test_l_administrateur_herite_de_tout(self) -> None:
        actions = {a for r, _e, a in contract_rows(CONTRAT) if r == "admin"}

        assert actions == {"lire", "publier", "supprimer"}

    def test_le_lecteur_n_herite_de_rien(self) -> None:
        actions = {a for r, _e, a in contract_rows(CONTRAT) if r == "lecteur"}

        assert actions == {"lire"}


class TestPermissionOrpheline:

    def test_une_permission_sans_entite_reste_visible(self) -> None:
        """La taire ferait disparaître d'une revue un droit pourtant accordé."""
        from forge_mvc_rbac.export import SANS_ENTITE

        contrat = dict(CONTRAT)
        contrat["roles"] = dict(CONTRAT["roles"], veilleur=["article.inconnue"])

        lignes = contract_rows(contrat)

        assert ("veilleur", SANS_ENTITE, "article.inconnue") in lignes
