"""`FIXTURES-SCENARIOS-001`, `FIXTURES-SNAPSHOT-001`, `FIXTURES-FK-ORDER-ROBUST-001`.

Le tri topologique existait, et se rabattait **en silence** sur l'ordre
alphabétique dans trois cas. Le repli est raisonnable ; le silence ne l'est
pas : le chargement échouait sur une violation de clé étrangère, et rien ne
reliait cette erreur à l'ordre qui l'avait causée.

Un fichier de fixtures pouvait par ailleurs écrire dans plusieurs tables, et
l'ordre n'en regardait que la première.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from forge_mvc_fixtures.ordering import (
    fk_dependencies,
    plan_fixture_order,
    tables_written_by,
    topological_order,
)
from forge_mvc_fixtures.scenarios import (
    SUGGESTED_SCENARIOS,
    ScenarioError,
    available_scenarios,
    select_scenario_files,
)
from forge_mvc_fixtures.snapshot import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    SnapshotError,
    TableSnapshot,
    render_insert,
    render_snapshot,
    snapshot_table,
)


class _Dialecte:
    def render_literal(self, value: object) -> str:
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, (int, float)):
            return str(value)
        return "'" + str(value).replace("'", "''") + "'"

    def limit_clause(self) -> str:
        return " LIMIT ?"


class _Db:
    def __init__(self, lignes: "list[dict[str, Any]]") -> None:
        self.lignes = lignes
        self.sql: "str | None" = None
        self.params: Any = None

    def fetch_all(self, sql: str, params: Any) -> "list[dict[str, Any]]":
        self.sql = sql
        self.params = params
        return list(self.lignes)


@pytest.fixture
def projet(tmp_path: Path) -> Path:
    (tmp_path / "mvc" / "entities").mkdir(parents=True)
    (tmp_path / "mvc" / "fixtures").mkdir()
    return tmp_path


def _relations(projet: Path, relations: "list[dict[str, str]]") -> None:
    (projet / "mvc" / "entities" / "relations.json").write_text(
        json.dumps({"relations": relations}), encoding="utf-8"
    )


# ---------------------------------------------- FIXTURES-FK-ORDER-ROBUST


class TestTablesEcrites:

    def test_toutes_les_tables_sont_lues(self, projet: Path) -> None:
        """L'ordre ne regardait que le PREMIER `INSERT INTO`.

        Un fichier insérant dans `articles` puis `commentaires` était classé
        comme s'il ne touchait qu'`articles`, et pouvait passer avant le
        fichier dont `commentaires` dépend.
        """
        fichier = projet / "mvc" / "fixtures" / "a.sql"
        fichier.write_text(
            "INSERT INTO articles VALUES (1);\nINSERT INTO commentaires VALUES (1);",
            encoding="utf-8",
        )

        assert tables_written_by(fichier) == ("articles", "commentaires")

    def test_les_doublons_ne_comptent_qu_une_fois(self, projet: Path) -> None:
        fichier = projet / "mvc" / "fixtures" / "a.sql"
        fichier.write_text("INSERT INTO t VALUES (1);\nINSERT INTO t VALUES (2);")

        assert tables_written_by(fichier) == ("t",)

    def test_la_casse_est_normalisee(self, projet: Path) -> None:
        """`Articles` et `articles` désignent la même table sur les quatre
        backends, et les distinguer casserait le rapprochement."""
        fichier = projet / "mvc" / "fixtures" / "a.sql"
        fichier.write_text("INSERT INTO Articles VALUES (1);")

        assert tables_written_by(fichier) == ("articles",)

    def test_les_delimiteurs_de_chaque_backend_sont_absorbes(
        self, projet: Path
    ) -> None:
        fichier = projet / "mvc" / "fixtures" / "a.sql"
        fichier.write_text('INSERT INTO `t1` VALUES (1);\nINSERT INTO "t2" VALUES (1);')

        assert set(tables_written_by(fichier)) == {"t1", "t2"}

    def test_sans_insert_le_nom_de_fichier_sert_de_repli(self, projet: Path) -> None:
        fichier = projet / "mvc" / "fixtures" / "clients.sql"
        fichier.write_text("-- rien")

        assert tables_written_by(fichier) == ("clients",)


class TestDiagnosticDeLOrdre:

    def test_un_graphe_complet_ne_dit_rien(self, projet: Path) -> None:
        _relations(projet, [{"type": "many_to_one", "from": "A", "to": "B"}])
        (projet / "mvc" / "fixtures" / "a.sql").write_text("INSERT INTO ta VALUES(1);")

        plan = plan_fixture_order(
            projet, [projet / "mvc" / "fixtures" / "a.sql"], {"A": "ta", "B": "tb"}
        )

        assert plan.ok
        assert plan.warnings == ()

    def test_relations_absent_est_dit(self, projet: Path) -> None:
        """Le silence faisait chercher dans les données un défaut du graphe."""
        plan = plan_fixture_order(projet, [], {})

        assert not plan.used_graph
        assert any("absent" in a for a in plan.warnings)

    def test_relations_illisible_est_distingue_d_absent(self, projet: Path) -> None:
        """Un fichier absent est normal, un fichier illisible est un défaut."""
        (projet / "mvc" / "entities" / "relations.json").write_text("{pas du json")

        _, avertissements, _ = fk_dependencies(projet)

        assert any("illisible" in a for a in avertissements)

    def test_un_cycle_est_nomme(self, projet: Path) -> None:
        """« cycle entre Article, Auteur » se corrige, « ordre non déduit » non."""
        deps = {"A": {"B"}, "B": {"A"}}

        ordre, avertissements = topological_order(deps)

        assert ordre is None
        assert "A" in avertissements[0] and "B" in avertissements[0]

    def test_une_table_sans_entite_est_signalee(self, projet: Path) -> None:
        _relations(projet, [{"type": "many_to_one", "from": "A", "to": "B"}])
        fichier = projet / "mvc" / "fixtures" / "inconnue.sql"
        fichier.write_text("INSERT INTO orpheline VALUES (1);")

        plan = plan_fixture_order(projet, [fichier], {"A": "ta", "B": "tb"})

        assert any("orpheline" in a for a in plan.warnings)

    def test_une_auto_reference_est_signalee(self, projet: Path) -> None:
        """L'ordre des lignes DANS le fichier compte, et aucun classement de
        fichiers ne peut le garantir."""
        _relations(projet, [{"type": "many_to_one", "from": "Categorie", "to": "Categorie"}])

        plan = plan_fixture_order(projet, [], {"Categorie": "categories"})

        assert plan.self_referencing == ("Categorie",)
        assert any("elle(s) même(s)" in a for a in plan.warnings)


class TestOrdreEffectif:

    def test_une_dependance_transitive_est_respectee(self, projet: Path) -> None:
        _relations(projet, [
            {"type": "many_to_one", "from": "Article", "to": "Categorie"},
            {"type": "many_to_one", "from": "Commentaire", "to": "Article"},
        ])
        base = projet / "mvc" / "fixtures"
        (base / "a_articles.sql").write_text(
            "INSERT INTO articles VALUES (1);\nINSERT INTO commentaires VALUES (1);"
        )
        (base / "z_categories.sql").write_text("INSERT INTO categories VALUES (1);")

        plan = plan_fixture_order(
            projet,
            sorted(base.glob("*.sql")),
            {"Article": "articles", "Categorie": "categories", "Commentaire": "commentaires"},
        )

        assert [p.name for p in plan.files] == ["z_categories.sql", "a_articles.sql"]

    def test_le_rang_le_plus_tardif_gouverne(self, projet: Path) -> None:
        """Classer sur la première table seule ferait passer le fichier avant
        celui dont sa seconde table dépend."""
        _relations(projet, [{"type": "many_to_one", "from": "Commentaire", "to": "Article"}])
        base = projet / "mvc" / "fixtures"
        (base / "aaa.sql").write_text(
            "INSERT INTO autre VALUES (1);\nINSERT INTO commentaires VALUES (1);"
        )
        (base / "bbb.sql").write_text("INSERT INTO articles VALUES (1);")

        plan = plan_fixture_order(
            projet, sorted(base.glob("*.sql")),
            {"Article": "articles", "Commentaire": "commentaires"},
        )

        assert [p.name for p in plan.files] == ["bbb.sql", "aaa.sql"]

    def test_le_repli_alphabetique_reste_deterministe(self, projet: Path) -> None:
        base = projet / "mvc" / "fixtures"
        for nom in ("02_b.sql", "01_a.sql"):
            (base / nom).write_text("INSERT INTO t VALUES(1);")

        plan = plan_fixture_order(projet, sorted(base.glob("*.sql")), {})

        assert [p.name for p in plan.files] == ["01_a.sql", "02_b.sql"]


# ------------------------------------------------------ FIXTURES-SCENARIOS


class TestJeuxNommes:

    @pytest.fixture
    def avec_scenarios(self, projet: Path) -> Path:
        base = projet / "mvc" / "fixtures"
        (base / "01_roles.sql").write_text("INSERT INTO roles VALUES (1);")
        (base / "demo").mkdir()
        (base / "demo" / "10_articles.sql").write_text("INSERT INTO articles VALUES(1);")
        (base / "test").mkdir()
        (base / "test" / "10_articles.sql").write_text("INSERT INTO articles VALUES(2);")
        return projet

    def test_sans_scenario_seul_le_jeu_commun(self, avec_scenarios: Path) -> None:
        """Comportement d'avant le ticket, inchangé."""
        selection = select_scenario_files(avec_scenarios)

        assert [p.name for p in selection.files] == ["01_roles.sql"]

    def test_le_commun_precede_le_scenario(self, avec_scenarios: Path) -> None:
        """Un scénario complète une base partagée au lieu de la réécrire."""
        selection = select_scenario_files(avec_scenarios, "demo")

        assert [p.name for p in selection.files] == ["01_roles.sql", "10_articles.sql"]

    def test_les_deux_provenances_restent_distinctes(
        self, avec_scenarios: Path
    ) -> None:
        """« 1 commun, 1 du scénario demo » se vérifie, « 2 fichiers » non."""
        selection = select_scenario_files(avec_scenarios, "demo")

        assert len(selection.common) == 1 and len(selection.scenario) == 1

    def test_les_scenarios_presents_sont_listes(self, avec_scenarios: Path) -> None:
        assert available_scenarios(avec_scenarios) == ("demo", "test")

    def test_un_dossier_vide_n_est_pas_un_scenario(self, avec_scenarios: Path) -> None:
        """Le proposer ferait croire à un jeu qui n'existe pas."""
        (avec_scenarios / "mvc" / "fixtures" / "vide").mkdir()

        assert "vide" not in available_scenarios(avec_scenarios)

    def test_un_dossier_souligne_est_ignore(self, avec_scenarios: Path) -> None:
        souligne = avec_scenarios / "mvc" / "fixtures" / "_notes"
        souligne.mkdir()
        (souligne / "a.sql").write_text("x")

        assert "_notes" not in available_scenarios(avec_scenarios)


