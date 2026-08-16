"""ENTITIES-PIVOT-FIELDS-001 : declarer les attributs d'un pivot par l'outillage.

`make:relation` ecrivait toujours `pivot.fields: []`, et ne posait jamais la
question, **ni en dialogue ni en ligne de commande**. Or `make:pivot-crud` exige
`pivot.fields[]` non vide et refuse sinon.

La commande etait donc inatteignable par le seul outillage : la seule facon d'y
arriver etait d'editer `mvc/entities/relations.json` a la main, ce que la
documentation disait franchement. C'etait le seul endroit ou Forge demandait
d'ecrire un contrat JSON a la main, alors qu'il fournit un generateur partout
ailleurs, et aucun agent ne pouvait modeler un pivot enrichi (ADR-047).

La grammaire n'est pas inventee : c'est celle de `make:entity --field`, posee
par ENTITIES-NON-INTERACTIVE-001. Une seconde grammaire pour la meme intention
contredirait le principe 11.

Les deux modes recoivent la capacite ensemble. N'ouvrir que la ligne de commande
creerait l'asymetrie **inverse** de celle qu'ENTITIES-NON-INTERACTIVE-002 a
corrigee, le mode non interactif sachant alors ce que le dialogue ignore.
"""
from __future__ import annotations

from typing import Any, cast

import pytest

pytest.importorskip("forge_mvc_entities")

from forge_mvc_entities.make_relation import (  # noqa: E402
    build_relation_from_options,
    parse_relation_args,
)


#: Les deux entites que le dialogue propose ; leur contenu importe peu ici,
#: seule leur presence dans la liste des noms connus compte.
_ENTITES: dict[str, dict[str, object]] = {"Article": {}, "Tag": {}}


def _pivot(*args: str) -> dict[str, Any]:
    relation = build_relation_from_options(
        parse_relation_args(["--type", "many_to_many", "--from", "Article",
                             "--to", "Tag", *args])
    )
    pivot = relation["pivot"]
    assert isinstance(pivot, dict)
    return cast("dict[str, Any]", pivot)


def _champs(*args: str) -> list[dict[str, Any]]:
    """Les attributs du pivot, typés : `_pivot()` rend le bloc entier.

    Distinction qui m'a coûté un échec : itérer `_pivot(...)` parcourt les clés
    du bloc pivot, pas ses attributs.
    """
    champs = _pivot(*args)["fields"]
    assert isinstance(champs, list)
    return cast("list[dict[str, Any]]", champs)


# ── Ligne de commande ────────────────────────────────────────────────────────

def test_sans_option_le_pivot_reste_sans_attribut() -> None:
    """Le defaut ne change pas : un pivot simple reste simple.

    C'est ce qui distingue `make:crud` de `make:pivot-crud`, et l'ouvrir par
    defaut ferait basculer des relations existantes vers l'autre generateur.
    """
    assert _pivot()["fields"] == []


def test_un_attribut_se_declare_en_ligne_de_commande() -> None:
    champs = _champs("--pivot-field", "position:integer")

    assert champs == [
        {"name": "position", "type": "integer",
         "required": True, "nullable": False, "unique": False}
    ]


def test_les_attributs_gardent_leur_ordre() -> None:
    """L'ordre est celui de la ligne de commande : il decide des colonnes."""
    champs = _champs("--pivot-field", "position:integer",
                     "--pivot-field", "note:string:max_length=200,optional")

    assert [c["name"] for c in champs] == ["position", "note"]


def test_la_grammaire_est_celle_des_champs_d_entite() -> None:
    """Memes attributs, memes defauts : une seule grammaire a apprendre."""
    from forge_mvc_entities.make_entity import parse_field_spec

    spec = "note:string:max_length=200,optional,unique"
    assert _champs("--pivot-field", spec) == [parse_field_spec(spec)]


# ── Ce que le pivot n'admet pas ──────────────────────────────────────────────

@pytest.mark.parametrize("forge_type", ["foreign_key", "slug"])
def test_les_types_hors_pivot_sont_refuses_tot(forge_type: str) -> None:
    """Deux des quatorze types d'entite n'ont pas de sens sur une association.

    La cle etrangere est deja portee par `from_key` et `to_key`, et un slug
    designe une ressource, pas un lien. Le refus vient de la commande, avec la
    raison : laisser passer ferait echouer la validation plus loin, sur un
    message qui ne dirait pas pourquoi.
    """
    with pytest.raises(ValueError, match="pivot"):
        _pivot("--pivot-field", f"x:{forge_type}")


@pytest.mark.parametrize("nom", ["id", "article_id", "tag_id"])
def test_les_noms_geres_par_forge_sont_refuses_tot(nom: str) -> None:
    """`id`, `from_key` et `to_key` appartiennent a Forge (schema pivot).

    Les redeclarer produirait une colonne en double, refusee par le moteur bien
    apres la commande.
    """
    with pytest.raises(ValueError, match=nom):
        _pivot("--pivot-field", f"{nom}:integer")


def test_l_option_est_refusee_sur_une_relation_many_to_one() -> None:
    """Un many_to_one n'a pas de pivot : accepter l'option serait un silence."""
    with pytest.raises(ValueError, match="many_to_many"):
        build_relation_from_options(
            parse_relation_args(["--from", "Eleve", "--to", "Classe",
                                 "--pivot-field", "position:integer"])
        )


# ── Dialogue ─────────────────────────────────────────────────────────────────

def test_le_dialogue_propose_aussi_les_attributs() -> None:
    """Les deux modes savent la meme chose, sans quoi l'asymetrie s'inverse."""
    from forge_mvc_entities.make_relation import _build_relation_interactively

    reponses = iter([
        "many_to_many",   # type
        "Article",        # from
        "Tag",            # to
        "tags",           # nom
        "",               # nom inverse
        "article_tag",    # table pivot
        "article_id",     # from_key
        "tag_id",         # to_key
        "cascade",        # on delete
        "position:integer",  # premier attribut
        "",               # fin des attributs
    ])
    relation = _build_relation_interactively(_ENTITES, input_fn=lambda _: next(reponses))

    pivot = relation["pivot"]
    assert isinstance(pivot, dict)
    assert pivot["fields"] == [
        {"name": "position", "type": "integer",
         "required": True, "nullable": False, "unique": False}
    ]


def test_le_dialogue_sans_attribut_laisse_le_pivot_simple() -> None:
    """Repondre vide d'emblee doit rendre exactement l'ancien comportement."""
    from forge_mvc_entities.make_relation import _build_relation_interactively

    reponses = iter([
        "many_to_many", "Article", "Tag", "tags", "",
        "article_tag", "article_id", "tag_id", "cascade",
        "",  # aucun attribut
    ])
    relation = _build_relation_interactively(_ENTITES, input_fn=lambda _: next(reponses))

    pivot = relation["pivot"]
    assert isinstance(pivot, dict)
    assert pivot["fields"] == []
