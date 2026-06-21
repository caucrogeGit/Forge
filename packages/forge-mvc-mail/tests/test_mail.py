import pytest

pytest.importorskip("forge_mvc_mail")
from forge_mvc_mail import MailMessage

# Note (MAIL-SMTPMAILER-REMOVE-001) : la couverture de l'envoi SMTP vit
# désormais entièrement dans test_mail_transports.py (classe SmtpTransport,
# voie officielle). L'ancien doublon SMTPMailer a été retiré (principe 11) ;
# ce fichier ne conserve que les tests de construction de MailMessage.


def test_creation_message_texte_seul():
    message = MailMessage(
        subject="Bienvenue",
        to="test@example.test",
        body_text="Bonjour",
        from_email="from@example.test",
    )
    email = message.as_email_message("from@example.test")

    assert email["Subject"] == "Bienvenue"
    assert email["To"] == "test@example.test"
    assert email.get_content().strip() == "Bonjour"


def test_creation_message_html_avec_alternative_texte():
    message = MailMessage(
        subject="Bienvenue",
        to="test@example.test",
        body_text="Bonjour",
        body_html="<p>Bonjour</p>",
    )
    email = message.as_email_message("from@example.test")

    assert email.is_multipart()
    parts = email.get_payload()
    assert parts[0].get_content_type() == "text/plain"
    assert parts[0].get_content().strip() == "Bonjour"
    assert parts[1].get_content_type() == "text/html"
    assert parts[1].get_content().strip() == "<p>Bonjour</p>"


def test_destinataire_unique():
    message = MailMessage(subject="Test", to="a@example.test", body_text="Bonjour")

    assert message.to_addresses == ["a@example.test"]


def test_liste_de_destinataires():
    message = MailMessage(
        subject="Test",
        to=["a@example.test", "b@example.test"],
        body_text="Bonjour",
    )

    assert message.to_addresses == ["a@example.test", "b@example.test"]
