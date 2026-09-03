"""`ADMIN-BULK-ACTIONS-001` — supprimer plusieurs lignes en une fois.

Le back-office ne savait supprimer qu'une ligne à la fois : nettoyer deux cents
inscriptions de test demandait deux cents allers-retours, et deux cents
confirmations.
"""
from __future__ import annotations

from typing import Any

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_admin")

from forge_mvc_admin.query import (  # noqa: E402
    BULK_MAX_ROWS,
    BulkActionError,
    delete_rows,
)
from forge_mvc_admin.resources import AdminResource  # noqa: E402


@pytest.fixture
def ressource() -> AdminResource:
    return AdminResource(
        entity="User", slug="u", label="Utilisateur", plural_label="Utilisateurs",
        list_fields=("id",), form_fields=("id",), table="users",
        bulk_delete=True,
    )


@pytest.fixture
def avec_workflow() -> AdminResource:
    return AdminResource(
        entity="Article", slug="articles", label="Article", plural_label="Articles",
        list_fields=("id", "titre"), form_fields=("titre",), table="articles",
        bulk_delete=True, status_field="statut",
        bulk_transitions=(("brouillon", "publie"),),
    )


class _Executeur:
    def __init__(self, affectees: "int | None" = None) -> None:
        self.appels: "list[tuple[str, tuple[Any, ...]]]" = []
        self.affectees = affectees

    def __call__(self, sql: str, params: "tuple[Any, ...]") -> int:
        self.appels.append((sql, params))
        return len(params) if self.affectees is None else self.affectees


class TestSuppressionGroupee:

    def test_une_seule_requete(self, ressource: AdminResource) -> None:
        executeur = _Executeur()

        delete_rows(ressource, executeur, pk_values=[1, 2, 3])

        assert len(executeur.appels) == 1

    def test_les_identifiants_partent_en_parametres_lies(
        self, ressource: AdminResource
    ) -> None:
        """Les concaténer serait une injection, et le fait qu'ils viennent de
        cases cochées n'y change rien : une case cochée est une donnée de
        requête comme une autre."""
        executeur = _Executeur()

        delete_rows(ressource, executeur, pk_values=[1, 2, 3])

        sql, params = executeur.appels[0]
        assert sql.count("?") == 3
        assert params == (1, 2, 3)
        assert "1, 2, 3" not in sql

    def test_une_valeur_hostile_ne_touche_pas_le_sql(
        self, ressource: AdminResource
    ) -> None:
        executeur = _Executeur()

        delete_rows(ressource, executeur, pk_values=["1); DROP TABLE users; --"])

        sql, params = executeur.appels[0]
        assert "DROP" not in sql
        assert params == ("1); DROP TABLE users; --",)

    def test_la_cle_primaire_de_la_ressource_est_employee(
        self, ressource: AdminResource
    ) -> None:
        executeur = _Executeur()

        delete_rows(ressource, executeur, pk_values=[1])

        assert f"WHERE {ressource.pk} IN" in executeur.appels[0][0]

    def test_le_nombre_reellement_supprime_est_rendu(
        self, ressource: AdminResource
    ) -> None:
        """Une ligne supprimée entre l'affichage et la validation n'est pas une
        erreur, et refuser toute la fournée pour cela ferait échouer une action
        correcte."""
        assert delete_rows(ressource, _Executeur(affectees=2), pk_values=[1, 2, 3]) == 2


class TestRefus:

    def test_une_selection_vide_est_refusee(self, ressource: AdminResource) -> None:
        """Une suppression groupée sans sélection effacerait la table entière
        si la clause était omise."""
        executeur = _Executeur()

        with pytest.raises(BulkActionError, match="aucune ligne"):
            delete_rows(ressource, executeur, pk_values=[])

        assert executeur.appels == []

    def test_au_dela_du_plafond_c_est_refuse(self, ressource: AdminResource) -> None:
        """Une sélection de cette taille vient plus souvent d'un « tout cocher »
        malencontreux que d'une intention."""
        with pytest.raises(BulkActionError, match="plafond"):
            delete_rows(
                ressource, _Executeur(), pk_values=list(range(BULK_MAX_ROWS + 1))
            )

    def test_pile_au_plafond_c_est_permis(self, ressource: AdminResource) -> None:
        executeur = _Executeur()

        delete_rows(ressource, executeur, pk_values=list(range(BULK_MAX_ROWS)))

        assert len(executeur.appels) == 1

    def test_le_plafond_se_regle(self, ressource: AdminResource) -> None:
        with pytest.raises(BulkActionError):
            delete_rows(ressource, _Executeur(), pk_values=[1, 2, 3], max_rows=2)


