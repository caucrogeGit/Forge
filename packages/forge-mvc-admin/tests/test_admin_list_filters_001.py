"""ADMIN-LIST-FILTERS-001 : filtrer, chercher et trier une liste du back-office.

La liste affichait la table entière, page par page, sans autre choix que de
tourner les pages. Passé quelques centaines de lignes, retrouver un
enregistrement devenait impraticable, et le back-office avec lui.

Les filtres viennent de l'URL : ce sont des entrées non fiables, et tout
l'enjeu est qu'elles ne décident jamais d'un identifiant SQL.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_admin")

from forge_mvc_admin import AdminResource  # noqa: E402
from forge_mvc_admin.exceptions import AdminResourceError  # noqa: E402
from forge_mvc_admin.query import (  # noqa: E402
    LIKE_ESCAPE,
    build_count_sql,
    build_list_sql,
    build_where_clause,
    escape_like,
    list_params,
    list_rows,
    resolve_sort,
)


def _ressource(**extra: Any) -> AdminResource:
    params: dict[str, Any] = {
        "entity": "Article", "slug": "articles", "label": "Article",
        "plural_label": "Articles", "list_fields": ("titre", "statut"),
        "form_fields": ("titre",), "table": "articles",
    }
    params.update(extra)
    return AdminResource(**params)


RESSOURCE = _ressource(filter_fields=("statut",), search_fields=("titre",))


class TestColonnesRefusees:
    """Le cœur du ticket : un nom d'URL ne devient jamais un identifiant SQL."""

    def test_une_colonne_non_declaree_est_refusee(self) -> None:
        with pytest.raises(AdminResourceError, match="non filtrable"):
            build_where_clause(RESSOURCE, filters={"mot_de_passe": "x"})

    def test_une_colonne_affichee_mais_non_declaree_filtrable_est_refusee(self) -> None:
        """`list_fields` n'ouvre pas le filtre : la déclaration est séparée."""
        with pytest.raises(AdminResourceError, match="non filtrable"):
            build_where_clause(RESSOURCE, filters={"titre": "x"})

    @pytest.mark.parametrize(
        "hostile",
        ["statut; DROP TABLE articles", "statut OR 1=1", "1=1", "statut--",
         "statut/*", "(SELECT 1)", "statut UNION SELECT"],
    )
    def test_une_injection_dans_le_nom_est_refusee(self, hostile: str) -> None:
        with pytest.raises(AdminResourceError):
            build_where_clause(RESSOURCE, filters={hostile: "x"})

    def test_sans_declaration_aucun_filtre_n_est_possible(self) -> None:
        """Une ressource qui ne déclare rien reste fermée."""
        with pytest.raises(AdminResourceError):
            build_where_clause(_ressource(), filters={"statut": "x"})

    def test_une_recherche_sans_champs_declares_est_refusee(self) -> None:
        with pytest.raises(AdminResourceError, match="search_fields"):
            build_where_clause(_ressource(), search="terme")

    def test_le_message_nomme_les_colonnes_permises(self) -> None:
        """Un refus doit dire comment réussir."""
        with pytest.raises(AdminResourceError, match="statut"):
            build_where_clause(RESSOURCE, filters={"inconnue": "x"})


class TestValeursLiees:
    def test_une_valeur_hostile_reste_un_parametre(self) -> None:
        """La valeur n'entre jamais dans le SQL, quelle qu'elle soit."""
        sql, params = build_where_clause(
            RESSOURCE, filters={"statut": "'; DROP TABLE articles; --"}
        )
        assert "DROP" not in sql
        assert params == ["'; DROP TABLE articles; --"]

    def test_chaque_filtre_produit_un_parametre(self) -> None:
        ressource = _ressource(filter_fields=("statut", "titre"))
        sql, params = build_where_clause(
            ressource, filters={"statut": "publie", "titre": "essai"}
        )
        assert sql.count("?") == 2
        assert params == ["publie", "essai"]

    def test_les_filtres_sont_combines_en_et(self) -> None:
        ressource = _ressource(filter_fields=("statut", "titre"))
        sql, _ = build_where_clause(
            ressource, filters={"statut": "publie", "titre": "essai"}
        )
        assert " AND " in sql


