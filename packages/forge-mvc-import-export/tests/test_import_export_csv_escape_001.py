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


@pytest.mark.parametrize("dangereuse", ["=1+1", "+1", "-1", "@SUM(A1)",
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
