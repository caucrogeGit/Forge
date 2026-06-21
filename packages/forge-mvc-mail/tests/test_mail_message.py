"""Tests unitaires de MailMessage — aucune dépendance SMTP ni forge.configure."""

import pytest

pytest.importorskip("forge_mvc_mail")
from forge_mvc_mail.exceptions import MailConfigurationError, MailValidationError
from forge_mvc_mail.message import MailMessage


# ── Hiérarchie des exceptions ─────────────────────────────────────────────────

def test_mail_validation_error_est_sous_classe_mail_configuration_error():
    assert issubclass(MailValidationError, MailConfigurationError)


# ── Construction valide ───────────────────────────────────────────────────────

def test_message_body_text_seul():
    m = MailMessage(subject="Test", to="a@example.test", body_text="Bonjour")
    assert m.body_text == "Bonjour"
    assert m.body_html is None


def test_message_body_html_seul():
    m = MailMessage(subject="Test", to="a@example.test", body_html="<p>Bonjour</p>")
    assert m.body_html == "<p>Bonjour</p>"
    assert m.body_text is None


def test_message_body_text_et_html():
    m = MailMessage(
        subject="Test",
        to="a@example.test",
        body_text="Bonjour",
        body_html="<p>Bonjour</p>",
    )
    assert m.body_text is not None
    assert m.body_html is not None


# ── Validation champs obligatoires ────────────────────────────────────────────

def test_to_none_leve_erreur():
    with pytest.raises(MailValidationError, match="to"):
        MailMessage(subject="Test", to=None, body_text="x")


def test_to_liste_vide_leve_erreur():
    with pytest.raises(MailValidationError, match="to"):
        MailMessage(subject="Test", to=[], body_text="x")


def test_to_chaine_vide_leve_erreur():
    with pytest.raises(MailValidationError, match="to"):
        MailMessage(subject="Test", to="", body_text="x")


def test_to_espaces_seuls_leve_erreur():
    with pytest.raises(MailValidationError, match="to"):
        MailMessage(subject="Test", to="   ", body_text="x")


def test_subject_vide_leve_erreur():
    with pytest.raises(MailValidationError, match="subject"):
        MailMessage(subject="", to="a@example.test", body_text="x")


def test_subject_espaces_seuls_leve_erreur():
    with pytest.raises(MailValidationError, match="subject"):
        MailMessage(subject="   ", to="a@example.test", body_text="x")


def test_aucun_body_leve_erreur():
    with pytest.raises(MailValidationError):
        MailMessage(subject="Test", to="a@example.test")


def test_body_text_none_et_body_html_none_leve_erreur():
    with pytest.raises(MailValidationError):
        MailMessage(subject="Test", to="a@example.test", body_text=None, body_html=None)


# ── Anti-injection headers ────────────────────────────────────────────────────

def test_subject_avec_newline_leve_erreur():
    with pytest.raises(MailValidationError, match="injection"):
        MailMessage(
            subject="Test\nBcc: evil@example.test",
            to="a@example.test",
            body_text="x",
        )


def test_subject_avec_crlf_leve_erreur():
    with pytest.raises(MailValidationError, match="injection"):
        MailMessage(
            subject="Test\r\nBcc: evil@example.test",
            to="a@example.test",
            body_text="x",
        )


def test_subject_avec_carriage_return_seul_leve_erreur():
    with pytest.raises(MailValidationError, match="injection"):
        MailMessage(subject="Test\rEvil", to="a@example.test", body_text="x")


def test_from_email_avec_newline_leve_erreur():
    with pytest.raises(MailValidationError, match="injection"):
        MailMessage(
            subject="Test",
            to="a@example.test",
            body_text="x",
            from_email="x@x.test\nBcc: evil@x.test",
        )


def test_adresse_to_avec_newline_leve_erreur():
    with pytest.raises(MailValidationError, match="injection"):
        MailMessage(
            subject="Test",
            to="evil@x.test\nBcc: other@x.test",
            body_text="x",
        )


def test_adresse_cc_avec_newline_leve_erreur():
    with pytest.raises(MailValidationError, match="injection"):
        MailMessage(
            subject="Test",
            to="a@x.test",
            cc="evil@x.test\nX-Extra: hacked",
            body_text="x",
        )


def test_adresse_bcc_avec_newline_leve_erreur():
    with pytest.raises(MailValidationError, match="injection"):
        MailMessage(
            subject="Test",
            to="a@x.test",
            bcc="evil@x.test\nX-Extra: hacked",
            body_text="x",
        )


def test_reply_to_avec_newline_leve_erreur():
    with pytest.raises(MailValidationError, match="injection"):
        MailMessage(
            subject="Test",
            to="a@x.test",
            reply_to="evil@x.test\nX-Extra: hacked",
            body_text="x",
        )


# ── Normalisation des adresses ────────────────────────────────────────────────

