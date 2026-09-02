"""Les quatre tickets import-export du cycle rc8.

`IMPEXP-COLUMN-MAPPING-001`, `IMPEXP-ERROR-REPORT-001`,
`IMPEXP-FILTERED-EXPORT-001` et `IMPEXP-JSONL-001`.

Le défaut le plus coûteux ne tenait pas à une fonction absente. Une colonne
requise mal orthographiée dans l'en-tête n'était pas détectée : chaque ligne
produisait « valeur requise manquante », et un fichier de dix mille lignes
rendait dix mille erreurs pour un seul en-tête, la vraie cause restant
introuvable.

Côté export, les filtres étaient **déjà** respectés. Ce qui ne l'était pas est
plus grave : l'export s'arrêtait à mille lignes sans le dire.
"""
from __future__ import annotations

from typing import Any

import pytest

from forge_mvc_import_export.engine import (
    FieldSpec,
    ImportReport,
    coerce_int,
    import_rows,
    resolve_headers,
)
from forge_mvc_import_export.jsonl import (
    JSONL_MIME_TYPE,
    JsonlError,
    parse_jsonl,
    to_jsonl,
)
from forge_mvc_import_export.report import (
    MAX_VALUE_LENGTH,
    REPORT_COLUMNS,
    SPREADSHEET_ROW_OFFSET,
    errors_to_csv,
    errors_to_rows,
    report_filename,
)


# ------------------------------------------------- IMPEXP-COLUMN-MAPPING


class TestCorrespondanceDeclaree:

    def test_sans_source_l_en_tete_est_le_nom_du_champ(self) -> None:
        """Comportement d'avant le ticket, inchangé."""
        assert FieldSpec("email").accepted_headers == ("email",)

    def test_un_en_tete_humain_alimente_un_champ_technique(self) -> None:
        """« Adresse e-mail » ne pouvait pas alimenter `email` : il fallait
        renommer à la main les colonnes d'un export tableur."""
        spec = FieldSpec("email", source="Adresse e-mail")

        mapping = resolve_headers(["Adresse e-mail", "nom"], [spec])

        assert mapping.resolved == {"email": "Adresse e-mail"}

    def test_plusieurs_en_tetes_sont_acceptes_dans_l_ordre(self) -> None:
        spec = FieldSpec("email", source=["Adresse e-mail", "Courriel", "email"])

        assert resolve_headers(["Courriel"], [spec]).resolved == {"email": "Courriel"}

    def test_le_premier_en_tete_present_l_emporte(self) -> None:
        spec = FieldSpec("email", source=["Courriel", "email"])

        mapping = resolve_headers(["email", "Courriel"], [spec])

        assert mapping.resolved == {"email": "Courriel"}

    def test_rien_n_est_rapproche_par_ressemblance(self) -> None:
        """Rapprocher « Prix HT » de `prix_ttc` parce que les deux contiennent
        « prix » ferait importer la mauvaise colonne sans le signaler."""
        mapping = resolve_headers(["Prix HT"], [FieldSpec("prix_ttc")])

        assert mapping.resolved == {}
        assert mapping.missing_required == ("prix_ttc",)

    def test_la_casse_n_est_pas_normalisee(self) -> None:
        """« Email » et « email » sont deux en-têtes différents tant qu'un
        `source` ne dit pas qu'ils désignent le même champ."""
        assert resolve_headers(["Email"], [FieldSpec("email")]).missing_required

    def test_les_espaces_de_bordure_sont_tolerees(self) -> None:
        """Un export tableur en pose souvent, et ce n'est pas une intention."""
        assert resolve_headers(["  email  "], [FieldSpec("email")]).ok

    def test_une_colonne_optionnelle_absente_n_est_pas_une_erreur(self) -> None:
        mapping = resolve_headers(["nom"], [FieldSpec("note", required=False)])

        assert mapping.ok
        assert mapping.missing_optional == ("note",)

    def test_les_en_tetes_inutilises_sont_nommes(self) -> None:
        """Ils ne sont pas une erreur, mais les nommer aide à repérer une
        correspondance oubliée."""
        mapping = resolve_headers(["nom", "Service"], [FieldSpec("nom")])

        assert mapping.unused_headers == ("Service",)