class TestScenarioInconnu:
    """Le point qui compte."""

    def test_une_faute_de_frappe_leve(self, projet: Path) -> None:
        """`--scenario dmo` chargerait zéro fichier et annoncerait un succès :
        l'exploitant croirait ses données en place."""
        base = projet / "mvc" / "fixtures"
        (base / "demo").mkdir()
        (base / "demo" / "a.sql").write_text("x")

        with pytest.raises(ScenarioError, match="inconnu"):
            select_scenario_files(projet, "dmo")

    def test_le_message_liste_les_scenarios_presents(self, projet: Path) -> None:
        base = projet / "mvc" / "fixtures"
        (base / "demo").mkdir()
        (base / "demo" / "a.sql").write_text("x")

        with pytest.raises(ScenarioError, match="demo"):
            select_scenario_files(projet, "dmo")

    def test_un_scenario_vide_leve(self, projet: Path) -> None:
        (projet / "mvc" / "fixtures" / "vide").mkdir()

        with pytest.raises(ScenarioError, match="aucun fichier chargeable"):
            select_scenario_files(projet, "vide")

    @pytest.mark.parametrize("mauvais", ["../etc", "a/b", "", "  ", "A B"])
    def test_un_nom_invalide_leve(self, projet: Path, mauvais: str) -> None:
        """Le nom devient un dossier : il doit être un segment de chemin sûr."""
        with pytest.raises(ScenarioError, match="invalide"):
            select_scenario_files(projet, mauvais)

    def test_aucun_nom_n_est_reserve(self) -> None:
        """Imposer une liste fermée obligerait à un ticket pour chaque projet
        ayant un quatrième besoin."""
        assert SUGGESTED_SCENARIOS == ("demo", "test", "minimal")


