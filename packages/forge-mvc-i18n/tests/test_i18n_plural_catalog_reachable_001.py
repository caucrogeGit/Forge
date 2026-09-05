"""I18N-PLURAL-CATALOG-REACHABLE-001 : le pluriel est joignable du catalogue.

`select_plural` était écrite pour une valeur de catalogue, sa docstring le
disant mot pour mot : « choisit la forme dans une valeur de catalogue », et
« un objet portant les formes one et other ».

Le chargeur refusait précisément cette valeur, avec « Clés et valeurs doivent
être des chaînes ». L'entrée que la fonction attendait ne pouvait donc pas
venir d'un catalogue, et `trans` n'avait pas de `count` : le pluriel n'était
joignable qu'en construisant le dictionnaire à la main, ce que fait un test et
que ne fait aucune application.

Ce que ces tests fixent : l'aller de bout en bout, catalogue puis `trans`, et
surtout les refus. Une forme manquante est refusée au **chargement** et non à
la requête qui porte le nombre correspondant, sans quoi la page marche pour un
élève et casse pour deux.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_i18n")

from forge_mvc_i18n import (  # noqa: E402
    PluralError,
    TranslationCatalogError,
    clear_translation_cache,
    load_catalog,
    trans,
)


@pytest.fixture
def catalogue(tmp_path: Path):
    """Écrit un catalogue et rend le dossier, cache vidé."""
    dossier = tmp_path / "translations"
    dossier.mkdir()

    def _ecrire(contenu: dict[str, object], locale: str = "fr") -> str:
        (dossier / f"{locale}.json").write_text(
            json.dumps(contenu, ensure_ascii=False), encoding="utf-8")
        clear_translation_cache()
        return str(dossier)

    return _ecrire


PLURIEL = {"eleve.compte": {"one": "{count} élève inscrit",
                            "other": "{count} élèves inscrits"},
           "common.bonjour": "Bonjour"}


class TestAllerDeBoutEnBout:

    def test_le_catalogue_porte_une_entree_pluralisee(self, catalogue) -> None:
        """Elle était refusée au chargement, ce qui fermait toute la mécanique."""
        chemin = catalogue(PLURIEL)

        assert isinstance(load_catalog("fr", chemin)["eleve.compte"], dict)

    @pytest.mark.parametrize("nombre,attendu", [
        (0, "{count} élève inscrit"),
        (1, "{count} élève inscrit"),
        (2, "{count} élèves inscrits"),
        (21, "{count} élèves inscrits"),
    ])
    def test_le_francais_compte_zero_au_singulier(
        self, catalogue, nombre: int, attendu: str
    ) -> None:
        chemin = catalogue(PLURIEL)

        assert trans("eleve.compte", "fr", chemin, count=nombre) == attendu

    def test_l_anglais_compte_zero_au_pluriel(self, catalogue) -> None:
        """Les deux langues diffèrent sur zéro, et c'est la raison du module."""
        chemin = catalogue({"n": {"one": "one student", "other": "students"}}, "en")

        assert trans("n", "en", chemin, count=0) == "students"

    def test_une_entree_textuelle_ignore_le_nombre(self, catalogue) -> None:
        """Pour écrire l'appel sans savoir si la clé est encore pluralisée."""
        chemin = catalogue(PLURIEL)

        assert trans("common.bonjour", "fr", chemin, count=7) == "Bonjour"

    def test_le_texte_n_est_pas_formate(self, catalogue) -> None:
        """Le module n'a jamais substitué ; le rappeler évite une attente fausse."""
        chemin = catalogue(PLURIEL)

        assert "{count}" in trans("eleve.compte", "fr", chemin, count=3)


class TestRefus:

    def test_un_pluriel_sans_nombre_est_refuse(self, catalogue) -> None:
        """Rendre « one » afficherait « 3 élève » sans que rien ne le signale."""
        chemin = catalogue(PLURIEL)

        with pytest.raises(PluralError, match="count"):
            trans("eleve.compte", "fr", chemin)

    @pytest.mark.parametrize("valeur,motif", [
        ({"one": "un"}, "other"),
        ({"other": "des"}, "one"),
        ({}, "one"),
        ({"one": "un", "other": 3}, "chaîne"),
        ({"one": "un", "other": "  "}, "chaîne"),
        (["un", "des"], "objet"),
        (42, "objet"),
    ])
    def test_une_entree_mal_formee_est_refusee_au_chargement(
        self, catalogue, valeur: object, motif: str
    ) -> None:
        """Au chargement, pas à la requête qui porte le nombre manquant."""
        chemin = catalogue({"a.b": valeur})

        with pytest.raises(TranslationCatalogError, match=motif):
            load_catalog("fr", chemin)

    def test_une_langue_a_trois_formes_est_refusee(self, catalogue) -> None:
        """Le module ne couvre que « one » et « other », et le dit."""
        chemin = catalogue({"a.b": {"one": "un", "other": "des"}}, "ru")

        with pytest.raises(TranslationCatalogError, match="plus de deux formes"):
            load_catalog("ru", chemin)


class TestRepli:

    def test_le_repli_choisit_la_forme_de_la_langue_rendue(self, tmp_path: Path) -> None:
        """Un texte anglais servi en repli suit la règle anglaise, où zéro est pluriel."""
        from forge_mvc_i18n import set_fallback_locale

        dossier = tmp_path / "translations"
        dossier.mkdir()
        (dossier / "fr.json").write_text('{"autre": "x"}', encoding="utf-8")
        (dossier / "en.json").write_text(
            '{"n": {"one": "one student", "other": "students"}}', encoding="utf-8")
        clear_translation_cache()

        ancien = None
        try:
            from forge_mvc_i18n import get_fallback_locale

            ancien = get_fallback_locale()
            set_fallback_locale("en")

            assert trans("n", "fr", str(dossier), count=0) == "students"
        finally:
            if ancien is not None:
                set_fallback_locale(ancien)
