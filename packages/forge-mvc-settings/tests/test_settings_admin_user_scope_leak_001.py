"""SETTINGS-ADMIN-USER-SCOPE-LEAK-001 : l'écran n'affiche plus les comptes.

`get_all_settings` excluait déjà l'espace `user.`, et sa docstring nommait le
danger : « un écran de réglages afficherait les préférences de tout le monde ».
La garde manquait sur `get_settings_with_types`, qui est précisément la porte
que `describe_settings` emprunte, donc l'écran de réglages.

Mesuré avant correction, sur une base SQLite montée par la DDL du framework :
`describe_settings()` rendait `user.42.theme` et `user.7.notifications_email`,
adresse électronique comprise, et l'écran documenté les offrait à l'édition.

Le refus d'**écriture** tenait, lui : `set_setting` rejette le préfixe réservé.
Ce test fixe les deux moitiés, parce que seule la lecture avait cédé et qu'un
correctif ne doit pas emporter l'autre en passant.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_settings")

from forge_mvc_settings import (  # noqa: E402
    USER_SCOPE_PREFIX,
    SettingsError,
    describe_settings,
    get_all_settings,
    get_settings_with_types,
    set_setting,
    user_setting_key,
)


class _FauxDb:
    """Rend les lignes telles que la table les porte, portées mêlées."""

    def __init__(self, lignes: list[dict[str, Any]]) -> None:
        self._lignes = lignes

    def fetch_all(self, sql: str, params: Any = ()) -> list[dict[str, Any]]:
        return self._lignes


def _table_melangee() -> _FauxDb:
    return _FauxDb([
        {"setting_key": "site_name", "setting_value": "Lycee Diderot", "value_type": "str"},
        {"setting_key": "maintenance", "setting_value": "1", "value_type": "bool"},
        {"setting_key": "user.42.theme", "setting_value": "sombre", "value_type": "str"},
        {"setting_key": "user.7.notifications_email",
         "setting_value": "prive@exemple.fr", "value_type": "str"},
    ])


class TestLecture:

    def test_l_ecran_ne_voit_que_les_parametres_globaux(self) -> None:
        lignes = describe_settings(db=_table_melangee())

        assert [ligne.key for ligne in lignes] == ["maintenance", "site_name"]

    def test_aucune_valeur_d_utilisateur_ne_transite(self) -> None:
        """La clé filtrée ne suffit pas : c'est la valeur qui fuyait."""
        valeurs = [str(ligne.value) for ligne in describe_settings(db=_table_melangee())]

        assert not any("prive@exemple.fr" in v for v in valeurs)

    def test_le_listing_type_exclut_l_espace_utilisateur(self) -> None:
        cles = [cle for cle, _, _ in get_settings_with_types(db=_table_melangee())]

        assert not any(cle.startswith(USER_SCOPE_PREFIX) for cle in cles)

    def test_les_deux_portes_de_lecture_s_accordent(self) -> None:
        """Une seule des deux filtrait, et c'est ce désaccord qui a fait le trou."""
        db = _table_melangee()

        assert sorted(get_all_settings(db=db)) == sorted(
            cle for cle, _, _ in get_settings_with_types(db=db))

    def test_le_type_declare_survit_au_filtrage(self) -> None:
        """Filtrer ne doit pas coûter la raison d'être de cette fonction."""
        types = {cle: t for cle, _, t in get_settings_with_types(db=_table_melangee())}

        assert types == {"site_name": "str", "maintenance": "bool"}


class TestEcriture:

    def test_l_ecran_ne_peut_pas_ecrire_dans_l_espace_d_un_compte(self) -> None:
        with pytest.raises(SettingsError, match="réservée"):
            set_setting(user_setting_key(42, "theme"), "clair", db=_table_melangee())