class TestCommandeLoad:

    def test_le_scenario_se_lit_des_deux_facons(self, projet: Path) -> None:
        from forge_mvc_fixtures.cli.load import collect_fixture_files

        base = projet / "mvc" / "fixtures"
        (base / "demo").mkdir()
        (base / "demo" / "a.sql").write_text("INSERT INTO t VALUES(1);")

        assert len(collect_fixture_files(projet, "demo")) == 1
        assert collect_fixture_files(projet) == []


# ------------------------------------------------------- FIXTURES-SNAPSHOT


class TestInstantane:

    def test_il_rend_les_lignes_de_la_table(self) -> None:
        db = _Db([{"id": 1, "nom": "A"}])

        instantane = snapshot_table("clients", db=db, dialect=_Dialecte())

        assert instantane.rows == ({"id": 1, "nom": "A"},)
        assert instantane.columns == ("id", "nom")

    def test_il_demande_une_ligne_de_plus_pour_savoir(self) -> None:
        """Rendre un instantané tronqué qui ressemble à un instantané complet
        est le défaut que ce contrôle évite."""
        db = _Db([{"id": i} for i in range(5)])

        instantane = snapshot_table("t", limit=2, db=db, dialect=_Dialecte())

        assert db.params == (3,)
        assert instantane.truncated is True
        assert len(instantane.rows) == 2

    def test_une_table_vide_n_est_pas_une_erreur(self) -> None:
        instantane = snapshot_table("t", db=_Db([]), dialect=_Dialecte())

        assert instantane.is_empty
        assert not instantane.truncated

    def test_le_tri_est_optionnel_et_valide(self) -> None:
        db = _Db([{"id": 1}])

        snapshot_table("t", order_by="id", db=db, dialect=_Dialecte())

        assert db.sql is not None and "ORDER BY id" in db.sql

    @pytest.mark.parametrize(
        "mauvais", ["clients; DROP TABLE x", "", "../etc", "a b", "1abc"]
    )
    def test_un_nom_de_table_invalide_leve(self, mauvais: str) -> None:
        """Le nom vient de la ligne de commande et entre dans une requête :
        aucun backend n'accepte un nom de table en paramètre lié."""
        with pytest.raises(SnapshotError, match="invalide"):
            snapshot_table(mauvais, db=_Db([]), dialect=_Dialecte())

    def test_un_tri_invalide_leve_aussi(self) -> None:
        with pytest.raises(SnapshotError):
            snapshot_table("t", order_by="id; DROP TABLE x", db=_Db([]), dialect=_Dialecte())

    @pytest.mark.parametrize("mauvais", [0, -1, MAX_LIMIT + 1, "50", True])
    def test_un_plafond_invalide_leve(self, mauvais: Any) -> None:
        with pytest.raises(SnapshotError):
            snapshot_table("t", limit=mauvais, db=_Db([]), dialect=_Dialecte())

    def test_le_plafond_par_defaut_reste_une_amorce(self) -> None:
        """Une table de cent mille lignes n'a rien à faire dans mvc/fixtures/."""
        assert DEFAULT_LIMIT == 50
        assert MAX_LIMIT == 1000


