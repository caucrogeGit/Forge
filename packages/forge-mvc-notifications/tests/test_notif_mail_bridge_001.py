"""NOTIF-MAIL-BRIDGE-001 : doubler une notification par un autre canal.

Une notification in-app n'est vue que si son destinataire revient sur le site.
Pour une alerte qui compte, une facture impayée ou un incident, c'est trop tard,
et l'opt-in n'offrait aucun moyen de doubler le canal.

Chaque application réécrivait la même chose à côté de `notify`, et l'y oubliait
à un endroit sur trois : la notification partait, l'email non, et personne ne
s'en apercevait avant la réclamation.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("forge_mvc_notifications")

from forge_mvc_notifications import (  # noqa: E402
    NotificationEvent,
    clear_notification_relays,
    notification_relays,
    notify,
    on_notification_created,
)


class _FauxDb:
    def __init__(self) -> None:
        self.lignes: list[Any] = []

    def insert(self, sql: str, params: Any) -> int:
        self.lignes.append(params)
        return len(self.lignes)


@pytest.fixture(autouse=True)
def _sans_relais():
    clear_notification_relays()
    yield
    clear_notification_relays()


class TestEnregistrement:
    def test_rien_ne_relaie_par_defaut(self) -> None:
        """Une notification ne part sur aucun autre canal sans demande explicite."""
        assert notification_relays() == ()

    def test_un_relais_enregistre_est_appele(self) -> None:
        vus: list[NotificationEvent] = []
        on_notification_created(vus.append)

        notify("roger", "Facture impayée", type="alerte", db=_FauxDb())

        assert len(vus) == 1
        assert vus[0].recipient == "roger"

    def test_l_enregistrement_s_utilise_en_decorateur(self) -> None:
        vus: list[NotificationEvent] = []

        @on_notification_created
        def relais(evenement: NotificationEvent) -> None:
            vus.append(evenement)

        notify("roger", "Message", db=_FauxDb())
        assert len(vus) == 1

    def test_l_ordre_d_enregistrement_est_conserve(self) -> None:
        ordre: list[str] = []
        on_notification_created(lambda e: ordre.append("premier"))
        on_notification_created(lambda e: ordre.append("second"))

        notify("roger", "Message", db=_FauxDb())

        assert ordre == ["premier", "second"]


class TestEvenement:
    def test_l_identifiant_ecrit_est_transmis(self) -> None:
        """Un relais doit pouvoir retrouver la notification."""
        vus: list[NotificationEvent] = []
        on_notification_created(vus.append)

        identifiant = notify("roger", "Message", db=_FauxDb())

        assert vus[0].notification_id == identifiant

    def test_le_complement_de_donnees_suit(self) -> None:
        """Un relais compose souvent son message à partir de ce complément."""
        vus: list[NotificationEvent] = []
        on_notification_created(vus.append)

        notify("roger", "Facture", data={"facture": 12}, db=_FauxDb())

        assert vus[0].data == {"facture": 12}

    def test_le_type_permet_de_filtrer(self) -> None:
        """Toutes les notifications ne méritent pas un email."""
        alertes: list[str] = []
        on_notification_created(
            lambda e: alertes.append(e.message) if e.type == "alerte" else None
        )
        faux = _FauxDb()

        notify("roger", "Information", type="info", db=faux)
        notify("roger", "Incident", type="alerte", db=faux)

        assert alertes == ["Incident"]

    def test_l_evenement_est_immuable(self) -> None:
        evenement = NotificationEvent(notification_id=1, recipient="r", message="m")
        with pytest.raises(Exception):
            evenement.recipient = "autre"  # type: ignore[misc]

    def test_les_donnees_sont_copiees(self) -> None:
        """Un relais ne doit pas modifier le dictionnaire de l'appelant."""
        origine = {"facture": 12}
        on_notification_created(lambda e: e.data.update({"ajoute": True}))

        notify("roger", "Message", data=origine, db=_FauxDb())

        assert origine == {"facture": 12}