def test_to_chaine_simple_produit_liste():
    m = MailMessage(subject="Test", to="a@example.test", body_text="x")
    assert m.to_addresses == ["a@example.test"]


def test_to_liste_multiple():
    m = MailMessage(
        subject="Test",
        to=["a@example.test", "b@example.test"],
        body_text="x",
    )
    assert m.to_addresses == ["a@example.test", "b@example.test"]


def test_to_espaces_trim():
    m = MailMessage(subject="Test", to="  a@example.test  ", body_text="x")
    assert m.to_addresses == ["a@example.test"]


def test_to_liste_filtre_chaines_vides():
    m = MailMessage(
        subject="Test",
        to=["a@example.test", "   ", "b@example.test"],
        body_text="x",
    )
    assert m.to_addresses == ["a@example.test", "b@example.test"]


def test_cc_none_produit_liste_vide():
    m = MailMessage(subject="Test", to="a@example.test", body_text="x")
    assert m.cc_addresses == []


def test_bcc_none_produit_liste_vide():
    m = MailMessage(subject="Test", to="a@example.test", body_text="x")
    assert m.bcc_addresses == []


def test_reply_to_none_produit_liste_vide():
    m = MailMessage(subject="Test", to="a@example.test", body_text="x")
    assert m.reply_to_addresses == []


def test_subject_trim():
    m = MailMessage(subject="  Test  ", to="a@example.test", body_text="x")
    assert m.subject == "Test"


# ── envelope_recipients ───────────────────────────────────────────────────────

def test_envelope_recipients_to_seul():
    m = MailMessage(subject="Test", to="a@example.test", body_text="x")
    assert m.envelope_recipients == ["a@example.test"]


def test_envelope_recipients_to_cc_bcc():
    m = MailMessage(
        subject="Test",
        to="a@example.test",
        cc="b@example.test",
        bcc=["c@example.test", "d@example.test"],
        body_text="x",
    )
    assert m.envelope_recipients == [
        "a@example.test",
        "b@example.test",
        "c@example.test",
        "d@example.test",
    ]


def test_envelope_recipients_exclut_reply_to():
    m = MailMessage(
        subject="Test",
        to="a@example.test",
        reply_to="r@example.test",
        body_text="x",
    )
    assert "r@example.test" not in m.envelope_recipients


# ── as_email_message ──────────────────────────────────────────────────────────

def test_email_texte_seul_content_type():
    m = MailMessage(subject="Test", to="a@example.test", body_text="Bonjour")
    email = m.as_email_message("from@example.test")
    assert not email.is_multipart()
    assert email.get_content_type() == "text/plain"
    assert email.get_content().strip() == "Bonjour"


def test_email_html_seul_content_type():
    m = MailMessage(subject="Test", to="a@example.test", body_html="<p>Bonjour</p>")
    email = m.as_email_message("from@example.test")
    assert email.get_content_type() == "text/html"
    assert email.get_content().strip() == "<p>Bonjour</p>"


def test_email_multipart_contient_texte_et_html():
    m = MailMessage(
        subject="Test",
        to="a@example.test",
        body_text="Bonjour",
        body_html="<p>Bonjour</p>",
    )
    email = m.as_email_message("from@example.test")
    assert email.is_multipart()
    types = [p.get_content_type() for p in email.get_payload()]
    assert "text/plain" in types
    assert "text/html" in types


def test_email_headers_from_to_subject():
    m = MailMessage(subject="Bienvenue", to="dest@example.test", body_text="x")
    email = m.as_email_message("from@example.test")
    assert email["Subject"] == "Bienvenue"
    assert email["From"] == "from@example.test"
    assert "dest@example.test" in email["To"]


def test_email_cc_present_dans_headers():
    m = MailMessage(
        subject="Test",
        to="a@example.test",
        cc="b@example.test",
        body_text="x",
    )
    email = m.as_email_message("from@example.test")
    assert "b@example.test" in email["Cc"]


def test_email_bcc_absent_des_headers():
    m = MailMessage(
        subject="Test",
        to="a@example.test",
        bcc="hidden@example.test",
        body_text="x",
    )
    email = m.as_email_message("from@example.test")
    assert "Bcc" not in email


def test_email_reply_to_dans_headers():
    m = MailMessage(
        subject="Test",
        to="a@example.test",
        reply_to="r@example.test",
        body_text="x",
    )
    email = m.as_email_message("from@example.test")
    assert "r@example.test" in email["Reply-To"]


def test_email_sans_cc_ni_reply_to_headers_absents():
    m = MailMessage(subject="Test", to="a@example.test", body_text="x")
    email = m.as_email_message("from@example.test")
    assert email["Cc"] is None
    assert email["Reply-To"] is None


def test_email_to_multiple_dans_header():
    m = MailMessage(
        subject="Test",
        to=["a@example.test", "b@example.test"],
        body_text="x",
    )
    email = m.as_email_message("from@example.test")
    assert "a@example.test" in email["To"]
    assert "b@example.test" in email["To"]
