"""Fixtures callable : import du code applicatif et ordre fournit/dépend
(FIXTURES-CALLABLE-002, ADR-078 ; retour terrain F49/F50).

F49 : une fixture callable peut importer mvc.… (racine du projet dans sys.path).
F50 : une unité qui dépend d'une table passe après toute unité qui la fournit,
que le fournisseur soit un .sql ou un callable.
"""
from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_fixtures")

from forge_mvc_fixtures.cli.load import (
    collect_callable_fixtures,
    collect_fixture_files,
    load_fixtures,
    order_load_units,
)
from forge_mvc_fixtures.cli.purge import purge_fixtures


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_entity(root: Path, snake: str, name: str, table: str) -> None:
    _write(
        root, f"mvc/entities/{snake}/{snake}.json",
        json.dumps({"name": name, "table": table, "fields": []}),
    )


def _write_relations(root: Path, relations: list[dict]) -> None:
    _write(
        root, "mvc/entities/relations.json",
        json.dumps({"schema_version": "1.0", "relations": relations}),
    )


def _vient_d_un_projet_jetable(module: object, racines: list[str]) -> bool:
    """Dit si un module a été chargé depuis l'un des projets fabriqués du test.

    Le critère est le **chemin** du module, et les racines sont les entrées que
    le test a ajoutées à ``sys.path`` : ce sont exactement les projets qu'il a
    fabriqués. Un module sans ``__file__`` (paquet natif ou d'espace de noms)
    n'en vient pas.
    """
    chemin = getattr(module, "__file__", None)
    if not isinstance(chemin, str):
        return False
    resolu = Path(chemin).resolve()
    return any(resolu.is_relative_to(Path(racine).resolve()) for racine in racines)


@pytest.fixture
def isolated_imports() -> Iterator[None]:
    """Isole les imports du test.

    Un autre test (dans le même worker xdist) peut avoir laissé un module ``mvc``
    en cache, pointant vers un autre projet : on l'évince au setup, on le restaure
    au teardown, et on retire les modules chargés depuis les projets que le test a
    fabriqués.

    Le teardown évinçait auparavant **tout** module apparu pendant le test.
    Mesuré : un seul ``from forge_mvc_fixtures.cli.load import …`` en amène 31,
    dont ``core``, ``core.app.env``, ``core.database.sql_script`` et des modules
    de la bibliothèque standard (``ast``, ``typing``, ``dataclasses``,
    ``inspect``). Les évincer les fait réimporter au test suivant, ce qui rend
    l'état de module réinitialisé et fait coexister **deux classes distinctes
    portant le même nom** : un ``except`` sur l'ancienne ne rattrape pas la
    nouvelle, et l'erreur qui en résulte ne désigne pas sa cause
    (``FIXTURES-ISOLATION-PORTEE-001``).

    La fixture retire donc ce qu'elle annonce retirer : les modules du projet
    jetable, reconnus au chemin dont ils viennent.
    """
    saved_path = list(sys.path)
    stashed = {
        name: module
        for name, module in list(sys.modules.items())
        if name == "mvc" or name.startswith("mvc.")
    }
    for name in stashed:
        del sys.modules[name]
    try:
        yield
    finally:
        # Relevé avant de restaurer `sys.path` : ce sont les projets du test.
        racines = [chemin for chemin in sys.path if chemin not in saved_path]
        sys.path[:] = saved_path
        for name, module in list(sys.modules.items()):
            if name == "mvc" or name.startswith("mvc."):
                del sys.modules[name]
            elif racines and _vient_d_un_projet_jetable(module, racines):
                del sys.modules[name]
        sys.modules.update(stashed)


