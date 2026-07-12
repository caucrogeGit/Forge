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


@pytest.fixture
def isolated_imports() -> Iterator[None]:
    """Isole les imports du test.

    Un autre test (dans le même worker xdist) peut avoir laissé un module ``mvc``
    en cache, pointant vers un autre projet : on l'évince au setup (et on le
    restaure au teardown), on restaure ``sys.path`` et on retire les modules
    importés pendant le test.
    """
    saved_path = list(sys.path)
    stashed = {
        name: module
        for name, module in list(sys.modules.items())
        if name == "mvc" or name.startswith("mvc.")
    }
    for name in stashed:
        del sys.modules[name]
    baseline = set(sys.modules)
    try:
        yield
    finally:
        sys.path[:] = saved_path
        for name in list(sys.modules):
            if name not in baseline:
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
            "    def load(self):\n"
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
            "    def load(self): ...\n"
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
            "    def load(self):\n"
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
            "    def load(self): ...\n"
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
