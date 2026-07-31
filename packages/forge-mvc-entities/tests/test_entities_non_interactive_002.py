"""ENTITIES-NON-INTERACTIVE-002 : declarer une relation sans terminal.

`make:relation` etait entierement interactive, sans la moindre option. Or la
contrainte de cle etrangere vient de `relations.json` (ADR-069) : tant que cette
commande exigeait un terminal, un modele relationnel complet restait hors
d'atteinte d'un script, de l'integration continue et d'un agent, alors que Forge
ecrit lui-meme la guidance des agents (ADR-047).

Suite directe de [ENTITIES-NON-INTERACTIVE-001], qui a ouvert `make:entity`.

Comme pour les champs, ce sont les **defauts** qui font l'egalite des deux
modes : s'ils differaient, la meme intention produirait deux relations selon la
facon de la formuler.
"""
from __future__ import annotations

import pytest

from forge_mvc_entities.make_relation import (
    build_relation_from_options,
    parse_relation_args,
)


def _relation(*args: str) -> dict[str, object]:
    return build_relation_from_options(parse_relation_args(list(args)))


# ── many_to_one ──────────────────────────────────────────────────────────────

def test_les_defauts_sont_ceux_du_dialogue() -> None:
    relation = _relation("--from", "Eleve", "--to", "Classe")

    assert relation == {
        "type": "many_to_one", "from": "Eleve", "to": "Classe",
        "name": "classe", "foreign_key": "classe_id",
        "nullable": True, "on_delete": "restrict", "index": True,
    }


def test_la_colonne_suit_le_nom_de_la_relation() -> None:
    """Le dialogue propose <nom>_id : la ligne de commande fait de meme."""
    relation = _relation("--from", "Eleve", "--to", "Classe", "--name", "groupe")

    assert relation["foreign_key"] == "groupe_id"


@pytest.mark.parametrize(("drapeau", "cle"), [("--not-null", "nullable"),
                                              ("--no-index", "index")])
def test_les_drapeaux_inversent_le_defaut(drapeau: str, cle: str) -> None:
    relation = _relation("--from", "Eleve", "--to", "Classe", drapeau)

    assert relation[cle] is False


def test_le_nom_inverse_n_apparait_que_s_il_est_demande() -> None:
    """Le dialogue l'omet quand la reponse est vide : ne pas ecrire une cle vide."""
    assert "inverse_name" not in _relation("--from", "Eleve", "--to", "Classe")
    assert _relation("--from", "Eleve", "--to", "Classe",
                     "--inverse-name", "eleves")["inverse_name"] == "eleves"


# ── many_to_many ─────────────────────────────────────────────────────────────

def test_le_pivot_prend_les_defauts_du_dialogue() -> None:
    relation = _relation("--type", "many_to_many", "--from", "Eleve", "--to", "Tag")

    assert relation["name"] == "tags"
    assert relation["pivot"] == {
        "table": "eleve_tag", "from_key": "eleve_id", "to_key": "tag_id",
        "id": True, "unique_pair": True, "on_delete": "cascade", "fields": [],
    }


def test_le_pivot_se_laisse_nommer() -> None:
    relation = _relation("--type", "many_to_many", "--from", "Eleve", "--to", "Tag",
                         "--pivot-table", "inscription", "--from-key", "e_id",
                         "--to-key", "t_id", "--on-delete", "restrict")
    pivot = relation["pivot"]

    assert isinstance(pivot, dict)
    assert pivot["table"] == "inscription"
    assert pivot["from_key"] == "e_id"
    assert pivot["to_key"] == "t_id"
    assert pivot["on_delete"] == "restrict"


def test_l_on_delete_par_defaut_differe_selon_le_type() -> None:
    """Le dialogue propose restrict en m2o et cascade sur le pivot : deux
    defauts distincts, qu'il faut reproduire tels quels."""
    m2o = _relation("--from", "Eleve", "--to", "Classe")
    m2m = _relation("--type", "many_to_many", "--from", "Eleve", "--to", "Tag")
    pivot = m2m["pivot"]

    assert m2o["on_delete"] == "restrict"
    assert isinstance(pivot, dict)
    assert pivot["on_delete"] == "cascade"


# ── Les refus disent quoi corriger ───────────────────────────────────────────

def test_les_deux_entites_sont_requises() -> None:
    with pytest.raises(ValueError, match="--from et --to"):
        _relation("--from", "Eleve")


def test_un_type_invalide_est_refuse() -> None:
    with pytest.raises(ValueError, match="Type de relation invalide"):
        _relation("--type", "one_to_one", "--from", "Eleve", "--to", "Classe")


def test_une_option_inconnue_est_refusee() -> None:
    with pytest.raises(ValueError, match="Option inconnue"):
        parse_relation_args(["--cardinalite", "3"])


def test_une_option_sans_valeur_est_refusee() -> None:
    with pytest.raises(ValueError, match="attend une valeur"):
        parse_relation_args(["--from"])


# ── Le mode interactif reste intact ──────────────────────────────────────────

def test_sans_argument_le_dialogue_reste_le_chemin() -> None:
    """Ouvrir un mode ne doit pas fermer l'autre (principe 11 : une seule facon
    officielle, mais le dialogue et le script visent deux usages distincts)."""
    from pathlib import Path

    import forge_mvc_entities.make_relation as module

    source = Path(module.__file__ or "").read_text(encoding="utf-8")

    assert "_build_relation_interactively(entity_map)" in source
    assert "options is None and not _prompt_yes_no" in source