class TestF49AppImport:

    def _make_project(self, root: Path) -> None:
        _write(root, "mvc/__init__.py", "")
        _write(root, "mvc/services/__init__.py", "")
        _write(
            root, "mvc/services/importer.py",
            "def do_import(db):\n    db.execute('INSERT INTO ref (x) VALUES (1)')\n",
        )
        src = (
            "from forge_mvc_fixtures import Fixture\n"
            "from core.database import db\n"
            "from mvc.services.importer import do_import\n"
            "class RefFixture(Fixture):\n"
            "    tables = ('ref',)\n"
            "    def load(self, *, tx=None):\n"
            "        do_import(db)\n"
        )
        _write(root, "mvc/fixtures/referentiel.py", src)

    def test_discovery_imports_app_module(
        self, tmp_path: Path, isolated_imports: None
    ) -> None:
        self._make_project(tmp_path)
        found = collect_callable_fixtures(tmp_path)
        assert len(found) == 1
        assert found[0][1].__name__ == "RefFixture"

    def test_run_executes_callable_using_app_code(
        self, tmp_path: Path, isolated_imports: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._make_project(tmp_path)
        calls: list[str] = []
        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", lambda sql, *a, **k: calls.append(sql) or 0)
        rc = load_fixtures(tmp_path, run=True, force=False, env="dev")
        assert rc == 0
        assert calls == ["INSERT INTO ref (x) VALUES (1)"]


class TestF50ProviderOrder:

    def _make_seed(self, root: Path) -> None:
        # AnneeScolaire <- Classe -> NiveauClasse ; niveau_classe fourni par un callable.
        _write_entity(root, "annee_scolaire", "AnneeScolaire", "annee_scolaire")
        _write_entity(root, "niveau_classe", "NiveauClasse", "niveau_classe")
        _write_entity(root, "classe", "Classe", "classe")
        _write_relations(root, [
            {"type": "many_to_one", "from": "Classe", "to": "AnneeScolaire",
             "name": "annee_scolaire"},
            {"type": "many_to_one", "from": "Classe", "to": "NiveauClasse",
             "name": "niveau_classe"},
        ])
        _write(root, "mvc/fixtures/annee.sql",
               "INSERT INTO annee_scolaire (Libelle) VALUES ('2024');")
        _write(root, "mvc/fixtures/classe.sql",
               "INSERT INTO classe (Nom, NiveauClasseId) VALUES "
               "('CP', (SELECT Id FROM niveau_classe WHERE Code = 'CP' LIMIT 1));")
        src = (
            "from forge_mvc_fixtures import Fixture\n"
            "class ReferentielFixture(Fixture):\n"
            "    tables = ('niveau_classe',)\n"
            "    def load(self, *, tx=None): ...\n"
        )
        _write(root, "mvc/fixtures/referentiel.py", src)

    def test_callable_provider_before_dependent_sql(self, tmp_path: Path) -> None:
        self._make_seed(tmp_path)
        units = order_load_units(
            tmp_path, collect_fixture_files(tmp_path), collect_callable_fixtures(tmp_path)
        )
        order = [u.path.name for u in units]
        # annee_scolaire (dépendance) avant tout ; referentiel fournit niveau_classe
        # AVANT classe.sql qui en dépend par FK.
        assert order.index("annee.sql") < order.index("referentiel.py")
        assert order.index("referentiel.py") < order.index("classe.sql")

    def test_load_runs_provider_before_dependent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._make_seed(tmp_path)
        calls: list[str] = []
        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", lambda sql, *a, **k: calls.append(sql) or 0)
        rc = load_fixtures(tmp_path, run=True, force=False, env="dev")
        assert rc == 0
        # annee insérée, puis classe (le referentiel callable n'exécute aucun SQL ici,
        # mais il est ordonné avant classe : la FK niveau_classe serait satisfaite).
        assert calls == [
            "INSERT INTO annee_scolaire (Libelle) VALUES ('2024')",
            "INSERT INTO classe (Nom, NiveauClasseId) VALUES "
            "('CP', (SELECT Id FROM niveau_classe WHERE Code = 'CP' LIMIT 1))",
        ]


class TestF51ReferenceOrder:
    """F51 : une reference() vers une table hors relations.json est une dépendance."""

    def _make(self, root: Path) -> None:
        # comptes.py (callable) fournit users ; eleve.sql y référence users par
        # sous-requête (reference("users", …)). users n'est pas une entité mvc/.
        _write(
            root, "mvc/fixtures/comptes.py",
            "from forge_mvc_fixtures import Fixture\n"
            "from core.database import db\n"
            "class ComptesFixture(Fixture):\n"
            "    tables = ('users', 'user_roles')\n"
            "    def load(self, *, tx=None):\n"
            "        db.execute(\"INSERT INTO users (email) VALUES ('a@b.fr')\")\n",
        )
        _write(
            root, "mvc/fixtures/eleve.sql",
            "INSERT INTO eleve (Nom, UserId) VALUES "
            "('Dupont', (SELECT Id FROM users WHERE email = 'a@b.fr' LIMIT 1));",
        )

    def test_reference_orders_after_provider(self, tmp_path: Path) -> None:
        self._make(tmp_path)
        units = order_load_units(
            tmp_path, collect_fixture_files(tmp_path), collect_callable_fixtures(tmp_path)
        )
        order = [u.path.name for u in units]
        # eleve.sql référence users (fourni par comptes.py) : chargé après.
        assert order.index("comptes.py") < order.index("eleve.sql")

    def test_load_runs_provider_before_reference(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._make(tmp_path)
        calls: list[str] = []
        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", lambda sql, *a, **k: calls.append(sql) or 0)
        rc = load_fixtures(tmp_path, run=True, force=False, env="dev")
        assert rc == 0
        # comptes.load() crée users AVANT l'INSERT eleve qui le référence.
        assert calls == [
            "INSERT INTO users (email) VALUES ('a@b.fr')",
            "INSERT INTO eleve (Nom, UserId) VALUES "
            "('Dupont', (SELECT Id FROM users WHERE email = 'a@b.fr' LIMIT 1))",
        ]


class TestF52PurgeReverseOrder:
    """F52 : purge dans l'ordre inverse EXACT du chargement (enfants avant parents)."""

    def _make(self, root: Path) -> None:
        # annee_scolaire (parent) <- affectation_professeur_classe (enfant, FK).
        _write_entity(root, "annee_scolaire", "AnneeScolaire", "annee_scolaire")
        _write_entity(
            root, "affectation_professeur_classe",
            "AffectationProfesseurClasse", "affectation_professeur_classe",
        )
        _write_relations(root, [
            {"type": "many_to_one", "from": "AffectationProfesseurClasse",
             "to": "AnneeScolaire", "name": "annee_scolaire"},
        ])
        _write(root, "mvc/fixtures/annee.sql",
               "INSERT INTO annee_scolaire (Libelle) VALUES ('2025-2026');")
        _write(root, "mvc/fixtures/affectation.sql",
               "INSERT INTO affectation_professeur_classe (AnneeScolaireId) VALUES "
               "((SELECT Id FROM annee_scolaire WHERE Libelle = '2025-2026' LIMIT 1));")

    def test_purge_deletes_child_before_parent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._make(tmp_path)
        calls: list[str] = []
        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", lambda sql, *a, **k: calls.append(sql) or 0)
        rc = purge_fixtures(tmp_path, run=True, force=False, env="dev")
        assert rc == 0
        # enfant (affectation) supprimé avant le parent (annee_scolaire) ; on filtre
        # la (dés)activation FK encadrante pour rester indépendant du backend.
        assert [s for s in calls if s.upper().startswith("DELETE")] == [
            "DELETE FROM affectation_professeur_classe",
            "DELETE FROM annee_scolaire",
        ]

    def test_purge_is_exact_reverse_of_load(self, tmp_path: Path) -> None:
        self._make(tmp_path)
        load_order = [
            u.path.name for u in order_load_units(
                tmp_path, collect_fixture_files(tmp_path), collect_callable_fixtures(tmp_path)
            )
        ]
        assert load_order == ["annee.sql", "affectation.sql"]


class TestF52ForeignKeyWrap:
    """F52 (complément) : la purge encadre le démontage par la désactivation FK,
    robuste face à un callable multi-tables dont l'ordre interne viole ses FK."""

    def test_purge_brackets_deletes_with_fk_toggle(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Dialecte factice : statements FK déterministes, quel que soit le backend.
        class _Dialect:
            def foreign_key_checks_ddl(self, *, enabled: bool) -> list[str]:
                return [f"SET FOREIGN_KEY_CHECKS = {1 if enabled else 0}"]

        class _Backend:
            dialect = _Dialect()

        import core.database.backend as backend_mod
        monkeypatch.setattr(backend_mod, "get_backend", lambda: _Backend())

        # Callable multi-tables : pivot déclaré AVANT la table qu'il référence,
        # donc reversed(tables) donnerait le mauvais ordre. La désactivation FK
        # rend le démontage robuste malgré cela.
        src = (
            "from forge_mvc_fixtures import Fixture\n"
            "from core.database import db\n"
            "class RefFixture(Fixture):\n"
            "    tables = ('referentiel_niveau_classe', 'niveau_classe')\n"
            "    def load(self, *, tx=None): ...\n"
        )
        _write(tmp_path, "mvc/fixtures/referentiel.py", src)

        calls: list[str] = []
        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", lambda sql, *a, **k: calls.append(sql) or 0)
        rc = purge_fixtures(tmp_path, run=True, force=False, env="dev")
        assert rc == 0
        # Encadrement : désactivation en tête, réactivation en fin.
        assert calls[0] == "SET FOREIGN_KEY_CHECKS = 0"
        assert calls[-1] == "SET FOREIGN_KEY_CHECKS = 1"
        # Toutes les tables déclarées sont vidées.
        deletes = [s for s in calls if s.startswith("DELETE")]
        assert set(deletes) == {
            "DELETE FROM referentiel_niveau_classe",
            "DELETE FROM niveau_classe",
        }

    def test_all_statements_share_one_transaction(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # F52-bis : SET FOREIGN_KEY_CHECKS est une variable de session (par
        # connexion). Tout le démontage (SET, DELETE des .sql ET des callable)
        # doit passer par le MÊME tx, sinon chaque db.execute repioche une
        # connexion du pool où les FK restent actives.
        class _Dialect:
            def foreign_key_checks_ddl(self, *, enabled: bool) -> list[str]:
                return [f"SET FOREIGN_KEY_CHECKS = {1 if enabled else 0}"]

        class _Backend:
            dialect = _Dialect()

        import core.database.backend as backend_mod
        monkeypatch.setattr(backend_mod, "get_backend", lambda: _Backend())

        # un callable multi-tables + un .sql : les deux doivent partager le tx.
        _write(
            tmp_path, "mvc/fixtures/referentiel.py",
            "from forge_mvc_fixtures import Fixture\n"
            "class RefFixture(Fixture):\n"
            "    tables = ('a', 'b')\n"
            "    def load(self, *, tx=None): ...\n",
        )
        _write(tmp_path, "mvc/fixtures/ville.sql", "INSERT INTO ville (nom) VALUES ('Lyon');")

        seen_tx: list[object] = []

        def execute(sql: str, params: object = (), *, tx: object = None) -> int:
            seen_tx.append(tx)
            return 0

        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", execute)
        rc = purge_fixtures(tmp_path, run=True, force=False, env="dev")
        assert rc == 0
        # Au moins : SET=0, DELETE b, DELETE a (callable), DELETE ville (.sql), SET=1.
        assert len(seen_tx) >= 5
        assert all(tx is not None for tx in seen_tx)
        # Toutes les instructions partagent le même objet transaction (une connexion).
        assert len({id(tx) for tx in seen_tx}) == 1

    def test_fk_reenabled_even_on_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _Dialect:
            def foreign_key_checks_ddl(self, *, enabled: bool) -> list[str]:
                return ["SET FOREIGN_KEY_CHECKS = 1" if enabled else "SET FOREIGN_KEY_CHECKS = 0"]

        class _Backend:
            dialect = _Dialect()

        import core.database.backend as backend_mod
        monkeypatch.setattr(backend_mod, "get_backend", lambda: _Backend())

        _write(tmp_path, "mvc/fixtures/ville.sql", "INSERT INTO ville (nom) VALUES ('Lyon');")
        calls: list[str] = []

        def execute(sql: str, *a: object, **k: object) -> int:
            calls.append(sql)
            if sql.startswith("DELETE"):
                raise RuntimeError("boom")
            return 0

        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", execute)
        rc = purge_fixtures(tmp_path, run=True, force=False, env="dev")
        assert rc == 1
        # Réactivation FK garantie même en cas d'erreur (finally).
        assert calls[-1] == "SET FOREIGN_KEY_CHECKS = 1"


class TestPorteeDeLIsolation:
    """`FIXTURES-ISOLATION-PORTEE-001` — ce que le teardown retire, et ce qu'il garde.

    Le teardown évinçait **tout** module apparu pendant le test. Un seul import
    du CLI de fixtures en amène 31, dont `core`, `core.app.env`,
    `core.database.sql_script` et des modules de la bibliothèque standard.

    Les réimporter fait coexister deux classes distinctes portant le même nom :
    un `except` posé sur l'ancienne ne rattrape pas la nouvelle, et l'erreur qui
    en résulte ne désigne pas sa cause. La suite était verte, ce qui rendait le
    défaut latent plutôt qu'absent.

    Les témoins sont **injectés dans `sys.modules`** plutôt que choisis parmi
    les modules réels : un module du framework est déjà chargé au moment où la
    fixture prend son instantané, si bien que le retirer puis le réimporter ne
    le rend pas « nouveau ». Un premier garde-fou écrit ainsi ne tombait pas sur
    l'ancien comportement, donc ne gardait rien.

    Les deux méthodes s'exécutent dans leur ordre de définition ; la seconde
    observe l'état laissé par le teardown de la première, et ne prend donc pas
    la fixture.
    """

    #: Ne vient d'aucun projet : il doit survivre au teardown.
    HORS_PROJET = "_temoin_isolation_hors_projet"

    def test_1_charge_un_projet_jetable_et_un_module_etranger(
        self, tmp_path: Path, isolated_imports: None
    ) -> None:
        import importlib
        import types

        _write(tmp_path, "mvc/__init__.py", "")
        _write(tmp_path, "mvc/services/__init__.py", "")
        _write(tmp_path, "mvc/services/marqueur.py", "VALEUR = 1\n")
        sys.path.insert(0, str(tmp_path))
        importlib.import_module("mvc.services.marqueur")

        # Apparaît pendant le test, sans venir du projet fabriqué.
        sys.modules[self.HORS_PROJET] = types.ModuleType(self.HORS_PROJET)

        assert "mvc.services.marqueur" in sys.modules
        assert self.HORS_PROJET in sys.modules

    def test_2_le_projet_est_retire_l_etranger_reste(self) -> None:
        etranger_present = self.HORS_PROJET in sys.modules
        sys.modules.pop(self.HORS_PROJET, None)

        assert "mvc.services.marqueur" not in sys.modules, (
            "le module du projet jetable survit au test : un test suivant qui "
            "importe `mvc.…` lirait le projet du précédent"
        )
        assert etranger_present, (
            "le teardown a évincé un module qui ne venait pas du projet "
            "fabriqué : appliqué au framework, le prochain qui l'importe en "
            "obtient une seconde instance, et deux classes de même nom cessent "
            "d'être la même classe"
        )
