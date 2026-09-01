"""MAIL-QUEUE-VIA-JOBS-001 : confier l'envoi d'email à la file de tâches.

Envoyer un email pendant une requête HTTP la fait attendre le serveur SMTP.
Une seconde de latence est courante, dix le sont aussi quand le relais est
lent, et une panne du relais devient une panne du formulaire : l'utilisateur
voit une erreur alors que son inscription est enregistrée.

Les deux opt-ins restent indépendants : `forge-mvc-mail` n'importe jamais
`forge_mvc_jobs`, et c'est l'application qui les met en présence.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("forge_mvc_mail")

from forge_mvc_mail import (  # noqa: E402
    MAIL_JOB_TASK,
    FakeTransport,
    Mailer,
    MailMessage,
    MailPayloadError,
    make_mail_job_handler,
    message_from_payload,
    message_to_payload,
)
from forge_mvc_mail.exceptions import MailError  # noqa: E402
from forge_mvc_mail.transports import BaseTransport, TransportResult  # noqa: E402


def _message() -> MailMessage:
    return MailMessage(
        subject="Bienvenue", to=["a@b.fr", "c@d.fr"],
        body_text="Bonjour", cc="e@f.fr",
    )


class TestIndependanceDesOptIns:
    def test_mail_n_importe_jamais_jobs(self) -> None:
        """Un opt-in ne peut pas dépendre d'un autre.

        Le contrôle passe par l'AST et non par le texte : le docstring du
        module montre l'exemple `from forge_mvc_jobs import enqueue`, qu'une
        lecture ligne à ligne prendrait pour un import réel.
        """
        import ast

        from forge_mvc_mail import queueing

        arbre = ast.parse(Path(queueing.__file__).read_text(encoding="utf-8"))
        modules: list[str] = []
        for noeud in ast.walk(arbre):
            if isinstance(noeud, ast.Import):
                modules.extend(alias.name for alias in noeud.names)
            elif isinstance(noeud, ast.ImportFrom) and noeud.module:
                modules.append(noeud.module)

        assert not any(module.startswith("forge_mvc_jobs") for module in modules)

    def test_le_nom_de_tache_est_nomme_une_fois(self) -> None:
        """La mise en file et le gestionnaire désignent la même."""
        assert MAIL_JOB_TASK == "mail.send"


class TestChargeUtile:
    def test_la_charge_est_serialisable_en_json(self) -> None:
        """`enqueue` sérialise la charge : un objet non JSON la ferait échouer."""
        charge = message_to_payload(_message())
        assert json.loads(json.dumps(charge)) == charge

    def test_l_aller_retour_preserve_le_message(self) -> None:
        refait = message_from_payload(message_to_payload(_message()))

        assert refait.subject == "Bienvenue"
        assert refait.to_addresses == ["a@b.fr", "c@d.fr"]
        assert refait.cc_addresses == ["e@f.fr"]
        assert refait.body_text == "Bonjour"

    def test_les_champs_de_journalisation_suivent(self) -> None:
        """Sans eux, différer un envoi rendrait le journal muet."""
        charge = message_to_payload(
            _message(), message_type="bienvenue",
            related_entity="contact", related_id=42,
        )
        assert charge["message_type"] == "bienvenue"
        assert charge["related_entity"] == "contact"
        assert charge["related_id"] == 42

    def test_les_champs_de_journalisation_absents_ne_sont_pas_transportes(self) -> None:
        charge = message_to_payload(_message())
        assert "message_type" not in charge
        assert "related_id" not in charge

    def test_les_adresses_derivees_ne_sont_pas_transportees(self) -> None:
        """Les transporter ferait deux sources pour la même information."""
        charge = message_to_payload(_message())
        assert "to_addresses" not in charge

    def test_un_message_invalide_est_refuse_a_la_mise_en_file(self) -> None:
        """Différer l'erreur jusqu'à l'ouvrier la rendrait invisible."""
        with pytest.raises(Exception):
            message_to_payload(MailMessage(subject="", to="a@b.fr", body_text="x"))


