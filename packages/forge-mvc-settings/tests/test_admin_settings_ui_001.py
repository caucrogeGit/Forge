"""ADMIN-SETTINGS-UI-001 : éditer les paramètres depuis un écran.

Un paramètre porte une valeur **et** son type, et le store déduit le second de
la première. Une page web ne reçoit que du texte, ce qui ouvrait trois pièges.

Brancher un CRUD générique sur la table ferait saisir le type à la main : une
incohérence, `value_type=int` sur une valeur `abc`, casse toute lecture
ultérieure.

Convertir avec `int(saisie)` lève une `ValueError` nue, donc une erreur cinq
cents là où l'appelant attendait un refus de formulaire.

Et une valeur booléenne se lit `text == "1"` : taper `oui` y enregistre
**faux**, en silence. L'exploitant croit avoir activé une option.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("forge_mvc_settings")

from forge_mvc_settings import (  # noqa: E402
    SettingsError,
    describe_settings,
    parse_setting_value,
)


class _FauxDb:
    def __init__(self, lignes: list[dict[str, Any]]) -> None:
        self._lignes = lignes

    def fetch_all(self, sql: str, params: Any) -> list[dict[str, Any]]:
        return self._lignes


class TestSaisieBooleenne:
    """Le piège le plus silencieux : `oui` enregistrait faux."""

    @pytest.mark.parametrize(
        "saisie", ["1", "true", "vrai", "oui", "yes", "on", "VRAI", "  Oui  "]
    )
    def test_les_ecritures_de_vrai_sont_reconnues(self, saisie: str) -> None:
        assert parse_setting_value(saisie, "bool") is True

    @pytest.mark.parametrize(
        "saisie", ["0", "false", "faux", "non", "no", "off", "NON", " faux "]
    )
    def test_les_ecritures_de_faux_sont_reconnues(self, saisie: str) -> None:
        assert parse_setting_value(saisie, "bool") is False

    @pytest.mark.parametrize("saisie", ["peut-etre", "2", "", "   ", "oui non"])
    def test_une_saisie_ambigue_est_refusee_et_non_prise_pour_faux(
        self, saisie: str
    ) -> None:
        """Sans refus, l'exploitant croirait avoir activé une option."""
        with pytest.raises(SettingsError, match="booléenne"):
            parse_setting_value(saisie, "bool")

    def test_le_refus_enumere_les_saisies_acceptees(self) -> None:
        with pytest.raises(SettingsError, match="vrai"):
            parse_setting_value("peut-etre", "bool")


class TestSaisieNumerique:
    def test_un_entier_valide_passe(self) -> None:
        assert parse_setting_value("8000", "int") == 8000

    def test_un_flottant_valide_passe(self) -> None:
        assert parse_setting_value("1.5", "float") == 1.5

    @pytest.mark.parametrize(("saisie", "type_"), [("abc", "int"), ("x", "float")])
    def test_une_saisie_invalide_leve_une_erreur_du_paquet(
        self, saisie: str, type_: str
    ) -> None:
        """Une `ValueError` nue produirait une erreur cinq cents."""
        with pytest.raises(SettingsError, match="invalide"):
            parse_setting_value(saisie, type_)

    @pytest.mark.parametrize("type_", ["int", "float"])
    def test_une_saisie_vide_est_refusee(self, type_: str) -> None:
        with pytest.raises(SettingsError, match="manquante"):
            parse_setting_value("   ", type_)

    def test_les_blancs_de_bord_sont_tolerés(self) -> None:
        assert parse_setting_value("  42  ", "int") == 42


class TestSaisieTexte:
    def test_le_texte_est_conservé_tel_quel(self) -> None:
        """Une valeur textuelle peut légitimement commencer par une espace."""
        assert parse_setting_value("  bonjour  ", "str") == "  bonjour  "

    def test_un_texte_vide_est_permis(self) -> None:
        """Contrairement à un entier, la chaîne vide est une valeur."""
        assert parse_setting_value("", "str") == ""