class TestColonneAbsente:
    """Le défaut le plus coûteux du paquet."""

    def test_une_colonne_absente_donne_une_erreur_et_non_dix_mille(self) -> None:
        specs = [FieldSpec("nom"), FieldSpec("email")]
        lignes = [{"nom": f"n{i}"} for i in range(10_000)]

        rapport = import_rows(lignes, specs, lambda rec: None)

        assert len(rapport.errors) == 1

    def test_le_fichier_n_est_meme_pas_parcouru(self) -> None:
        """L'utilisateur doit corriger son en-tête, pas ses données."""
        rapport = import_rows(
            [{"nom": "A"}], [FieldSpec("nom"), FieldSpec("email")], lambda rec: None
        )

        assert rapport.rejected_before_reading
        assert rapport.header_errors == ("email",)

    def test_le_message_nomme_la_colonne_et_les_en_tetes_lus(self) -> None:
        rapport = import_rows(
            [{"nom": "A", "courriel": "x"}],
            [FieldSpec("nom"), FieldSpec("email")],
            lambda rec: None,
        )

        message = rapport.errors[0].message
        assert "'email'" in message
        assert "'courriel'" in message

    def test_rien_n_est_insere(self) -> None:
        inseres: list[Any] = []
        import_rows(
            [{"nom": "A"}], [FieldSpec("nom"), FieldSpec("email")], inseres.append
        )

        assert inseres == []

    def test_le_mode_partiel_n_ouvre_pas_cette_porte(self) -> None:
        """Une colonne absente n'est pas une ligne fautive : aucune ligne ne
        peut être valide sans elle."""
        inseres: list[Any] = []
        import_rows(
            [{"nom": "A"}],
            [FieldSpec("nom"), FieldSpec("email")],
            inseres.append,
            partial=True,
        )

        assert inseres == []


class TestImportAvecCorrespondance:

    def test_les_valeurs_viennent_de_la_colonne_declaree(self) -> None:
        inseres: list[dict[str, object]] = []
        specs = [FieldSpec("email", source="Adresse e-mail"), FieldSpec("age", coerce=coerce_int)]

        import_rows(
            [{"Adresse e-mail": "a@b.fr", "age": "30"}], specs, inseres.append
        )

        assert inseres == [{"email": "a@b.fr", "age": 30}]

    def test_le_comportement_sans_source_est_inchange(self) -> None:
        inseres: list[dict[str, object]] = []

        import_rows([{"nom": "A"}], [FieldSpec("nom")], inseres.append)

        assert inseres == [{"nom": "A"}]


# -------------------------------------------------- IMPEXP-ERROR-REPORT


def _rapport_de_trois_erreurs() -> "tuple[ImportReport, list[dict[str, str]]]":
    specs = [FieldSpec("nom"), FieldSpec("age", coerce=coerce_int)]
    lignes = [
        {"nom": "A", "age": "30"},
        {"nom": "", "age": "=cmd|' /c calc'!A1"},
        {"nom": "C", "age": "abc"},
    ]
    return import_rows(lignes, specs, lambda rec: None), lignes