class TestChargeInexploitable:
    @pytest.mark.parametrize("charge", [{}, {"subject": "x"}, {"to": "a@b.fr"}])
    def test_une_charge_incomplete_est_refusee(self, charge: dict[str, Any]) -> None:
        with pytest.raises(MailPayloadError):
            message_from_payload(charge)

    def test_le_motif_du_refus_est_conserve(self) -> None:
        """Une charge d'une version antérieure doit dire pourquoi elle est refusée."""
        with pytest.raises(MailPayloadError) as capture:
            message_from_payload({"subject": "x", "to": "a@b.fr"})
        assert capture.value.__cause__ is not None

    def test_une_charge_qui_n_est_pas_un_dictionnaire_est_refusee(self) -> None:
        with pytest.raises(MailPayloadError):
            message_from_payload("pas un dict")  # type: ignore[arg-type]


class TestGestionnaire:
    def test_l_envoi_part_par_le_transport(self) -> None:
        transport = FakeTransport()
        handler = make_mail_job_handler(mailer=Mailer(transport))

        handler(message_to_payload(_message()))

        assert len(transport.messages) == 1
        assert transport.messages[0].subject == "Bienvenue"

    def test_un_echec_leve_pour_declencher_le_reessai(self) -> None:
        """Rendre None ferait marquer la tâche réussie, et l'email ne partirait jamais."""
        class _Refus(BaseTransport):
            def send(self, message: MailMessage) -> TransportResult:
                return TransportResult(success=False, transport="refus", detail="relais injoignable")

        handler = make_mail_job_handler(mailer=Mailer(_Refus()))

        with pytest.raises(MailError, match="relais injoignable"):
            handler(message_to_payload(_message()))

    def test_un_envoi_saute_n_est_pas_un_echec(self) -> None:
        """`NullTransport` désactive le mail : réessayer sans fin serait absurde."""
        from forge_mvc_mail import NullTransport

        handler = make_mail_job_handler(mailer=Mailer(NullTransport()))
        handler(message_to_payload(_message()))

    def test_les_champs_de_journalisation_sont_transmis_a_l_envoi(self) -> None:
        vus: list[dict[str, Any]] = []

        class _Espion:
            @staticmethod
            def send(message: MailMessage, **kwargs: Any) -> TransportResult:
                vus.append(kwargs)
                return TransportResult(success=True, transport="espion")

        handler = make_mail_job_handler(mailer=_Espion())
        handler(message_to_payload(_message(), message_type="bienvenue", related_id=42))

        assert vus[0]["message_type"] == "bienvenue"
        assert vus[0]["related_id"] == 42

    def test_l_envoyeur_n_est_construit_qu_au_premier_appel(self) -> None:
        """Un ouvrier qui enregistre ses gestionnaires ne doit pas lire la config."""
        make_mail_job_handler()  # ne doit rien construire, donc ne pas lever


class TestParcoursComplet:
    """Mise en file puis traitement, comme le motif officiel le décrit."""

    def test_de_la_mise_en_file_a_l_envoi(self) -> None:
        pytest.importorskip("forge_mvc_jobs")
        from forge_mvc_jobs.queue import enqueue, process_one

        import importlib.util
        import sys

        chemin = (
            Path(__file__).resolve().parent.parent.parent
            / "forge-mvc-jobs" / "tests" / "test_jobs_queue_001.py"
        )
        spec = importlib.util.spec_from_file_location("_jobs_double_mail", chemin)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules["_jobs_double_mail"] = module
        spec.loader.exec_module(module)

        faux = module.FakeDb()
        transport = FakeTransport()

        enqueue(MAIL_JOB_TASK, message_to_payload(_message()), db=faux)
        assert transport.messages == [], "rien ne doit partir pendant la requête"

        traitee = process_one(
            {MAIL_JOB_TASK: make_mail_job_handler(mailer=Mailer(transport))}, db=faux
        )

        assert traitee is True
        assert len(transport.messages) == 1
        assert transport.messages[0].subject == "Bienvenue"
