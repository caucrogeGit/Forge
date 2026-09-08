"""Cinq contrats de données qui changeaient de sens en cours de route.

Une revue externe des 27 opt-ins a relevé une famille cohérente : une donnée
écrite d'un côté n'était pas relue de la même façon de l'autre.

- `stats` : le filtre normalisait la catégorie, l'écriture non.
- `import-export` : les cellules au-delà de l'en-tête disparaissaient sans un mot.
- `audit` : la borne de période perdait son fuseau.
- `sessions-db` : l'aller-retour d'horodatage dépendait du fuseau du serveur.
- `admin` : la transition groupée n'écrivait pas `updated_at`.

Aucun ne fait échouer quoi que ce soit. C'est ce qui les rend coûteux : la
valeur est simplement fausse, et le reste.
"""
from __future__ import annotations

import os
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest


class TestStatsCategorie:
    """`STATS-CATEGORY-NORMALISATION-001` — écrire et chercher la même valeur."""

    @pytest.fixture
    def base(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute(
            "CREATE TABLE forge_stats_events "
            "(name TEXT, label TEXT, category TEXT, metadata TEXT, kind TEXT)"
        )
        return conn

    @pytest.mark.parametrize(
        "saisie", [" cours ", "cours ", " cours", "cours"],
        ids=["deux-cotes", "a-droite", "a-gauche", "propre"],
    )
    def test_l_aller_retour_trouve_l_evenement(self, saisie: str, base) -> None:
        """Un événement écrit avec des espaces était introuvable par son filtre."""
        pytest.importorskip("forge_mvc_stats")
        from forge_mvc_stats.aggregate import count_stats_events
        from forge_mvc_stats.tracking import track_event

        def execute(sql: str, params=()):
            curseur = base.execute(sql, params)
            base.commit()
            return curseur.rowcount

        def fetch_all(sql: str, params=()):
            return [dict(r) for r in base.execute(sql, params).fetchall()]

        track_event(execute, "view", category=saisie)

        assert count_stats_events(fetch_all, "name", category=saisie) != []
        assert count_stats_events(fetch_all, "name", category="cours") != []

    def test_une_categorie_vide_vaut_le_defaut(self) -> None:
        pytest.importorskip("forge_mvc_stats")
        from forge_mvc_stats.events import normalize_category

        assert normalize_category("   ") == "general"
        assert normalize_category("") == "general"


class TestCsvLigneTropLongue:
    """`IMPEXP-CSV-LIGNE-TROP-LONGUE-001` — un import qui perd des données s'arrête."""

    def test_une_cellule_excedentaire_est_refusee(self) -> None:
        """`nom,note` puis `Alice,12,5` rendait `{"nom": "Alice", "note": "12"}`."""
        pytest.importorskip("forge_mvc_import_export")
        from forge_mvc_import_export.csv_reader import CsvImportError, parse_csv

        with pytest.raises(CsvImportError, match="Ligne 2"):
            parse_csv("nom,note\nAlice,12,5\n")

    def test_le_message_nomme_la_ligne_et_les_comptes(self) -> None:
        """Sans le numéro, il faut chercher dans un fichier de milliers de lignes."""
        pytest.importorskip("forge_mvc_import_export")
        from forge_mvc_import_export.csv_reader import CsvImportError, parse_csv

        with pytest.raises(CsvImportError) as capture:
            parse_csv("a,b\n1,2\n3,4,5\n")

        message = str(capture.value)
        assert "Ligne 3" in message
        assert "3 cellules" in message and "2 colonnes" in message

    def test_une_ligne_courte_reste_acceptee(self) -> None:
        """Le contrat d'avant : les colonnes absentes valent la chaîne vide."""
        pytest.importorskip("forge_mvc_import_export")
        from forge_mvc_import_export.csv_reader import parse_csv

        assert parse_csv("nom,note\nAlice\n") == [{"nom": "Alice", "note": ""}]

    def test_une_ligne_normale_passe(self) -> None:
        pytest.importorskip("forge_mvc_import_export")
        from forge_mvc_import_export.csv_reader import parse_csv

        assert parse_csv("nom,note\nAlice,12\n") == [{"nom": "Alice", "note": "12"}]


class TestAuditBornePeriode:
    """`AUDIT-BORNE-PERIODE-UTC-001` — la borne est exprimée dans le fuseau du journal."""

    def test_une_date_avec_fuseau_est_convertie(self) -> None:
        """`12:00+02:00` devenait la borne `12:00:00`, au lieu de `10:00:00`."""
        pytest.importorskip("forge_mvc_audit")
        from forge_mvc_audit.store import _borne_periode

        valeur = datetime(2026, 9, 8, 12, tzinfo=timezone(timedelta(hours=2)))

        assert _borne_periode(valeur, "since") == "2026-09-08 10:00:00"

    def test_une_date_naive_est_tenue_pour_utc(self) -> None:
        """Supposer le fuseau du serveur ferait dépendre l'export de la machine."""
        pytest.importorskip("forge_mvc_audit")
        from forge_mvc_audit.store import _borne_periode

        assert _borne_periode(datetime(2026, 9, 8, 12), "since") == "2026-09-08 12:00:00"

    @pytest.mark.parametrize("decalage", [-8, -2, 0, 2, 5])
    def test_tous_les_fuseaux_ramenent_au_meme_instant(self, decalage: int) -> None:
        pytest.importorskip("forge_mvc_audit")
        from forge_mvc_audit.store import _borne_periode

        valeur = datetime(2026, 9, 8, 12, tzinfo=timezone(timedelta(hours=decalage)))
        attendu = (valeur - timedelta(hours=decalage)).strftime("%Y-%m-%d %H:%M:%S")

        assert _borne_periode(valeur, "since") == attendu


class TestSessionsHorodatage:
    """`SESSIONS-DB-HORODATAGE-UTC-001` — l'aller-retour ne dépend pas du serveur."""

    @pytest.fixture
    def fuseau(self):
        """Rend le fuseau du processus après le test, quel qu'ait été le sien."""
        ancien = os.environ.get("TZ")
        yield
        if ancien is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = ancien
        time.tzset()

    @pytest.mark.parametrize("tz", ["Europe/Paris", "UTC", "America/New_York", "Asia/Tokyo"])
    def test_l_aller_retour_est_neutre(self, tz: str, fuseau) -> None:
        """Sous `TZ=Europe/Paris`, l'aller-retour décalait de 7 200 secondes."""
        pytest.importorskip("forge_mvc_sessions_db")
        from forge_mvc_sessions_db.store import _dt, _horodatage

        os.environ["TZ"] = tz
        time.tzset()
        instant = 1788840000.0

        assert _horodatage(_dt(instant)) == instant


class TestAdminTransitionHorodatee:
    """`ADMIN-TRANSITION-TIMESTAMPS-001` — une transition modifie, donc elle horodate."""

    @pytest.fixture
    def base(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE demo (id INTEGER PRIMARY KEY, status TEXT, updated_at TEXT)")
        conn.execute("INSERT INTO demo VALUES (1, 'draft', '2000-01-01 00:00:00')")
        conn.commit()
        return conn

    @staticmethod
    def _execute(base):
        def execute(sql: str, params=()):
            curseur = base.execute(sql, params)
            base.commit()
            return curseur.rowcount
        return execute

    def test_la_transition_groupee_met_a_jour_l_horodatage(self, base) -> None:
        """Un tri par date de modification plaçait la ligne au mauvais endroit."""
        pytest.importorskip("forge_mvc_admin")
        from forge_mvc_admin.query import transition_rows

        ressource = SimpleNamespace(
            table="demo", pk="id", status_field="status", slug="demo", timestamps=True
        )

        assert transition_rows(
            ressource, self._execute(base), pk_values=[1],
            from_status="draft", to_status="done",
        ) == 1

        ligne = dict(base.execute("SELECT * FROM demo").fetchone())
        assert ligne["status"] == "done"
        assert ligne["updated_at"] != "2000-01-01 00:00:00"

    def test_une_ressource_sans_horodatage_n_en_gagne_pas(self, base) -> None:
        """La colonne n'existe pas forcément : l'écrire ferait échouer la transition."""
        pytest.importorskip("forge_mvc_admin")
        from forge_mvc_admin.query import transition_rows

        ressource = SimpleNamespace(
            table="demo", pk="id", status_field="status", slug="demo", timestamps=False
        )

        assert transition_rows(
            ressource, self._execute(base), pk_values=[1],
            from_status="draft", to_status="done",
        ) == 1

        ligne = dict(base.execute("SELECT * FROM demo").fetchone())
        assert ligne["updated_at"] == "2000-01-01 00:00:00"

    def test_la_garde_sur_le_statut_de_depart_tient_toujours(self, base) -> None:
        """C'est elle qui protège d'un changement concurrent : ne pas la perdre."""
        pytest.importorskip("forge_mvc_admin")
        from forge_mvc_admin.query import transition_rows

        ressource = SimpleNamespace(
            table="demo", pk="id", status_field="status", slug="demo", timestamps=True
        )

        assert transition_rows(
            ressource, self._execute(base), pk_values=[1],
            from_status="published", to_status="done",
        ) == 0