# ─────────────────────────────────────────────────────────────────────────────
# Le câblage, qui manquait à la première livraison
# ─────────────────────────────────────────────────────────────────────────────


class TestDeclarationSurLaRessource:

    def test_la_suppression_groupee_est_fermee_par_defaut(self) -> None:
        """Une case à cocher offerte sans qu'on l'ait demandée invite à un
        geste irréversible sur une table qu'on croyait en lecture."""
        r = AdminResource(
            entity="A", slug="a", label="A", plural_label="As",
            list_fields=("id",), form_fields=("id",), table="a",
        )

        assert r.bulk_delete is False
        assert r.bulk_transitions == ()

    def test_une_transition_sans_colonne_de_statut_est_refusee(self) -> None:
        """L'action échouerait sinon à l'exécution sur N lignes, plutôt qu'ici
        où elle se corrige."""
        from forge_mvc_admin.exceptions import AdminResourceError

        with pytest.raises(AdminResourceError, match="status_field"):
            AdminResource(
                entity="A", slug="a", label="A", plural_label="As",
                list_fields=("id",), form_fields=("id",), table="a",
                bulk_transitions=(("x", "y"),),
            )

    def test_une_transition_sans_effet_est_refusee(self) -> None:
        from forge_mvc_admin.exceptions import AdminResourceError

        with pytest.raises(AdminResourceError, match="sans effet"):
            AdminResource(
                entity="A", slug="a", label="A", plural_label="As",
                list_fields=("id",), form_fields=("id",), table="a",
                status_field="s", bulk_transitions=(("x", "x"),),
            )


class TestTransitionGroupee:

    def test_le_statut_de_depart_est_dans_la_clause(
        self, avec_workflow: AdminResource
    ) -> None:
        """Une ligne dont le statut a changé entre l'affichage et la validation
        n'est pas touchée, là où une mise à jour sur la seule clé primaire
        écraserait un état que quelqu'un vient de poser."""
        from forge_mvc_admin.query import transition_rows

        executeur = _Executeur()
        transition_rows(
            avec_workflow, executeur, pk_values=[1, 2],
            from_status="brouillon", to_status="publie",
        )

        sql, params = executeur.appels[0]
        assert "AND statut = ?" in sql
        assert params[-1] == "brouillon"

    def test_les_identifiants_partent_en_parametres_lies(
        self, avec_workflow: AdminResource
    ) -> None:
        from forge_mvc_admin.query import transition_rows

        executeur = _Executeur()
        transition_rows(
            avec_workflow, executeur, pk_values=["1); DROP TABLE x; --"],
            from_status="brouillon", to_status="publie",
        )

        sql, _ = executeur.appels[0]
        assert "DROP" not in sql

    def test_sans_colonne_de_statut_c_est_refuse(
        self, ressource: AdminResource
    ) -> None:
        from forge_mvc_admin.query import transition_rows

        with pytest.raises(BulkActionError, match="status_field"):
            transition_rows(
                ressource, _Executeur(), pk_values=[1],
                from_status="a", to_status="b",
            )


class TestActionDemandee:

    def test_seule_une_transition_declaree_est_reconnue(
        self, avec_workflow: AdminResource
    ) -> None:
        """Une valeur venue du formulaire ne peut désigner qu'un couple que
        l'application a écrit."""
        from forge_mvc_admin.http import _parse_transition

        assert _parse_transition(avec_workflow, "transition:brouillon:publie") == (
            "brouillon", "publie"
        )
        assert _parse_transition(avec_workflow, "transition:brouillon:supprime") is None

    @pytest.mark.parametrize("action", ["delete", "transition:x", "", "n'importe quoi"])
    def test_une_action_mal_formee_ne_designe_rien(
        self, avec_workflow: AdminResource, action: str
    ) -> None:
        from forge_mvc_admin.http import _parse_transition

        assert _parse_transition(avec_workflow, action) is None