class TestRapportTelechargeable:

    def test_il_porte_les_colonnes_attendues(self) -> None:
        rapport, lignes = _rapport_de_trois_erreurs()

        csv = errors_to_csv(rapport, lignes)

        assert csv.splitlines()[0] == ",".join(REPORT_COLUMNS)

    def test_il_donne_le_numero_de_ligne_du_tableur(self) -> None:
        """« Ligne 1847 » oblige à chercher à la main, et la numérotation du
        rapport et celle du tableur diffèrent d'une unité à cause de l'en-tête."""
        rapport, lignes = _rapport_de_trois_erreurs()

        premiere = errors_to_rows(rapport, lignes)[0]

        assert premiere["ligne"] == 2
        assert premiere["ligne_tableur"] == 2 + SPREADSHEET_ROW_OFFSET

    def test_il_porte_la_valeur_refusee(self) -> None:
        """Sans elle, il faut rouvrir le fichier pour comprendre."""
        rapport, lignes = _rapport_de_trois_erreurs()

        valeurs = [r["valeur_refusee"] for r in errors_to_rows(rapport, lignes)]

        assert "abc" in valeurs

    def test_le_rapport_est_lui_meme_echappe(self) -> None:
        """Il contient des données du fichier déposé : sans échappement, il
        deviendrait lui même le vecteur."""
        rapport, lignes = _rapport_de_trois_erreurs()

        csv = errors_to_csv(rapport, lignes)

        assert "=cmd" in csv
        assert "'=cmd" in csv, "la cellule doit être rendue inerte pour un tableur"

    def test_une_valeur_demesuree_est_tronquee(self) -> None:
        specs = [FieldSpec("age", coerce=coerce_int)]
        lignes = [{"age": "x" * 5000}]
        rapport = import_rows(lignes, specs, lambda rec: None)

        valeur = str(errors_to_rows(rapport, lignes)[0]["valeur_refusee"])

        assert len(valeur) <= MAX_VALUE_LENGTH + 1

    def test_sans_les_lignes_le_rapport_reste_utilisable(self) -> None:
        rapport, _ = _rapport_de_trois_erreurs()

        lignes = errors_to_rows(rapport)

        assert all(r["valeur_refusee"] == "" for r in lignes)
        assert all(r["probleme"] for r in lignes)

    def test_un_rapport_sans_erreur_rend_l_en_tete_seul(self) -> None:
        """Un fichier vide se lit comme un téléchargement raté."""
        csv = errors_to_csv(ImportReport(imported=3, errors=[]))

        assert csv.strip() == ",".join(REPORT_COLUMNS)

    def test_une_erreur_d_en_tete_n_a_pas_de_valeur_refusee(self) -> None:
        rapport = import_rows(
            [{"nom": "A"}], [FieldSpec("nom"), FieldSpec("email")], lambda rec: None
        )

        ligne = errors_to_rows(rapport, [{"nom": "A"}])[0]

        assert ligne["ligne_tableur"] == ""
        assert ligne["valeur_refusee"] == ""

    def test_une_erreur_d_insertion_n_a_pas_de_colonne(self) -> None:
        def _echoue(rec: dict[str, object]) -> None:
            raise RuntimeError("doublon")

        rapport = import_rows([{"nom": "A"}], [FieldSpec("nom")], _echoue)

        assert errors_to_rows(rapport, [{"nom": "A"}])[0]["colonne"] == ""


class TestNomDuRapport:

    @pytest.mark.parametrize(
        "source,attendu",
        [
            ("clients.csv", "clients-erreurs.csv"),
            ("Clients 2026.csv", "Clients-2026-erreurs.csv"),
            ("../../etc/passwd", "passwd-erreurs.csv"),
            ("", "import-erreurs.csv"),
        ],
    )
    def test_il_est_assaini(self, source: str, attendu: str) -> None:
        """Il voyage dans un en-tête Content-Disposition, où un saut de ligne
        couperait l'en-tête en deux."""
        assert report_filename(source) == attendu

    def test_un_saut_de_ligne_ne_survit_pas(self) -> None:
        nom = report_filename("a\r\nX-Injecte: 1.csv")

        assert "\n" not in nom and "\r" not in nom


# --------------------------------------------------------- IMPEXP-JSONL


class TestEcritureJsonl:

    def test_un_objet_par_ligne(self) -> None:
        texte = to_jsonl([{"a": 1}, {"a": 2}])

        assert texte.splitlines() == ['{"a":1}', '{"a":2}']

    def test_le_fichier_finit_par_un_saut(self) -> None:
        """Un `cat` de deux fichiers collerait sinon deux enregistrements."""
        assert to_jsonl([{"a": 1}]).endswith("\n")

    def test_les_types_survivent(self) -> None:
        """C'est ce que le CSV ne sait pas faire : tout y est du texte."""
        relu = parse_jsonl(to_jsonl([{"n": 1, "s": "1", "b": True, "v": None}]))

        assert relu == [{"n": 1, "s": "1", "b": True, "v": None}]

    def test_les_colonnes_ordonnent_et_restreignent(self) -> None:
        """Un ordre de clés variable ferait apparaître des différences là où
        les données sont identiques."""
        texte = to_jsonl([{"b": 2, "a": 1, "z": 9}], ["a", "b"])

        assert texte.strip() == '{"a":1,"b":2}'

    def test_une_cle_absente_est_ecrite_a_null(self) -> None:
        """Un consommateur qui lit un flux a besoin que toutes les lignes aient
        la même forme."""
        texte = to_jsonl([{"a": 1}, {"a": 2, "b": 3}], ["a", "b"])

        assert texte.splitlines()[0] == '{"a":1,"b":null}'

    def test_les_accents_ne_sont_pas_echappes(self) -> None:
        """Un fichier destiné à être relu par un humain reste lisible."""
        assert "Élise" in to_jsonl([{"nom": "Élise"}])

    def test_une_liste_vide_rend_une_chaine_vide(self) -> None:
        assert to_jsonl([]) == ""

    def test_le_type_mime_est_celui_du_ndjson(self) -> None:
        assert JSONL_MIME_TYPE.startswith("application/x-ndjson")


