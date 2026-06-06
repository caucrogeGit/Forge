import smtplib

import pytest

import core.forge as forge
pytest.importorskip("forge_mvc_mail")
from forge_mvc_mail import MailConfigurationError, MailMessage, MailSendError, SMTPMailer


class FakeSMTP:
    instances = []

    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.started_tls = False
        self.login_args = None
        self.sent = []
        type(self).instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def starttls(self):
        self.started_tls = True

    def login(self, username, password):
        self.login_args = (username, password)

    def send_message(self, message, *, from_addr=None, to_addrs=None):
        self.sent.append((message, from_addr, list(to_addrs or [])))


class FailingSMTP(FakeSMTP):
    def send_message(self, message, *, from_addr=None, to_addrs=None):
        raise smtplib.SMTPException("boom")


@pytest.fixture(autouse=True)
def _mail_config(monkeypatch):
    snapshot = dict(forge._cfg)
    FakeSMTP.instances = []
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)
    forge.configure(
        mail_host="smtp.example.test",
        mail_port=2525,
        mail_username="",
        mail_password="",
        mail_from="default@example.test",
        mail_use_tls=False,
        mail_use_ssl=False,
        mail_timeout=3,
        mail_enabled=True,
    )
    yield
    forge._cfg.clear()
    forge._cfg.update(snapshot)


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


def test_from_email_explicite_prioritaire():
    message = MailMessage(
        subject="Test",
        to="a@example.test",
        body_text="Bonjour",
        from_email="explicit@example.test",
    )
    mailer = SMTPMailer.from_config()

    assert mailer.send(message) is True
    sent_message, from_addr, _to_addrs = FakeSMTP.instances[0].sent[0]
    assert from_addr == "explicit@example.test"
    assert sent_message["From"] == "explicit@example.test"


def test_from_email_par_defaut_depuis_config():
    message = MailMessage(subject="Test", to="a@example.test", body_text="Bonjour")
    mailer = SMTPMailer.from_config()

    assert mailer.send(message) is True
    sent_message, from_addr, _to_addrs = FakeSMTP.instances[0].sent[0]
    assert from_addr == "default@example.test"
    assert sent_message["From"] == "default@example.test"


def test_erreur_claire_si_aucun_from_email():
    forge.configure(mail_from="")
    message = MailMessage(subject="Test", to="a@example.test", body_text="Bonjour")
    mailer = SMTPMailer.from_config()

    with pytest.raises(MailConfigurationError, match="MAIL_FROM"):
        mailer.send(message)


def test_starttls_appele_si_mail_use_tls_true():
    forge.configure(mail_use_tls=True)
    message = MailMessage(subject="Test", to="a@example.test", body_text="Bonjour")

    SMTPMailer.from_config().send(message)

    assert FakeSMTP.instances[0].started_tls is True


def test_booleens_config_acceptent_chaines_false():
    forge.configure(mail_use_tls="false", mail_enabled="false")

    mailer = SMTPMailer.from_config()

    assert mailer.use_tls is False
    assert mailer.enabled is False


def test_mail_enabled_false_leve_erreur_explicite():
    forge.configure(mail_enabled=False)
    message = MailMessage(subject="Test", to="a@example.test", body_text="Bonjour")

    with pytest.raises(MailConfigurationError, match="MAIL_ENABLED=false"):
        SMTPMailer.from_config().send(message)


def test_smtp_ssl_utilise_si_mail_use_ssl_true(monkeypatch):
    class PlainSMTP(FakeSMTP):
        pass

    class SecureSMTP(FakeSMTP):
        pass

    PlainSMTP.instances = []
    SecureSMTP.instances = []
    monkeypatch.setattr(smtplib, "SMTP", PlainSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", SecureSMTP)
    forge.configure(mail_use_ssl=True)
    message = MailMessage(subject="Test", to="a@example.test", body_text="Bonjour")

    SMTPMailer.from_config().send(message)

    assert len(PlainSMTP.instances) == 0
    assert len(SecureSMTP.instances) == 1


def test_login_appele_si_mail_username_fourni():
    forge.configure(mail_username="roger", mail_password="secret")
    message = MailMessage(subject="Test", to="a@example.test", body_text="Bonjour")

    SMTPMailer.from_config().send(message)

    assert FakeSMTP.instances[0].login_args == ("roger", "secret")


def test_aucune_connexion_reelle_dans_les_tests():
    message = MailMessage(subject="Test", to="a@example.test", body_text="Bonjour")

    SMTPMailer.from_config().send(message)

    assert FakeSMTP.instances[0].host == "smtp.example.test"


def test_erreur_smtplib_transformee_en_exception_forge(monkeypatch):
    monkeypatch.setattr(smtplib, "SMTP", FailingSMTP)
    message = MailMessage(subject="Test", to="a@example.test", body_text="Bonjour")

    with pytest.raises(MailSendError, match="Envoi SMTP impossible"):
        SMTPMailer.from_config().send(message)


def test_bcc_dans_enveloppe_mais_pas_dans_headers_visibles():
    message = MailMessage(
        subject="Test",
        to="a@example.test",
        cc="b@example.test",
        bcc=["hidden@example.test"],
        body_text="Bonjour",
    )

    SMTPMailer.from_config().send(message)

    sent_message, _from_addr, to_addrs = FakeSMTP.instances[0].sent[0]
    assert to_addrs == ["a@example.test", "b@example.test", "hidden@example.test"]
    assert "Bcc" not in sent_message


def test_erreur_claire_si_mail_host_absent():
    forge.configure(mail_host="")
    message = MailMessage(subject="Test", to="a@example.test", body_text="Bonjour")

    with pytest.raises(MailConfigurationError, match="MAIL_HOST"):
        SMTPMailer.from_config().send(message)
