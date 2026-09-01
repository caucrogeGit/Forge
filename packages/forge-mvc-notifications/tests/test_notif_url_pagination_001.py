"""NOTIF-TARGET-URL-001 et NOTIF-PAGINATION-001 : le lien et la page suivante.

Une notification annonce quelque chose, et l'utilisateur veut y aller. Le lien
n'avait pas de place : le ranger dans `data` marchait, mais rien ne l'y validait
alors qu'il finit dans un `href`.

Et la liste ne se paginait pas. Un `OFFSET` l'aurait fait de travers : une
notification arrivée entre deux pages décale tout ce qui suit, si bien que la
page 2 réafficherait la dernière ligne de la page 1 et en cacherait une autre.
Une liste de notifications est justement celle qui reçoit des écritures pendant
qu'on la parcourt.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_notifications")

from core.database.table_ddl import AddColumn  # noqa: E402
from forge_mvc_notifications import (  # noqa: E402
    NotificationError,
    clear_notification_relays,
    get_notifications,
    notify,
    validate_target_url,
)
from forge_mvc_notifications.tables import MIGRATIONS, NOTIFICATIONS  # noqa: E402


class _FauxDb:
    def __init__(self) -> None:
        self.insertions: list[Any] = []
        self.sql: list[str] = []
        self.params: list[Any] = []

    def insert(self, sql: str, params: Any) -> int:
        self.insertions.append(params)
        return len(self.insertions)

    def fetch_all(self, sql: str, params: Any) -> list[dict[str, Any]]:
        self.sql.append(sql)
        self.params.append(list(params))
        return []


@pytest.fixture(autouse=True)
def _sans_relais():
    clear_notification_relays()
    yield
    clear_notification_relays()


class TestLiensAcceptes:
    @pytest.mark.parametrize(
        "lien",
        ["/factures/12", "/", "https://exemple.test/a", "http://exemple.test",
         "HTTPS://EXEMPLE.TEST"],
    )
    def test_un_chemin_interne_ou_une_url_http_passe(self, lien: str) -> None:
        assert validate_target_url(lien) == lien

    def test_les_blancs_de_bord_sont_retires(self) -> None:
        assert validate_target_url("  /a  ") == "/a"

    @pytest.mark.parametrize("vide", [None, "", "   "])
    def test_un_lien_absent_reste_absent(self, vide: "str | None") -> None:
        assert validate_target_url(vide) is None


class TestLiensRefuses:
    """Le lien finit dans un `href`, et vient souvent d'une saisie."""

    @pytest.mark.parametrize(
        "hostile",
        ["javascript:alert(1)", "JavaScript:alert(1)", "  javascript:x",
         "data:text/html,<script>", "vbscript:x", "file:///etc/passwd"],
    )
    def test_un_schema_executable_est_refuse(self, hostile: str) -> None:
        with pytest.raises(NotificationError, match="Schéma"):
            validate_target_url(hostile)

    @pytest.mark.parametrize("hostile", ["java\tscript:x", "java\nscript:x", "java script:x"])
    def test_un_schema_coupe_par_un_blanc_est_refuse(self, hostile: str) -> None:
        """Certains navigateurs lisent `java<tab>script:` comme un schéma."""
        with pytest.raises(NotificationError):
            validate_target_url(hostile)

    def test_une_url_protocole_relative_est_refusee(self) -> None:
        """Elle emmène ailleurs tout en ressemblant à un chemin interne."""
        with pytest.raises(NotificationError, match="protocole-relatif"):
            validate_target_url("//ailleurs.test/piege")

    @pytest.mark.parametrize("hostile", ["factures/12", "exemple.test", "ftp://x"])
    def test_une_forme_inattendue_est_refusee(self, hostile: str) -> None:
        with pytest.raises(NotificationError, match="invalide"):
            validate_target_url(hostile)

    def test_un_lien_trop_long_est_refuse(self) -> None:
        """La colonne fait 500 : tronquer donnerait un lien cassé."""
        with pytest.raises(NotificationError, match="trop long"):
            validate_target_url("/" + "a" * 500)


class TestEcritureDuLien:
    def test_le_lien_valide_part_en_base(self) -> None:
        faux = _FauxDb()
        notify("roger", "Facture", target_url="/factures/12", db=faux)

        assert faux.insertions[0][-1] == "/factures/12"

    def test_sans_lien_la_colonne_reste_vide(self) -> None:
        faux = _FauxDb()
        notify("roger", "Message", db=faux)

        assert faux.insertions[0][-1] is None

    def test_un_lien_hostile_empeche_l_ecriture(self) -> None:
        """Refuser à l'écriture, pas à l'affichage : la ligne ne doit pas exister."""
        faux = _FauxDb()
        with pytest.raises(NotificationError):
            notify("roger", "Message", target_url="javascript:alert(1)", db=faux)

        assert faux.insertions == []


class TestSchema:
    def test_la_colonne_est_dediee_et_non_une_cle_de_data(self) -> None:
        """Une clé libre n'aurait jamais été validée."""
        noms = [c.name for c in NOTIFICATIONS.columns]
        assert "target_url" in noms

    def test_la_colonne_est_nullable(self) -> None:
        """Toutes les notifications n'ont pas de lien, et les anciennes non plus."""
        colonne = next(c for c in NOTIFICATIONS.columns if c.name == "target_url")
        assert colonne.nullable

    def test_une_migration_l_ajoute_aux_projets_existants(self) -> None:
        ajouts = [d for _, d in MIGRATIONS if isinstance(d, AddColumn)]
        assert len(ajouts) == 1
        assert ajouts[0].column_name == "target_url"


class TestPagination:
    def test_le_curseur_entre_dans_la_requete(self) -> None:
        faux = _FauxDb()
        get_notifications("roger", before_id=100, db=faux)

        assert "id < ?" in faux.sql[0]
        assert 100 in faux.params[0]

    def test_sans_curseur_aucune_clause(self) -> None:
        faux = _FauxDb()
        get_notifications("roger", db=faux)

        assert "id < ?" not in faux.sql[0]

    def test_le_curseur_se_combine_au_filtre_de_lecture(self) -> None:
        faux = _FauxDb()
        get_notifications("roger", unread_only=True, before_id=100, db=faux)

        assert "read_at IS NULL" in faux.sql[0]
        assert "id < ?" in faux.sql[0]

    def test_l_ordre_reste_du_plus_recent_au_plus_ancien(self) -> None:
        """C'est ce qui fait du curseur un « plus ancien que »."""
        faux = _FauxDb()
        get_notifications("roger", before_id=100, db=faux)

        assert "ORDER BY id DESC" in faux.sql[0]

    def test_aucun_offset_n_est_employe(self) -> None:
        """Un OFFSET répéterait une ligne dès qu'une notification arrive."""
        faux = _FauxDb()
        get_notifications("roger", before_id=100, db=faux)

        assert "OFFSET" not in faux.sql[0].upper()