class TestLectureJsonl:

    def test_les_lignes_vides_sont_ignorees(self) -> None:
        """Un fichier concaténé ou terminé par un saut en porte souvent."""
        assert parse_jsonl('{"a":1}\n\n\n{"a":2}\n') == [{"a": 1}, {"a": 2}]

    def test_une_ligne_illisible_leve_en_nommant_son_numero(self) -> None:
        with pytest.raises(JsonlError, match="ligne 2"):
            parse_jsonl('{"a":1}\n{pas du json}\n')

    def test_un_tableau_n_est_pas_un_enregistrement(self) -> None:
        with pytest.raises(JsonlError, match="objet JSON"):
            parse_jsonl('{"a":1}\n[1,2]\n')

    def test_une_valeur_seule_n_est_pas_un_enregistrement(self) -> None:
        with pytest.raises(JsonlError, match="objet JSON"):
            parse_jsonl("42\n")

    def test_le_mode_tolerant_ignore_ce_qui_est_illisible(self) -> None:
        """N'a de sens que pour récupérer ce qui est lisible d'un fichier
        abîmé, et perd des données en silence."""
        assert parse_jsonl('{"a":1}\nabc\n{"a":2}\n', strict=False) == [
            {"a": 1}, {"a": 2}
        ]

    def test_l_erreur_descend_de_l_erreur_d_import(self) -> None:
        """Une application qui traite déjà les erreurs d'import n'a pas à
        distinguer le format pour rendre un message."""
        from forge_mvc_import_export.errors import CsvImportError

        assert issubclass(JsonlError, CsvImportError)

    def test_aller_retour(self) -> None:
        lignes = [{"nom": "A", "n": 1}, {"nom": "B", "n": 2}]

        assert parse_jsonl(to_jsonl(lignes)) == lignes


# ----------------------------------------------- IMPEXP-FILTERED-EXPORT


class TestExportCrud:
    """Les filtres étaient déjà respectés. La troncature ne l'était pas."""

    def _modele(self) -> str:
        from tests.test_crud_export_csv import _model

        return _model()

    def _controleur(self) -> str:
        from tests.test_crud_export_csv import _ctrl

        return _ctrl()

    def test_les_filtres_etaient_deja_transmis(self) -> None:
        """Faux besoin mesuré : recherche, tri et filtres passaient déjà."""
        modele = self._modele()

        assert "q=q, sort=sort, direction=direction" in modele
        assert "filters=filters" in modele

    def test_l_export_demande_une_ligne_de_plus_que_le_plafond(self) -> None:
        """La seule façon de savoir qu'il en restait, sans payer un COUNT."""
        assert "_EXPORT_LIMIT + 1" in self._modele()

    def test_il_rend_le_drapeau_de_troncature(self) -> None:
        modele = self._modele()

        assert "truncated = len(rows) > _EXPORT_LIMIT" in modele
        assert "return (rows[:_EXPORT_LIMIT], truncated)" in modele

    def test_le_nom_du_fichier_porte_la_troncature(self) -> None:
        """C'est ce que l'utilisateur lit."""
        assert "-TRONQUE.csv" in self._controleur()

    def test_un_en_tete_la_porte_aussi(self) -> None:
        """Pour un client programmatique, qui ne lit pas le nom du fichier."""
        controleur = self._controleur()

        assert "X-Forge-Export-Truncated" in controleur
        assert "X-Forge-Export-Limit" in controleur

    def test_un_export_complet_garde_son_nom(self) -> None:
        assert 'if truncated else "articles.csv"' in self._controleur()

    def test_le_code_engendre_reste_valide(self) -> None:
        import ast

        ast.parse(self._modele())
        ast.parse(self._controleur())