class TestGardeWorkflow:

    def test_une_transition_declaree_passe(self, avec_workflow: AdminResource) -> None:
        pytest.importorskip("forge_mvc_workflow")
        from forge_mvc_admin.http import _verifier_transition_workflow

        assert _verifier_transition_workflow(
            avec_workflow, ("brouillon", "publie")
        ) is None

    def test_une_transition_non_declaree_est_refusee(
        self, avec_workflow: AdminResource
    ) -> None:
        pytest.importorskip("forge_mvc_workflow")
        from forge_mvc_admin.http import _verifier_transition_workflow

        refus = _verifier_transition_workflow(avec_workflow, ("a", "b"))

        assert refus is not None and "non déclarée" in refus

    def test_sans_workflow_installe_la_transition_est_refusee(
        self, avec_workflow: AdminResource, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Le refus diffère de la suppression, et c'est délibéré.

        Appliquer un changement de statut à N lignes sans pouvoir vérifier que
        la transition est déclarée écrirait un état que le workflow interdit
        peut-être, sur cinquante lignes d'un coup.
        """
        import builtins

        from forge_mvc_admin.http import _verifier_transition_workflow

        vrai_import = builtins.__import__

        def _sans_workflow(nom: str, *a: Any, **k: Any) -> Any:
            if nom.startswith("forge_mvc_workflow"):
                raise ImportError(nom)
            return vrai_import(nom, *a, **k)

        monkeypatch.setattr(builtins, "__import__", _sans_workflow)
        refus = _verifier_transition_workflow(avec_workflow, ("brouillon", "publie"))

        assert refus is not None and "forge-mvc-workflow" in refus

    def test_une_condition_de_workflow_refuse_avec_son_motif(
        self, avec_workflow: AdminResource
    ) -> None:
        """Le motif remonte jusqu'à l'écran, comme pour une transition unitaire."""
        pytest.importorskip("forge_mvc_workflow")
        from forge_mvc_workflow import clear_conditions, register_condition

        from forge_mvc_admin.http import _verifier_transition_workflow

        clear_conditions()
        register_condition(lambda d, v, ctx: "le stock doit être vérifié")
        try:
            refus = _verifier_transition_workflow(avec_workflow, ("brouillon", "publie"))
        finally:
            clear_conditions()

        assert refus is not None and "stock" in refus

    def test_la_condition_recoit_le_contexte_groupe(
        self, avec_workflow: AdminResource
    ) -> None:
        """Une règle peut vouloir refuser en masse ce qu'elle permet à l'unité."""
        pytest.importorskip("forge_mvc_workflow")
        from forge_mvc_workflow import clear_conditions, register_condition

        from forge_mvc_admin.http import _verifier_transition_workflow

        vus: "list[dict[str, Any]]" = []
        clear_conditions()
        register_condition(lambda d, v, ctx: vus.append(ctx) or None)
        try:
            _verifier_transition_workflow(avec_workflow, ("brouillon", "publie"))
        finally:
            clear_conditions()

        assert vus and vus[0]["bulk"] is True
        assert vus[0]["resource"] == "articles"


class TestRoutesCablees:

    def _routes(self) -> "list[tuple[str, str]]":
        import tempfile

        import core.forge as forge

        dossier = tempfile.mkdtemp()
        forge.configure(app_name="T", app_env="dev", views_dir=dossier, sql_dir=dossier)
        from forge_mvc_admin.http import register_admin_routes

        posees: "list[tuple[str, str]]" = []

        class _Router:
            def add(self, methode: str, chemin: str, handler: Any, **kw: Any) -> None:
                posees.append((methode, chemin))

        register_admin_routes(_Router())  # type: ignore[arg-type]
        return posees

    def test_les_trois_routes_groupees_existent(self) -> None:
        """La première livraison n'avait posé QUE la fonction de requête :
        depuis le back-office, elle était inatteignable."""
        posees = self._routes()

        assert ("POST", "/admin/{slug}/bulk") in posees
        assert ("POST", "/admin/{slug}/bulk-delete") in posees
        assert ("POST", "/admin/{slug}/bulk-transition") in posees

    def test_elles_sont_toutes_en_post(self) -> None:
        """La sélection est longue, et une URL de plusieurs centaines
        d'identifiants serait tronquée avant d'arriver. Le CSRF s'applique
        donc, par défaut du routeur."""
        groupees = [
            (m, c) for m, c in self._routes() if "bulk" in c
        ]

        assert groupees
        assert all(methode == "POST" for methode, _ in groupees)


class TestGabarits:

    def _rendu(self, nom: str, **contexte: Any) -> str:
        from jinja2 import Environment, FileSystemLoader

        from forge_mvc_admin import http as module

        racine = Path(module.__file__).parent / "templates"
        env = Environment(loader=FileSystemLoader(str(racine)), autoescape=True)
        env.globals["csrf_token"] = "jeton"
        return env.get_template(nom).render(**contexte)

    def test_sans_action_declaree_aucune_case_a_cocher(self) -> None:
        r = AdminResource(
            entity="A", slug="a", label="A", plural_label="As",
            list_fields=("id",), form_fields=("id",), table="a",
        )
        rendu = self._rendu(
            "admin/list.html", resource=r, columns=("id",), rows=[{"id": 1}],
            pagination={"page": 1, "nb_pages": 1, "has_prev": False, "has_next": False},
        )

        assert 'name="ids"' not in rendu

    def test_avec_action_declaree_la_case_apparait(
        self, avec_workflow: AdminResource
    ) -> None:
        rendu = self._rendu(
            "admin/list.html", resource=avec_workflow, columns=("id", "titre"),
            rows=[{"id": 1, "titre": "x"}],
            pagination={"page": 1, "nb_pages": 1, "has_prev": False, "has_next": False},
        )

        assert 'name="ids"' in rendu
        assert 'value="transition:brouillon:publie"' in rendu
        assert 'name="csrf_token"' in rendu

    def test_la_confirmation_reporte_la_selection_telle_quelle(
        self, avec_workflow: AdminResource
    ) -> None:
        """La page de confirmation ne doit pas élargir ce qui a été coché."""
        rendu = self._rendu(
            "admin/bulk.html", resource=avec_workflow, columns=("id",),
            rows=[{"id": 1}], ids=["1", "2"], action="delete",
            transition=None, manquantes=1,
        )

        assert rendu.count('name="ids"') == 2
        assert "irréversible" in rendu

    def test_la_confirmation_dit_les_lignes_disparues(
        self, avec_workflow: AdminResource
    ) -> None:
        rendu = self._rendu(
            "admin/bulk.html", resource=avec_workflow, columns=("id",),
            rows=[{"id": 1}], ids=["1", "2"], action="delete",
            transition=None, manquantes=1,
        )

        assert "n'existent plus" in rendu


class TestRowsByPk:

    def test_une_ligne_disparue_n_est_pas_une_erreur(
        self, ressource: AdminResource
    ) -> None:
        """Elle a pu être supprimée entre l'affichage de la liste et la
        validation."""
        from forge_mvc_admin.query import rows_by_pk

        def _fetch_all(sql: str, params: Any) -> "list[dict[str, Any]]":
            return [{"id": 1}]

        assert rows_by_pk(ressource, _fetch_all, pk_values=["1", "2"]) == [{"id": 1}]

    def test_une_selection_vide_ne_touche_pas_la_base(
        self, ressource: AdminResource
    ) -> None:
        from forge_mvc_admin.query import rows_by_pk

        def _interdit(sql: str, params: Any) -> "list[dict[str, Any]]":
            raise AssertionError("la base ne doit pas être interrogée")

        assert rows_by_pk(ressource, _interdit, pk_values=[]) == []


class TestDocumentationSansContradiction:

    def test_la_garde_rbac_est_decrite_fail_closed_partout(self) -> None:
        """Une documentation qui annonce une ouverture là où le code ferme fait
        chercher une faille qui n'existe pas, et inversement."""
        from forge_mvc_admin import http as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        avant_les_notes = source.split("Ce paragraphe écrivait")[0]

        assert "fail-open" not in avant_les_notes
