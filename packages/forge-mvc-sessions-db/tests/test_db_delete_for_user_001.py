"""SESSIONS-DELETE-FOR-USER-001, côté store BDD.

Contrairement aux stores mémoire et fichier, celui-ci est partagé entre
processus et sa table peut être grande : la révocation passe par une colonne
`user_id` indexée, écrite à chaque écriture de session, et non par un balayage
qui se dégraderait avec le trafic.

La migration d'ajout de colonne est vérifiée sur les quatre dialectes : les
projets provisionnés avant ce ticket ont la table sans la colonne, et la
migration de création ne se rejoue pas.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_sessions_db")

from core.database.table_ddl import AddColumn, render_add_column  # noqa: E402
from core.sessions.keys import SESSION_KEY_AUTH_USER_ID as CLE_UTILISATEUR  # noqa: E402
from forge_mvc_sessions_db.store import _user_id_of  # noqa: E402
from forge_mvc_sessions_db.tables import FORGE_SESSIONS, MIGRATIONS  # noqa: E402

BACKENDS = ["forge_mvc_sqlite", "forge_mvc_mariadb", "forge_mvc_postgres", "forge_mvc_mssql"]


def _dialecte(nom_module: str) -> object:
    module = importlib.import_module(f"{nom_module}.dialect")
    classe = next(
        objet for objet in vars(module).values()
        if isinstance(objet, type)
        and objet.__name__.endswith("Dialect")
        and objet.__module__ == module.__name__
    )
    return classe()


class TestSchema:
    def test_la_colonne_existe_et_est_indexee(self) -> None:
        noms = [c.name for c in FORGE_SESSIONS.columns]
        assert "user_id" in noms

        indexes = [i.column_list for i in FORGE_SESSIONS.indexes]
        assert "user_id" in indexes, "sans index, la révocation balaie la table"

    def test_la_colonne_est_nullable(self) -> None:
        """Les lignes existantes n'ont pas d'identité, et les sessions anonymes non plus."""
        colonne = next(c for c in FORGE_SESSIONS.columns if c.name == "user_id")
        assert colonne.nullable

    def test_une_migration_ajoute_la_colonne_aux_projets_existants(self) -> None:
        """La migration de création ne se rejoue pas : son empreinte est enregistrée."""
        ajouts = [d for _, d in MIGRATIONS if isinstance(d, AddColumn)]
        assert len(ajouts) == 1
        assert ajouts[0].column_name == "user_id"

    def test_les_noms_de_migration_restent_ordonnes(self) -> None:
        noms = [nom for nom, _ in MIGRATIONS]
        assert noms == sorted(noms), "l'ordre d'application suit l'horodatage du nom"


class TestMigrationPortable:
    @pytest.mark.parametrize("backend", BACKENDS)
    def test_l_ajout_se_rend_sur_les_quatre_dialectes(self, backend: str) -> None:
        pytest.importorskip(backend)
        instructions = render_add_column(FORGE_SESSIONS, "user_id", _dialecte(backend))

        assert instructions, f"aucune instruction rendue pour {backend}"
        # La clause vient du dialecte : SQL Server écrit `ADD`, les trois autres
        # `ADD COLUMN`, le mot-clé y étant une erreur de syntaxe.
        assert instructions[0].startswith("ALTER TABLE forge_sessions ADD")
        assert "user_id" in instructions[0]
        assert instructions[0].rstrip().endswith(";")

    @pytest.mark.parametrize("backend", BACKENDS)
    def test_l_index_est_cree_separement(self, backend: str) -> None:
        """Un ALTER ne porte pas d'index, y compris sur les dialectes qui les inlinent."""
        pytest.importorskip(backend)
        instructions = render_add_column(FORGE_SESSIONS, "user_id", _dialecte(backend))

        assert any("idx_forge_sessions_user_id" in i for i in instructions)

    @pytest.mark.parametrize("backend", BACKENDS)
    def test_l_index_de_l_autre_colonne_n_est_pas_recree(self, backend: str) -> None:
        """Seuls les index de la colonne ajoutée sont rendus."""
        pytest.importorskip(backend)
        instructions = render_add_column(FORGE_SESSIONS, "user_id", _dialecte(backend))

        assert not any("idx_forge_sessions_expire_at" in i for i in instructions)