class TestRendu:

    def test_les_valeurs_passent_par_le_dialecte(self) -> None:
        """ADR-075 : le littéral est du SQL visible, réservé aux artefacts relus."""
        rendu = render_insert(
            "t", ("id", "nom", "actif", "note"),
            {"id": 1, "nom": "L'aîné", "actif": True, "note": None},
            _Dialecte(),
        )

        assert rendu == "INSERT INTO t (id, nom, actif, note) VALUES (1, 'L''aîné', 1, NULL);"

    def test_l_apostrophe_est_echappee(self) -> None:
        rendu = render_insert("t", ("n",), {"n": "L'été"}, _Dialecte())

        assert "'L''été'" in rendu

    def test_l_en_tete_previent_du_contenu(self) -> None:
        """Un fichier de fixtures est relu des mois plus tard, souvent par
        quelqu'un d'autre, et rien dans un INSERT ne dit qu'il vient d'une base
        réelle."""
        rendu = render_snapshot(
            TableSnapshot("t", ("id",), ({"id": 1},)), _Dialecte()
        )

        assert "RELISEZ" in rendu
        assert "données personnelles" in rendu

    def test_la_troncature_est_dite_dans_le_fichier(self) -> None:
        rendu = render_snapshot(
            TableSnapshot("t", ("id",), ({"id": 1},), truncated=True), _Dialecte()
        )

        assert "TRONQUÉ" in rendu

    def test_une_table_vide_le_dit_au_lieu_de_rendre_rien(self) -> None:
        rendu = render_snapshot(TableSnapshot("t", (), ()), _Dialecte())

        assert "vide" in rendu
        assert "INSERT INTO" not in rendu, "aucune instruction ne doit être produite"


