"""I18N-LOCALE-DETECTION-001 : d'où vient la locale active.

Le paquet annonçait « locale et fallback » et ne savait pas d'où venait la
locale : `trans()` retombait sur une valeur globale de configuration, la même
pour tous les visiteurs. Une application multilingue devait écrire sa propre
détection, ce que la documentation ne disait pas.

L'ordre est explicite, du plus intentionnel au plus supposé : la session, puis
`Accept-Language`, puis le défaut.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_i18n")

from forge_mvc_i18n.detection import (  # noqa: E402
    SESSION_KEY_LOCALE,
    available_locales,
    detect_locale,
    negotiate_locale,
    parse_accept_language,
)

DISPONIBLES = ["fr", "en", "es"]


class TestAnalyseDeLEnTete:
    def test_l_ordre_suit_les_facteurs_de_qualite(self) -> None:
        assert parse_accept_language("en;q=0.2,de;q=0.9,fr;q=0.5") == ["de", "fr", "en"]

    def test_une_entree_sans_q_vaut_un(self) -> None:
        assert parse_accept_language("fr-FR,fr;q=0.9,en;q=0.8") == ["fr-FR", "fr", "en"]

    def test_l_ordre_de_l_entete_departage_a_qualite_egale(self) -> None:
        """Un tri instable rendrait la détection imprévisible."""
        assert parse_accept_language("de,fr,en") == ["de", "fr", "en"]

    def test_un_refus_explicite_est_ecarte(self) -> None:
        """`q=0` signifie « surtout pas celle là »."""
        assert parse_accept_language("fr;q=0,en") == ["en"]

    @pytest.mark.parametrize("entete", [None, "", "   ", "*", ",,,", ";;;"])
    def test_un_entete_vide_ou_generique_ne_donne_rien(self, entete: "str | None") -> None:
        assert parse_accept_language(entete) == []

    @pytest.mark.parametrize(
        "entete",
        ["fr;q=abc", "fr;q=", "../etc/passwd", "fr/../en", "fr\x00en", "<script>"],
    )
    def test_un_entete_malforme_ou_hostile_ne_fait_pas_echouer(self, entete: str) -> None:
        """Un en-tête vient du client : il ne doit ni lever, ni ouvrir un chemin."""
        resultat = parse_accept_language(entete)
        assert all("/" not in x and ".." not in x for x in resultat)

    def test_un_entete_enorme_est_borne(self) -> None:
        """Un en-tête de plusieurs kilo-octets ne doit pas coûter une analyse."""
        assert len(parse_accept_language(",".join(["fr"] * 5000))) <= 20


class TestNegociation:
    def test_une_correspondance_exacte_gagne(self) -> None:
        assert negotiate_locale(["en"], DISPONIBLES) == "en"

    def test_une_variante_regionale_retombe_sur_sa_base(self) -> None:
        """Un navigateur annonce presque toujours une région."""
        assert negotiate_locale(["fr-FR"], DISPONIBLES) == "fr"
        assert negotiate_locale(["fr_CA"], DISPONIBLES) == "fr"

    def test_une_base_ne_choisit_pas_une_variante(self) -> None:
        """Servir `fr-CA` à qui demande `fr` serait une supposition."""
        assert negotiate_locale(["fr"], ["fr-CA", "en"]) is None

    def test_la_casse_est_ignoree(self) -> None:
        assert negotiate_locale(["FR-fr"], DISPONIBLES) == "fr"

    def test_la_premiere_servable_gagne(self) -> None:
        assert negotiate_locale(["de", "es", "fr"], DISPONIBLES) == "es"

    @pytest.mark.parametrize(
        ("voulues", "disponibles"), [([], DISPONIBLES), (["fr"], []), ([], [])]
    )
    def test_sans_candidat_rien_n_est_negocie(
        self, voulues: list[str], disponibles: list[str]
    ) -> None:
        assert negotiate_locale(voulues, disponibles) is None


class TestOrdreDeDetection:
    def test_la_session_prime_sur_l_entete(self) -> None:
        """Un choix explicite l'emporte sur une préférence de navigateur."""
        assert detect_locale(
            session_locale="en", accept_language="fr", available=DISPONIBLES
        ) == "en"

    def test_l_entete_sert_quand_la_session_est_muette(self) -> None:
        assert detect_locale(
            accept_language="es-ES,es;q=0.9", available=DISPONIBLES
        ) == "es"

    def test_le_defaut_sert_en_dernier(self) -> None:
        assert detect_locale(
            accept_language="de", available=DISPONIBLES, default="fr"
        ) == "fr"

    def test_sans_rien_la_detection_rend_none(self) -> None:
        """À l'appelant de décider, plutôt qu'à la bibliothèque de supposer."""
        assert detect_locale() is None

    def test_une_session_non_servable_ne_bloque_pas_l_entete(self) -> None:
        """Une locale retirée du projet ne doit pas figer un visiteur."""
        assert detect_locale(
            session_locale="de", accept_language="es", available=DISPONIBLES
        ) == "es"