class TestTypeInconnu:
    # `json` figurait ici comme exemple de type hors contrat. Il est devenu un
    # type déclaré (`SETTINGS-JSON-TYPE-001`), et l'exemple a suivi : ce que ce
    # test fixe est le refus d'un type absent du contrat, pas la liste d'alors.
    @pytest.mark.parametrize("type_", ["date", "decimal", "", "INT"])
    def test_un_type_hors_contrat_est_refuse(self, type_: str) -> None:
        with pytest.raises(SettingsError, match="Type inconnu"):
            parse_setting_value("x", type_)

    def test_le_refus_enumere_les_types_acceptes(self) -> None:
        """Le message doit citer le contrat courant, pas une liste figée ici."""
        from forge_mvc_settings import SUPPORTED_TYPES

        with pytest.raises(SettingsError) as capture:
            parse_setting_value("x", "date")

        assert ", ".join(SUPPORTED_TYPES) in str(capture.value)


class TestAffichage:
    def test_les_parametres_sortent_tries_par_cle(self) -> None:
        """Un ordre au hasard ferait sauter les lignes d'un rafraîchissement à l'autre."""
        faux = _FauxDb([
            {"setting_key": "zeta", "setting_value": "1", "value_type": "int"},
            {"setting_key": "alpha", "setting_value": "x", "value_type": "str"},
        ])
        assert [ligne.key for ligne in describe_settings(db=faux)] == ["alpha", "zeta"]

    def test_la_valeur_est_typee_et_sa_forme_texte_fournie(self) -> None:
        faux = _FauxDb([
            {"setting_key": "port", "setting_value": "8000", "value_type": "int"},
        ])
        ligne = describe_settings(db=faux)[0]

        assert ligne.value == 8000
        assert ligne.raw == "8000"
        assert ligne.value_type == "int"

    def test_un_booleen_s_affiche_en_forme_renvoyable(self) -> None:
        """`True` dans un champ produirait une saisie que la conversion refuserait."""
        faux = _FauxDb([
            {"setting_key": "actif", "setting_value": "1", "value_type": "bool"},
        ])
        ligne = describe_settings(db=faux)[0]

        assert ligne.value is True
        assert ligne.raw == "1"
        assert parse_setting_value(ligne.raw, ligne.value_type) is True


class TestAllerRetourComplet:
    """Ce qu'un écran fait vraiment : afficher, puis réécrire la saisie."""

    @pytest.mark.parametrize(
        ("valeur", "type_"),
        [("8000", "int"), ("1", "bool"), ("0", "bool"), ("1.5", "float"), ("x", "str")],
    )
    def test_ce_qui_est_affiche_est_acceptable_en_retour(
        self, valeur: str, type_: str
    ) -> None:
        faux = _FauxDb([
            {"setting_key": "k", "setting_value": valeur, "value_type": type_},
        ])
        ligne = describe_settings(db=faux)[0]

        assert parse_setting_value(ligne.raw, ligne.value_type) == ligne.value


class TestSansDependance:
    def test_settings_n_importe_pas_le_back_office(self) -> None:
        """Un projet sans back-office édite ses paramètres depuis sa propre interface."""
        from forge_mvc_settings import admin_view

        arbre = ast.parse(Path(admin_view.__file__).read_text(encoding="utf-8"))
        modules: list[str] = []
        for noeud in ast.walk(arbre):
            if isinstance(noeud, ast.Import):
                modules.extend(alias.name for alias in noeud.names)
            elif isinstance(noeud, ast.ImportFrom) and noeud.module:
                modules.append(noeud.module)

        interdits = [
            m for m in modules if m.startswith("forge_mvc_") and "settings" not in m
        ]
        assert interdits == [], f"dépendance vers un autre opt-in : {interdits}"

    def test_le_module_ne_rend_aucune_page(self) -> None:
        from forge_mvc_settings import admin_view

        source = Path(admin_view.__file__).read_text(encoding="utf-8")
        for interdit in ("Response", "render", "template"):
            assert interdit not in source, f"{interdit} n'a rien à faire ici"