class TestCommandeSnapshot:

    def test_une_table_est_exigee(self) -> None:
        from forge_mvc_fixtures.cli.snapshot import parse_options

        assert parse_options([]).error is not None

    def test_une_option_inconnue_est_une_erreur(self) -> None:
        from forge_mvc_fixtures.cli.snapshot import parse_options

        assert parse_options(["t", "--limitt", "5"]).error is not None

    @pytest.mark.parametrize("argv", [["t", "--limit", "5"], ["t", "--limit=5"]])
    def test_les_deux_ecritures_sont_lues(self, argv: list[str]) -> None:
        from forge_mvc_fixtures.cli.snapshot import parse_options

        assert parse_options(argv).limit == 5

    def test_un_plafond_non_entier_est_une_erreur(self) -> None:
        from forge_mvc_fixtures.cli.snapshot import parse_options

        assert parse_options(["t", "--limit", "beaucoup"]).error is not None

    def test_il_affiche_par_defaut(self) -> None:
        from forge_mvc_fixtures.cli.snapshot import parse_options

        assert parse_options(["t"]).out is None

    def test_la_production_est_refusee_sans_force(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """La sortie vient d'une base réelle et finit dans un dépôt Git."""
        from forge_mvc_fixtures.cli import snapshot as module

        monkeypatch.setenv("APP_ENV", "prod")

        assert module.main(["clients"]) == 2
        assert "Refus" in capsys.readouterr().err

    def test_un_fichier_existant_n_est_pas_ecrase(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from forge_mvc_fixtures.cli import snapshot as module

        monkeypatch.setenv("APP_ENV", "dev")
        cible = tmp_path / "deja.sql"
        cible.write_text("-- precieux", encoding="utf-8")
        monkeypatch.setattr(
            module, "snapshot_table",
            lambda *a, **k: TableSnapshot("t", ("id",), ({"id": 1},)),
        )
        monkeypatch.setattr(
            "core.database.backend.get_backend",
            lambda: type("B", (), {"dialect": _Dialecte()})(),
        )

        code = module.main(["t", "--out", str(cible)])

        assert code == 1
        assert cible.read_text(encoding="utf-8") == "-- precieux"
        assert "existe déjà" in capsys.readouterr().err
