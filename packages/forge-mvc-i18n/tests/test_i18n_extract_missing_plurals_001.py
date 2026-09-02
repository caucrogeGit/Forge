"""`I18N-EXTRACT-CLI-001`, `I18N-MISSING-KEYS-DEV-001`, `I18N-PLURALS-001`.

`trans()` rendait la clé elle même quand la traduction manquait, ce qui reste
le bon comportement : une page ne doit pas casser pour une traduction absente.
Mais **rien ne le signalait**, et « panier_vide » s'affichait à l'utilisateur
sans que personne ne s'en aperçoive avant lui.

`i18n:check` ne pouvait rien y faire : il compare deux catalogues entre eux, et
une clé absente des deux lui est invisible.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("forge_mvc_i18n")

from forge_mvc_i18n.extract import (  # noqa: E402
    ExtractionResult,
    extract_from_directory,
    extract_from_text,
)
from forge_mvc_i18n.plurals import (  # noqa: E402
    PLURAL_FORMS,
    UNSUPPORTED_LANGUAGES,
    PluralError,
    language_of,
    plural_form,
    select_plural,
)
from forge_mvc_i18n.translator import (  # noqa: E402
    clear_missing_keys,
    missing_keys,
    trans,
)


# ------------------------------------------------------ I18N-PLURALS


class TestRegleDePluriel:

    @pytest.mark.parametrize(
        "compte,attendu", [(0, "one"), (1, "one"), (2, "other"), (17, "other")]
    )
    def test_le_francais_met_zero_au_singulier(self, compte: int, attendu: str) -> None:
        """Le français écrit « 0 article », l'anglais « 0 articles »."""
        assert plural_form(compte, "fr") == attendu

    @pytest.mark.parametrize(
        "compte,attendu", [(0, "other"), (1, "one"), (2, "other")]
    )
    def test_l_anglais_ne_met_que_un_au_singulier(
        self, compte: int, attendu: str
    ) -> None:
        assert plural_form(compte, "en") == attendu

    def test_la_region_ne_change_pas_la_regle(self) -> None:
        """Le français de Belgique et celui de France comptent pareil."""
        assert plural_form(0, "fr_BE") == plural_form(0, "fr-CA") == plural_form(0, "fr")

    def test_un_compte_negatif_suit_sa_valeur_absolue(self) -> None:
        assert plural_form(-1, "en") == "one"

    @pytest.mark.parametrize("langue", ["ru", "ar", "pl", "cs", "cy"])
    def test_une_langue_a_plus_de_deux_formes_leve(self, langue: str) -> None:
        """Rendre `one` ou `other` pour du russe produirait une phrase fausse
        dans un cas sur deux, ce qui est pire qu'un refus visible."""
        with pytest.raises(PluralError, match="plus de deux formes"):
            plural_form(2, langue)

    def test_le_message_oriente_vers_une_bibliotheque_complete(self) -> None:
        with pytest.raises(PluralError, match="bibliothèque"):
            plural_form(2, "ru")

    def test_les_langues_non_couvertes_sont_declarees(self) -> None:
        assert {"ru", "ar", "pl"} <= UNSUPPORTED_LANGUAGES

    def test_deux_formes_seulement(self) -> None:
        """CLDR en définit six ; une implémentation partielle donnerait
        l'impression de couvrir une langue qu'elle massacre."""
        assert PLURAL_FORMS == ("one", "other")

    @pytest.mark.parametrize("mauvais", ["2", 2.0, True, None])
    def test_un_compte_non_entier_leve(self, mauvais: Any) -> None:
        with pytest.raises(PluralError):
            plural_form(mauvais, "fr")

    def test_la_langue_se_deduit_de_la_locale(self) -> None:
        assert language_of("fr_BE") == language_of("FR-be") == "fr"


class TestChoixDansLeCatalogue:

    def test_une_chaine_reste_une_chaine(self) -> None:
        """Le format existant continue de fonctionner sans changement."""
        assert select_plural("Bonjour", 3, "fr") == "Bonjour"

    def test_les_deux_formes_sont_choisies(self) -> None:
        catalogue = {"one": "{n} article", "other": "{n} articles"}

        assert select_plural(catalogue, 1, "fr") == "{n} article"
        assert select_plural(catalogue, 3, "fr") == "{n} articles"

    def test_une_forme_absente_leve(self) -> None:
        """Retomber sur l'autre forme afficherait « 3 article » sans que rien
        ne le signale."""
        with pytest.raises(PluralError, match="absente du catalogue"):
            select_plural({"one": "{n} article"}, 3, "fr")

    def test_le_message_liste_les_formes_presentes(self) -> None:
        with pytest.raises(PluralError, match="one"):
            select_plural({"one": "x"}, 3, "fr")

    @pytest.mark.parametrize("mauvais", [42, ["a"], None])
    def test_une_valeur_inattendue_leve(self, mauvais: Any) -> None:
        with pytest.raises(PluralError, match="inattendue"):
            select_plural(mauvais, 1, "fr")