class TestRecherche:
    def test_la_recherche_balaie_les_champs_declares(self) -> None:
        ressource = _ressource(search_fields=("titre", "statut"))
        sql, params = build_where_clause(ressource, search="essai")

        assert sql.count("LIKE") == 2
        assert " OR " in sql
        assert params == ["%essai%", "%essai%"]

    def test_le_ou_est_parenthese(self) -> None:
        """Sans parenthèses, le OR absorberait les filtres et les rendrait vains."""
        ressource = _ressource(filter_fields=("statut",), search_fields=("titre", "statut"))
        sql, _ = build_where_clause(ressource, filters={"statut": "p"}, search="e")

        assert "AND (" in sql and sql.rstrip().endswith(")")

    @pytest.mark.parametrize(
        ("saisie", "attendu"),
        [("100%", "100!%"), ("a_b", "a!_b"), ("!", "!!"), ("!%", "!!!%"), ("net", "net")],
    )
    def test_les_metacaracteres_sont_neutralises(self, saisie: str, attendu: str) -> None:
        """Chercher `100%` ne doit pas ramener tout ce qui commence par 100."""
        assert escape_like(saisie) == attendu

    def test_le_caractere_d_echappement_est_declare(self) -> None:
        sql, _ = build_where_clause(RESSOURCE, search="x")
        assert f"ESCAPE '{LIKE_ESCAPE}'" in sql

    def test_l_echappement_n_est_pas_le_backslash(self) -> None:
        """Son sens dépend d'un réglage de serveur sur MariaDB."""
        assert LIKE_ESCAPE != "\\\\"

    @pytest.mark.parametrize("vide", [None, "", "   "])
    def test_une_recherche_vide_ne_filtre_rien(self, vide: "str | None") -> None:
        assert build_where_clause(RESSOURCE, search=vide) == ("", [])


class TestTri:
    def test_le_tri_par_defaut_vient_de_la_ressource(self) -> None:
        assert resolve_sort(RESSOURCE, None) == "titre"

    def test_une_colonne_affichee_est_acceptee(self) -> None:
        assert resolve_sort(RESSOURCE, "statut") == "statut"

    @pytest.mark.parametrize(
        "hostile", ["mot_de_passe", "titre; DROP TABLE x", "1", "titre DESC"]
    )
    def test_une_colonne_non_affichee_est_refusee(self, hostile: str) -> None:
        """Trier sur une colonne cachée révélerait son ordre, donc son contenu."""
        with pytest.raises(AdminResourceError, match="tri inconnue"):
            resolve_sort(RESSOURCE, hostile)

    def test_le_sens_est_un_booleen_pas_une_chaine(self) -> None:
        """Aucune chaîne de l'URL n'entre dans la clause ORDER BY."""
        montant = build_list_sql(RESSOURCE)
        descendant = build_list_sql(RESSOURCE, descending=True)

        assert "ORDER BY titre ASC" in montant
        assert "ORDER BY titre DESC" in descendant

    def test_la_cle_primaire_departage(self) -> None:
        """Sans elle, une page paginée montrerait deux fois la même ligne."""
        assert "ORDER BY titre ASC, id ASC" in build_list_sql(RESSOURCE)

    def test_la_cle_primaire_n_est_pas_repetee(self) -> None:
        """SQL Server refuse une colonne deux fois dans un ORDER BY."""
        ressource = _ressource(list_fields=("id", "titre"), order_by="id")
        sql = build_list_sql(ressource, sort="id")

        assert sql.count("id ASC") == 1, f"ORDER BY en doublon : {sql}"
        assert "ORDER BY id ASC," not in sql


class TestRequeteComplete:
    def test_sans_filtre_la_requete_est_inchangee(self) -> None:
        """La rétro-compatibilité : une ressource sans filtre se comporte comme avant."""
        sql = build_list_sql(_ressource())
        assert "WHERE" not in sql

    def test_le_compte_porte_sur_le_meme_ensemble_que_la_liste(self) -> None:
        """Sinon la pagination annoncerait des pages vides."""
        filtres = {"statut": "publie"}
        liste = build_list_sql(RESSOURCE, filters=filtres, search="e")
        compte = build_count_sql(RESSOURCE, filters=filtres, search="e")

        clause_liste = liste[liste.index("WHERE"):liste.index("ORDER BY")].strip()
        clause_compte = compte[compte.index("WHERE"):].strip()
        assert clause_liste == clause_compte

    def test_les_parametres_du_filtre_precedent_la_pagination(self) -> None:
        """Les inverser lierait un motif de recherche à une borne de page."""
        params = list_params(
            limit=20, offset=40, resource=RESSOURCE,
            filters={"statut": "publie"}, search="essai",
        )
        assert params[0] == "publie"
        assert params[1] == "%essai%"
        assert set(params[2:]) == {20, 40}

    def test_sans_ressource_seule_la_pagination_est_liee(self) -> None:
        assert set(list_params(limit=10, offset=0)) == {10, 0}


