# pyright: strict
"""IMPORT-EXPORT-CSV-ESCAPE-001 : l'export CSV ne produit plus de formule vive.

`to_csv` écrivait ses cellules telles quelles. Une cellule commençant par `=`,
`+`, `-` ou `@` redevient une formule à l'ouverture du fichier dans un tableur,
et la donnée vient le plus souvent d'un utilisateur : le fichier exporté
devenait exécutable chez celui qui le reçoit.

Le cœur portait déjà la primitive depuis `CRUD-CSV-ESCAPE-CORE-001`, né du
constat qu'une règle de sécurité recopiée dans trente-six contrôleurs finit
incomplète. `to_csv` s'y branche : la neutralisation vit à un seul endroit.

Ce que cela ne fait pas : retirer ou remplacer un caractère. Seule une
apostrophe peut être ajoutée en tête, ce qui reste lisible à la relecture.
"""
from __future__ import annotations

import csv
import io

import pytest

pytest.importorskip("forge_mvc_import_export")

from forge_mvc_import_export.csv_writer import to_csv  # noqa: E402


def _cellules(texte: str) -> "list[list[str]]":
    return list(csv.reader(io.StringIO(texte)))


@pytest.mark.parametrize("dangereuse", ["=1+1", "+1+cmd", "-1+1", "@SUM(A1)",
                                        '=HYPERLINK("http://x","clic")',
                                        "\t=cmd", "\r=cmd"])
def test_une_cellule_de_formule_sort_inerte(dangereuse: str) -> None:
    rendu = to_csv([{"a": dangereuse}], ["a"])

    valeur = _cellules(rendu)[1][0]
    assert valeur.startswith("'"), f"formule laissée vive : {valeur!r}"
    assert dangereuse.lstrip() in valeur or dangereuse in valeur


def test_une_cellule_ordinaire_n_est_pas_touchee() -> None:
    """Le cas courant doit rester intact, sans apostrophe parasite."""
    rendu = to_csv([{"a": "Bonjour", "b": "12", "c": "a=b"}], ["a", "b", "c"])

    assert _cellules(rendu)[1] == ["Bonjour", "12", "a=b"]


def test_l_en_tete_est_neutralise_aussi() -> None:
    """Un nom de colonne peut venir d'une entité, donc d'une saisie."""
    rendu = to_csv([{"=cmd": "v"}], ["=cmd"])

    assert _cellules(rendu)[0][0].startswith("'")


def test_une_valeur_absente_reste_une_cellule_vide() -> None:
    rendu = to_csv([{"a": None}], ["a", "b"])

    assert _cellules(rendu)[1] == ["", ""]


def test_le_separateur_et_les_guillemets_restent_geres_par_csv() -> None:
    """La neutralisation ne doit pas casser l'échappement CSV lui-même."""
    rendu = to_csv([{"a": 'un;deux,"trois"'}], ["a"])

    assert _cellules(rendu)[1] == ['un;deux,"trois"']


def test_l_export_passe_par_la_primitive_du_coeur() -> None:
    """Garde-fou de câblage : pas de règle recopiée dans le paquet."""
    from pathlib import Path

    import forge_mvc_import_export.csv_writer as module

    source = Path(module.__file__).read_text(encoding="utf-8")

    assert "from core.security.csv_export import escape_csv_field" in source
    assert "FORMULA_TRIGGERS" not in source, "la règle ne se recopie pas"


@pytest.mark.parametrize("nombre", ["-1", "+1", "-12", "-3.5", "-1e-3", "+33612345678"])
def test_un_nombre_sort_intact(nombre: str) -> None:
    """Un nombre ne peut pas être une formule, et l'échapper coûte cher.

    Ce fichier épinglait `+1` et `-1` comme devant être échappés. C'était la
    liste OWASP recopiée, pas un arbitrage sur les nombres : rien n'est écrit
    nulle part sur ce cas, et il a un coût mesuré
    (`CSV-NOMBRE-NEGATIF-001`).

    Tout nombre négatif d'un export devenait `'-12`, avec deux conséquences :

    - dans le tableur, la colonne des montants passait en **texte**, et les
      sommes cessaient silencieusement de compter les valeurs négatives ;
    - au réimport, la valeur revenait comme la chaîne `'-12`, qu'aucune
      conversion numérique n'accepte. Or exporter, corriger dans un tableur,
      réimporter est la raison d'être de ce module.

    L'exemption ne retire aucune protection : `-1+1` n'est pas un nombre et
    reste échappé, comme `+1+cmd`. Un tableur affiche `-12` comme moins douze,
    jamais comme un calcul.
    """
    rendu = to_csv([{"a": nombre}], ["a"])

    valeur = _cellules(rendu)[1][0]

    assert valeur == nombre, (
        f"le nombre {nombre!r} est sorti échappé en {valeur!r} : il deviendra "
        "du texte dans le tableur et refusera de se réimporter"
    )


def test_un_export_se_reimporte_a_l_identique() -> None:
    """L'aller-retour dans le sens qui compte : exporter puis relire.

    Le fichier ne testait que `parse` puis `export`. Le sens inverse est celui
    qu'un exploitant emprunte réellement : il exporte, corrige dans un tableur,
    réimporte. C'est là que l'échappement des nombres se payait, et rien ne
    l'exerçait.
    """
    from forge_mvc_import_export.csv_reader import parse_csv

    lignes = [
        {"nom": "Dupont", "solde": "-12", "note": "=1+1"},
        {"nom": "Martin", "solde": "40", "note": "ordinaire"},
    ]

    relu = parse_csv(to_csv(lignes, ["nom", "solde", "note"]))

    assert [ligne["solde"] for ligne in relu] == ["-12", "40"], (
        "les soldes ne reviennent pas tels qu'ils sont partis : une conversion "
        "numérique les refusera"
    )
    assert relu[0]["nom"] == "Dupont"
    # La formule, elle, revient neutralisée : c'est la protection qui agit, et
    # c'est le seul champ que l'aller-retour modifie légitimement.
    assert relu[0]["note"] == "'=1+1"