class TestListeBlanche:
    def test_sans_liste_les_sources_clientes_sont_refusees(self) -> None:
        """Mieux vaut le défaut qu'un catalogue qu'on n'a pas choisi de servir."""
        assert detect_locale(
            session_locale="fr", accept_language="fr", default="en"
        ) == "en"

    @pytest.mark.parametrize(
        "hostile", ["../../etc/passwd", "..", "fr/../../en", "/etc/hosts"]
    )
    def test_une_locale_hostile_n_est_jamais_retenue(self, hostile: str) -> None:
        assert detect_locale(
            session_locale=hostile, accept_language=hostile,
            available=DISPONIBLES, default="fr",
        ) == "fr"

    def test_le_defaut_n_est_pas_filtre(self) -> None:
        """L'application répond de sa propre configuration."""
        assert detect_locale(available=["fr"], default="zz") == "zz"


class TestCataloguesDisponibles:
    def test_les_catalogues_presents_sont_listes(self, tmp_path: Path) -> None:
        for locale in ("fr", "en", "pt_BR"):
            (tmp_path / f"{locale}.json").write_text("{}", encoding="utf-8")

        assert available_locales(tmp_path) == ["en", "fr", "pt_BR"]

    def test_un_dossier_absent_ne_leve_pas(self, tmp_path: Path) -> None:
        assert available_locales(tmp_path / "jamais") == []

    def test_les_noms_douteux_sont_ecartes(self, tmp_path: Path) -> None:
        (tmp_path / "fr.json").write_text("{}", encoding="utf-8")
        (tmp_path / "mon catalogue.json").write_text("{}", encoding="utf-8")

        assert available_locales(tmp_path) == ["fr"]

    def test_seuls_les_json_comptent(self, tmp_path: Path) -> None:
        (tmp_path / "fr.json").write_text("{}", encoding="utf-8")
        (tmp_path / "en.txt").write_text("", encoding="utf-8")

        assert available_locales(tmp_path) == ["fr"]


class TestParcoursComplet:
    def test_de_l_entete_au_texte_traduit(self, tmp_path: Path) -> None:
        """Le geste que la référence donne à copier, joué de bout en bout."""
        from forge_mvc_i18n import clear_translation_cache, trans

        (tmp_path / "fr.json").write_text('{"greeting": "Bonjour"}', encoding="utf-8")
        (tmp_path / "en.json").write_text('{"greeting": "Hello"}', encoding="utf-8")
        clear_translation_cache()

        locale = detect_locale(
            accept_language="en-GB,en;q=0.9,fr;q=0.5",
            available=available_locales(tmp_path),
            default="fr",
        )
        assert locale == "en"
        assert trans("greeting", locale, tmp_path) == "Hello"

    def test_la_cle_de_session_est_nommee_une_fois(self) -> None:
        """L'application et le paquet désignent la même, sans la recopier."""
        assert SESSION_KEY_LOCALE == "_i18n_locale"