class TestExtractionDeLIdentite:
    @pytest.mark.parametrize(
        ("session", "attendu"),
        [
            ({}, None),
            ({CLE_UTILISATEUR: None}, None),
            ({CLE_UTILISATEUR: 42}, "42"),
            ({CLE_UTILISATEUR: "42"}, "42"),
            ({CLE_UTILISATEUR: "alice"}, "alice"),
            ({"authenticated": True, "user": {"id": 7}}, None),
        ],
    )
    def test_rendu_en_texte(self, session: dict[str, object], attendu: str | None) -> None:
        """Entier ou chaîne, l'identité est écrite de la même façon dans la colonne."""
        assert _user_id_of(session) == attendu


class TestRevocation:
    def test_une_seule_requete_indexee(self) -> None:
        """Le store ne charge pas la table pour révoquer."""
        from forge_mvc_sessions_db import store as module

        appels: list[tuple[str, tuple[object, ...]]] = []

        instance = module.DbSessionStore(
            fetch_one=lambda sql, params: None,
            execute=lambda sql, params=(): (appels.append((sql, params)), 3)[1],
        )
        supprimes = instance.delete_for_user(7)

        assert supprimes == 3
        assert len(appels) == 1
        sql, params = appels[0]
        assert sql.startswith("DELETE FROM forge_sessions WHERE user_id =")
        assert params == ("7",)

    def test_epargner_une_session_ajoute_la_garde_a_la_requete(self) -> None:
        """La session épargnée est écartée en SQL, pas après coup en Python."""
        from forge_mvc_sessions_db import store as module

        appels: list[tuple[str, tuple[object, ...]]] = []
        instance = module.DbSessionStore(
            fetch_one=lambda sql, params: None,
            execute=lambda sql, params=(): (appels.append((sql, params)), 2)[1],
        )

        assert instance.delete_for_user(7, except_session_id="abc") == 2
        sql, params = appels[0]
        assert "session_id <> ?" in sql
        assert params == ("7", "abc")

    def test_identite_absente_ne_touche_pas_la_base(self) -> None:
        from forge_mvc_sessions_db import store as module

        appels: list[str] = []
        instance = module.DbSessionStore(
            fetch_one=lambda sql, params: None,
            execute=lambda sql, params=(): (appels.append(sql), 0)[1],
        )

        assert instance.delete_for_user(None) == 0
        assert appels == [], "aucune requête ne doit partir pour une identité absente"


class TestRevocationBoutEnBout:
    """Écriture puis révocation, à travers le double fidèle au schéma."""

    def test_seules_les_sessions_du_compte_tombent(self) -> None:
        from forge_mvc_sessions_db.store import DbSessionStore

        # Les tests de paquet ne forment pas un package importable : on charge
        # le double par son chemin, comme la convention le fait ailleurs.
        import importlib.util
        import sys

        chemin = Path(__file__).with_name("test_db_store_001.py")
        spec = importlib.util.spec_from_file_location("_db_store_double", chemin)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules["_db_store_double"] = module
        spec.loader.exec_module(module)

        faux = module._FakeDB()
        store = DbSessionStore(fetch_one=faux.fetch_one, execute=faux.execute)

        cible = store.create()
        donnees = store.get(cible)
        assert donnees is not None
        donnees[CLE_UTILISATEUR] = 7
        store.set(cible, donnees)

        voisine = store.create()
        autre = store.get(voisine)
        assert autre is not None
        autre[CLE_UTILISATEUR] = 9
        store.set(voisine, autre)

        anonyme = store.create()

        assert store.delete_for_user(7) == 1
        assert store.get(cible) is None
        assert store.get(voisine) is not None
        assert store.get(anonyme) is not None

    def test_la_session_epargnee_survit(self) -> None:
        from forge_mvc_sessions_db.store import DbSessionStore

        import importlib.util
        import sys

        chemin = Path(__file__).with_name("test_db_store_001.py")
        spec = importlib.util.spec_from_file_location("_db_store_double_bis", chemin)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules["_db_store_double_bis"] = module
        spec.loader.exec_module(module)

        faux = module._FakeDB()
        store = DbSessionStore(fetch_one=faux.fetch_one, execute=faux.execute)

        courante, autre = store.create(), store.create()
        for sid in (courante, autre):
            donnees = store.get(sid)
            assert donnees is not None
            donnees[CLE_UTILISATEUR] = 7
            store.set(sid, donnees)

        assert store.delete_for_user(7, except_session_id=courante) == 1
        assert store.get(courante) is not None
        assert store.get(autre) is None
