"""SETTINGS-JSON-TYPE-001 : un paramètre peut porter une valeur composite.

Les types déclarés s'arrêtaient à `str`, `int`, `bool` et `float`. Une liste
d'extensions permises ou une plage d'horaires n'avait donc pas de place : on la
sérialisait à la main dans une chaîne, et le type déclaré mentait.

Le type refuse les **scalaires**, et ce refus est le cœur du ticket. Le store
déduit le type de la valeur : un `42` déclaré `json` reviendrait `int` au
premier enregistrement depuis un écran, le type changeant sans que personne ne
l'ait demandé. Les scalaires ont déjà le leur.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_settings")

from forge_mvc_settings import (  # noqa: E402
    SUPPORTED_TYPES,
    SettingsError,
    describe_settings,
    parse_setting_value,
)
from forge_mvc_settings.store import _coerce, _serialize  # noqa: E402


class _FauxDb:
    def __init__(self, lignes: list[dict[str, Any]]) -> None:
        self._lignes = lignes

    def fetch_all(self, sql: str, params: Any = ()) -> list[dict[str, Any]]:
        return self._lignes


def test_json_figure_parmi_les_types_declares() -> None:
    assert "json" in SUPPORTED_TYPES


class TestAllerRetour:

    @pytest.mark.parametrize("valeur", [
        ["pdf", "odt"],
        [],
        {"lundi": "8h-17h"},
        {},
        {"places": 30, "ouvert": True, "niveaux": ["2nde", "1re"]},
    ])
    def test_la_valeur_revient_identique(self, valeur: Any) -> None:
        texte, type_declare = _serialize(valeur)

        assert type_declare == "json"
        assert _coerce(texte, "json") == valeur

    def test_les_accents_restent_lisibles_en_base(self) -> None:
        """La charte veut le contenu auditable à l'œil, pas en séquences \\u."""
        texte, _ = _serialize({"élève": "présent"})

        assert "élève" in texte

    def test_le_texte_stocke_est_stable(self) -> None:
        """Deux écritures du même contenu ne produisent pas deux lignes différentes."""
        premier, _ = _serialize({"b": 1, "a": 2})
        second, _ = _serialize({"a": 2, "b": 1})

        assert premier == second


class TestSaisieDepuisUnEcran:

    @pytest.mark.parametrize("saisie,attendu", [
        ('["pdf", "odt"]', ["pdf", "odt"]),
        ('{"lundi": "8h-17h"}', {"lundi": "8h-17h"}),
        ('  {"a": 1}  ', {"a": 1}),
    ])
    def test_une_saisie_valide_donne_la_valeur(self, saisie: str, attendu: Any) -> None:
        assert parse_setting_value(saisie, "json") == attendu

    @pytest.mark.parametrize("saisie", ['{"a": 1', "[1, 2", "n'importe quoi"])
    def test_une_saisie_malformee_est_refusee_explicitement(self, saisie: str) -> None:
        """Jamais une ValueError nue : une page attend un refus de formulaire."""
        with pytest.raises(SettingsError, match="json invalide"):
            parse_setting_value(saisie, "json")

    @pytest.mark.parametrize("saisie", ["42", '"texte"', "true", "null", "3.5"])
    def test_un_scalaire_est_refuse(self, saisie: str) -> None:
        with pytest.raises(SettingsError, match="scalaire"):
            parse_setting_value(saisie, "json")


class TestRetourAuFormulaire:

    def test_le_champ_porte_du_json_relisible(self) -> None:
        """`str(dict)` rendrait des apostrophes simples, que la saisie refuse."""
        db = _FauxDb([{"setting_key": "horaires",
                       "setting_value": '{"lundi": "8h-17h"}', "value_type": "json"}])

        ligne = describe_settings(db=db)[0]

        assert ligne.raw == '{"lundi": "8h-17h"}'
        assert parse_setting_value(ligne.raw, "json") == ligne.value


class TestLectureAbimee:

    def test_une_ligne_illisible_le_dit(self) -> None:
        """Modifiée à la main en base, elle ne doit pas remonter en ValueError nue."""
        with pytest.raises(SettingsError, match="illisible"):
            _coerce("{pas du json", "json")