class TestLectureDeBoutEnBout:
    def test_la_requete_et_ses_parametres_partent_ensemble(self) -> None:
        vus: list[tuple[str, tuple[Any, ...]]] = []

        def fetch_all(sql: str, params: Any) -> list[dict[str, Any]]:
            vus.append((sql, tuple(params)))
            return [{"titre": "Essai", "statut": "publie"}]

        lignes = list_rows(
            RESSOURCE, fetch_all, limit=20, offset=0,
            filters={"statut": "publie"}, search="Ess", sort="statut", descending=True,
        )

        sql, params = vus[0]
        assert sql.count("?") == len(params), "un paramètre par emplacement"
        assert lignes[0]["titre"] == "Essai"


class TestReponseHttp:
    """Ce que le navigateur reçoit, y compris quand il demande n'importe quoi."""

    def _controleur(self, ressource: AdminResource, vus: "list[Any] | None" = None):
        from forge_mvc_admin.http import AdminController
        from forge_mvc_admin.registry import AdminRegistry

        registre = AdminRegistry()
        registre.register(ressource)

        def fetch_all(sql: str, params: Any) -> list[dict[str, Any]]:
            if vus is not None:
                vus.append((sql, tuple(params)))
            return []

        return AdminController(
            registry=registre,
            fetch_all=fetch_all,
            fetch_one=lambda sql, params: {"total": 0},
        )

    def _requete(self, **query: str):
        """Requête authentifiée : la liste est derrière `@require_auth`."""
        from forge_mvc_testing import FakeRequest

        requete = FakeRequest("GET", "/admin/articles", params=query, session_id="s1")
        requete.route_params = {"slug": "articles"}
        return requete

    def _sans_auth(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Neutralise l'authentification et le rendu, hors sujet de ce ticket.

        Le rendu du gabarit demanderait un moteur enregistré ; ce qui se teste
        ici est la requête construite et le code de retour, pas le HTML.
        """
        import core.security.decorators as decorateurs
        from core.http.response import Response as _Response
        from core.mvc.controller.base_controller import BaseController

        monkeypatch.setattr(decorateurs, "is_authenticated", lambda request: True)
        monkeypatch.setattr(
            BaseController, "render",
            staticmethod(lambda *a, **k: _Response(200, "rendu")),
        )

    def test_une_colonne_de_tri_non_declaree_rend_400(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """La demande est fautive, pas cassée : une 500 accuserait le serveur."""
        self._sans_auth(monkeypatch)
        reponse = self._controleur(RESSOURCE).resource_list(
            self._requete(tri="mot_de_passe")
        )
        assert reponse.status == 400

    def test_le_refus_ne_fuit_aucune_pile(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._sans_auth(monkeypatch)
        reponse = self._controleur(RESSOURCE).resource_list(
            self._requete(tri="mot_de_passe")
        )
        corps = reponse.body if isinstance(reponse.body, str) else str(reponse.body)
        assert "Traceback" not in corps
        assert "tri inconnue" in corps

    def test_un_filtre_vide_est_ignore(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Un champ de formulaire laissé vide ne doit pas filtrer sur la chaîne vide."""
        self._sans_auth(monkeypatch)
        vus: list[Any] = []
        self._controleur(RESSOURCE, vus).resource_list(self._requete(statut=""))

        assert "WHERE" not in vus[0][0]

    def test_un_filtre_renseigne_part_en_parametre(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._sans_auth(monkeypatch)
        vus: list[Any] = []
        self._controleur(RESSOURCE, vus).resource_list(self._requete(statut="publie"))

        sql, params = vus[0]
        assert "statut = ?" in sql
        assert "publie" in params


class TestCriteresPreserves:
    """Tourner une page ne doit pas perdre le filtre."""

    def test_les_criteres_suivent_la_pagination(self) -> None:
        from forge_mvc_admin.http import _criteria_query  # pyright: ignore[reportPrivateUsage]

        assert _criteria_query({"statut": "publie"}, "essai", "titre", True) == (
            "&statut=publie&q=essai&tri=titre&sens=desc"
        )

    def test_sans_critere_la_chaine_est_vide(self) -> None:
        from forge_mvc_admin.http import _criteria_query  # pyright: ignore[reportPrivateUsage]

        assert _criteria_query({}, None, None, False) == ""

    def test_un_terme_a_caracteres_speciaux_est_encode(self) -> None:
        """Un `&` non encodé couperait la chaîne de requête en deux."""
        from forge_mvc_admin.http import _criteria_query  # pyright: ignore[reportPrivateUsage]

        chaine = _criteria_query({}, "a&b=c", None, False)
        assert "a%26b%3Dc" in chaine