# --------------------------------------------------- I18N-MISSING-KEYS


@pytest.fixture
def catalogue(tmp_path: Path) -> Path:
    dossier = tmp_path / "translations"
    dossier.mkdir()
    (dossier / "fr.json").write_text(
        json.dumps({"accueil": "Accueil"}), encoding="utf-8"
    )
    return dossier


@pytest.fixture(autouse=True)
def _registre_propre():
    clear_missing_keys()
    yield
    clear_missing_keys()


class TestClesManquantes:

    def test_la_cle_est_toujours_rendue_telle_quelle(
        self, catalogue: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Une page qui casse pour une traduction absente serait un remède
        pire que le mal."""
        monkeypatch.setenv("APP_ENV", "dev")

        assert trans("panier_vide", "fr", catalogue) == "panier_vide"

    def test_elle_est_collectee_hors_production(
        self, catalogue: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("APP_ENV", "dev")

        trans("panier_vide", "fr", catalogue)

        assert ("fr", "panier_vide") in missing_keys()

    def test_elle_est_journalisee(
        self, catalogue: Path, monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        monkeypatch.setenv("APP_ENV", "dev")

        with caplog.at_level(logging.WARNING, logger="forge.i18n"):
            trans("panier_vide", "fr", catalogue)

        assert "panier_vide" in caplog.text

    def test_la_meme_cle_n_est_signalee_qu_une_fois(
        self, catalogue: Path, monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """La même clé sur mille requêtes est un seul défaut, et l'accumuler
        ferait grossir la mémoire sans rien apprendre de plus."""
        monkeypatch.setenv("APP_ENV", "dev")

        with caplog.at_level(logging.WARNING, logger="forge.i18n"):
            for _ in range(50):
                trans("panier_vide", "fr", catalogue)

        assert caplog.text.count("panier_vide") == 1
        assert len(missing_keys()) == 1

    def test_la_production_reste_silencieuse(
        self, catalogue: Path, monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Journaliser chaque clé manquante à chaque requête noierait le
        journal, et une traduction absente n'est pas un incident
        d'exploitation."""
        monkeypatch.setenv("APP_ENV", "prod")

        with caplog.at_level(logging.WARNING, logger="forge.i18n"):
            resultat = trans("panier_vide", "fr", catalogue)

        assert resultat == "panier_vide"
        assert missing_keys() == ()
        assert "panier_vide" not in caplog.text

    def test_une_cle_traduite_n_est_pas_signalee(
        self, catalogue: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("APP_ENV", "dev")

        assert trans("accueil", "fr", catalogue) == "Accueil"
        assert missing_keys() == ()

    def test_le_registre_se_vide(
        self, catalogue: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("APP_ENV", "dev")
        trans("absente", "fr", catalogue)

        clear_missing_keys()

        assert missing_keys() == ()


# -------------------------------------------------------- I18N-EXTRACT


class TestExtraction:

    def test_les_cles_litterales_sont_trouvees(self) -> None:
        cles, _ = extract_from_text('{{ trans("panier_vide") }} {{ trans(\'accueil\') }}')

        assert set(cles) == {"panier_vide", "accueil"}

    def test_plusieurs_appels_sur_une_ligne(self) -> None:
        cles, _ = extract_from_text('{{ trans("un") }}{{ trans("deux") }}')

        assert set(cles) == {"un", "deux"}

    def test_les_espaces_dans_l_appel_sont_tolerees(self) -> None:
        cles, _ = extract_from_text('{{ trans (  "avec_espaces" ) }}')

        assert cles == ["avec_espaces"]

    def test_un_second_argument_ne_gene_pas(self) -> None:
        cles, _ = extract_from_text('{{ trans("cle", "en") }}')

        assert cles == ["cle"]

    def test_une_cle_calculee_est_comptee_sans_etre_extraite(self) -> None:
        """La clé n'existe qu'à l'exécution : la prétendre extraite ferait
        passer un minorant pour une liste exhaustive."""
        cles, dynamiques = extract_from_text("{{ trans(nom_variable) }}")

        assert cles == []
        assert dynamiques == 1

    def test_une_concatenation_est_comptee_aussi(self) -> None:
        cles, dynamiques = extract_from_text('{{ trans(prefixe ~ "_suffixe") }}')

        assert dynamiques == 1

    def test_une_cle_vide_est_ignoree(self) -> None:
        cles, _ = extract_from_text('{{ trans("") }} {{ trans("  ") }}')

        assert cles == []


class TestBalayageDeDossier:

    @pytest.fixture
    def vues(self, tmp_path: Path) -> Path:
        dossier = tmp_path / "views"
        (dossier / "pages").mkdir(parents=True)
        (dossier / "index.html").write_text('{{ trans("accueil") }}', encoding="utf-8")
        (dossier / "pages" / "panier.html").write_text(
            '{{ trans("panier_vide") }}{{ trans("accueil") }}', encoding="utf-8"
        )
        (dossier / "note.md").write_text('{{ trans("ignoree") }}', encoding="utf-8")
        return dossier

    def test_les_sous_dossiers_sont_balayes(self, vues: Path) -> None:
        resultat = extract_from_directory(vues)

        assert set(resultat.keys) == {"accueil", "panier_vide"}

    def test_une_cle_employee_deux_fois_ne_compte_qu_une(self, vues: Path) -> None:
        resultat = extract_from_directory(vues)

        assert resultat.keys.count("accueil") == 1

    def test_le_resultat_est_trie(self, vues: Path) -> None:
        """Un ordre stable rend deux exécutions comparables."""
        resultat = extract_from_directory(vues)

        assert list(resultat.keys) == sorted(resultat.keys)

    def test_les_extensions_hors_motif_sont_ignorees(self, vues: Path) -> None:
        assert "ignoree" not in extract_from_directory(vues).keys

    def test_le_detail_par_fichier_est_rendu(self, vues: Path) -> None:
        resultat = extract_from_directory(vues)

        assert "pages/panier.html" in resultat.by_file

    def test_un_dossier_absent_ne_leve_pas(self, tmp_path: Path) -> None:
        resultat = extract_from_directory(tmp_path / "jamais_cree")

        assert resultat.keys == ()
        assert resultat.files_scanned == 0

    def test_l_extraction_dit_si_elle_est_complete(self, tmp_path: Path) -> None:
        dossier = tmp_path / "v"
        dossier.mkdir()
        (dossier / "a.html").write_text('{{ trans(variable) }}', encoding="utf-8")

        resultat = extract_from_directory(dossier)

        assert not resultat.is_complete

    def test_une_extraction_sans_appel_calcule_est_complete(self, vues: Path) -> None:
        assert extract_from_directory(vues).is_complete


class TestCommandeExtract:

    @pytest.fixture
    def projet(self, tmp_path: Path) -> Path:
        vues = tmp_path / "mvc" / "views"
        vues.mkdir(parents=True)
        (vues / "index.html").write_text(
            '{{ trans("accueil") }}{{ trans("panier_vide") }}', encoding="utf-8"
        )
        traductions = tmp_path / "translations"
        traductions.mkdir()
        (traductions / "fr.json").write_text(
            json.dumps({"accueil": "Accueil", "jamais_employee": "X"}),
            encoding="utf-8",
        )
        return tmp_path

    def test_une_cle_absente_du_catalogue_fait_echouer(
        self, projet: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Le cas que `i18n:check` ne peut pas voir."""
        from cli.assets.i18n import cmd_i18n_extract

        code = cmd_i18n_extract([], root=projet)
        sortie = capsys.readouterr().out

        assert code == 1
        assert "panier_vide" in sortie

    def test_une_cle_du_catalogue_non_employee_est_signalee_sans_echec(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Elle peut servir à un appel calculé, ou à un gabarit hors mvc/views."""
        from cli.assets.i18n import cmd_i18n_extract

        vues = tmp_path / "mvc" / "views"
        vues.mkdir(parents=True)
        (vues / "a.html").write_text('{{ trans("accueil") }}', encoding="utf-8")
        traductions = tmp_path / "translations"
        traductions.mkdir()
        (traductions / "fr.json").write_text(
            json.dumps({"accueil": "A", "jamais": "J"}), encoding="utf-8"
        )

        code = cmd_i18n_extract([], root=tmp_path)
        sortie = capsys.readouterr().out

        assert code == 0
        assert "jamais" in sortie

    def test_sans_catalogue_les_cles_sont_seulement_listees(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from cli.assets.i18n import cmd_i18n_extract

        vues = tmp_path / "mvc" / "views"
        vues.mkdir(parents=True)
        (vues / "a.html").write_text('{{ trans("seule") }}', encoding="utf-8")

        code = cmd_i18n_extract([], root=tmp_path)

        assert code == 0
        assert "seule" in capsys.readouterr().out

    def test_la_locale_se_choisit(self, projet: Path) -> None:
        from cli.assets.i18n import _extract_locale

        assert _extract_locale(["i18n:extract", "--locale", "en"]) == "en"
        assert _extract_locale(["i18n:extract", "--locale=en"]) == "en"
        assert _extract_locale(["i18n:extract"]) == "fr"

    def test_un_appel_calcule_est_annonce(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from cli.assets.i18n import cmd_i18n_extract

        vues = tmp_path / "mvc" / "views"
        vues.mkdir(parents=True)
        (vues / "a.html").write_text('{{ trans(variable) }}', encoding="utf-8")

        cmd_i18n_extract([], root=tmp_path)

        assert "minorant" in capsys.readouterr().out


class TestResultatFige:

    def test_il_est_immuable(self) -> None:
        """Il traverse l'affichage, et un résultat modifié en route dirait
        autre chose que ce qui a été lu."""
        resultat = ExtractionResult((), 0, 0, {})

        with pytest.raises(Exception):
            resultat.keys = ("x",)  # type: ignore[misc]