class TestIsolation:
    def test_un_relais_qui_leve_n_annule_pas_la_notification(self) -> None:
        """Elle est déjà en base : faire échouer `notify` mentirait à l'appelant."""
        on_notification_created(
            lambda e: (_ for _ in ()).throw(RuntimeError("relais SMTP mort"))
        )
        faux = _FauxDb()

        identifiant = notify("roger", "Message", db=faux)

        assert identifiant == 1
        assert len(faux.lignes) == 1

    def test_un_relais_qui_leve_n_empeche_pas_les_suivants(self) -> None:
        vus: list[str] = []
        on_notification_created(lambda e: (_ for _ in ()).throw(RuntimeError("boum")))
        on_notification_created(lambda e: vus.append("second"))

        notify("roger", "Message", db=_FauxDb())

        assert vus == ["second"]

    def test_l_erreur_du_relais_est_journalisee(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        on_notification_created(lambda e: (_ for _ in ()).throw(RuntimeError("boum")))

        with caplog.at_level("WARNING"):
            notify("roger", "Message", db=_FauxDb())

        assert "Relais de notification en erreur" in caplog.text

    def test_une_notification_refusee_n_annonce_rien(self) -> None:
        """L'annonce suit l'écriture : rien n'a été écrit, rien n'est annoncé."""
        vus: list[NotificationEvent] = []
        on_notification_created(vus.append)

        with pytest.raises(Exception):
            notify("", "Message", db=_FauxDb())

        assert vus == []


class TestSansDependance:
    def test_notifications_n_importe_aucun_autre_opt_in(self) -> None:
        from forge_mvc_notifications import relays

        arbre = ast.parse(Path(relays.__file__).read_text(encoding="utf-8"))
        modules: list[str] = []
        for noeud in ast.walk(arbre):
            if isinstance(noeud, ast.Import):
                modules.extend(alias.name for alias in noeud.names)
            elif isinstance(noeud, ast.ImportFrom) and noeud.module:
                modules.append(noeud.module)

        interdits = [
            m for m in modules
            if m.startswith("forge_mvc_") and "notifications" not in m
        ]
        assert interdits == [], f"dépendance vers un autre opt-in : {interdits}"


class TestPontCompletVersEmail:
    """Le motif que la référence donne à copier, joué de bout en bout."""

    def test_une_alerte_part_en_file_puis_en_email(self) -> None:
        pytest.importorskip("forge_mvc_jobs")
        pytest.importorskip("forge_mvc_mail")

        import importlib.util
        import sys

        from forge_mvc_jobs.queue import enqueue, process_one
        from forge_mvc_mail import (
            MAIL_JOB_TASK,
            FakeTransport,
            Mailer,
            MailMessage,
            make_mail_job_handler,
            message_to_payload,
        )

        chemin = (
            Path(__file__).resolve().parent.parent.parent
            / "forge-mvc-jobs" / "tests" / "test_jobs_queue_001.py"
        )
        spec = importlib.util.spec_from_file_location("_jobs_double_notif", chemin)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules["_jobs_double_notif"] = module
        spec.loader.exec_module(module)

        file = module.FakeDb()
        transport = FakeTransport()

        @on_notification_created
        def doubler_par_email(evenement: NotificationEvent) -> None:
            if evenement.type != "alerte":
                return
            enqueue(MAIL_JOB_TASK, message_to_payload(MailMessage(
                subject=f"Alerte : {evenement.message}",
                to="roger@example.test",
                body_text=evenement.message,
            )), db=file)

        notify("roger", "Information", type="info", db=_FauxDb())
        notify("roger", "Facture impayée", type="alerte", db=_FauxDb())

        assert transport.messages == [], "rien ne part pendant la requête"

        traitee = process_one(
            {MAIL_JOB_TASK: make_mail_job_handler(mailer=Mailer(transport))}, db=file
        )

        assert traitee is True
        assert len(transport.messages) == 1
        assert transport.messages[0].subject == "Alerte : Facture impayée"
