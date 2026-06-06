"""Tests du renderer de templates mail — aucun envoi, aucun SMTP."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_mail")
from forge_mvc_mail.exceptions import MailTemplateError, MailValidationError
from forge_mvc_mail.message import MailMessage
from forge_mvc_mail.templates import MailTemplateRenderer


def _w(tmp_path: Path, name: str, content: str) -> None:
    (tmp_path / name).write_text(content, encoding="utf-8")


def _renderer(tmp_path: Path) -> MailTemplateRenderer:
    return MailTemplateRenderer(template_dir=tmp_path)


# ── Construction ──────────────────────────────────────────────────────────────

def test_renderer_cree_avec_dossier_explicite(tmp_path):
    assert MailTemplateRenderer(template_dir=tmp_path) is not None


def test_renderer_dir_stocke_le_chemin(tmp_path):
    r = MailTemplateRenderer(template_dir=tmp_path)
    assert r._dir == tmp_path


# ── Rendu complet : subject + text + html ─────────────────────────────────────

def test_render_retourne_mail_message(tmp_path):
    _w(tmp_path, "t_subject.txt", "Bienvenue")
    _w(tmp_path, "t_text.txt", "Corps")
    msg = _renderer(tmp_path).render("t", {}, to="a@x.test")
    assert isinstance(msg, MailMessage)


def test_render_subject_interpole(tmp_path):
    _w(tmp_path, "t_subject.txt", "Bonjour {{ prenom }}")
    _w(tmp_path, "t_text.txt", "Corps")
    msg = _renderer(tmp_path).render("t", {"prenom": "Alice"}, to="a@x.test")
    assert msg.subject == "Bonjour Alice"


def test_render_subject_stripppe_espaces(tmp_path):
    _w(tmp_path, "t_subject.txt", "  Bienvenue  \n")
    _w(tmp_path, "t_text.txt", "Corps")
    msg = _renderer(tmp_path).render("t", {}, to="a@x.test")
    assert msg.subject == "Bienvenue"


def test_render_body_text_interpole(tmp_path):
    _w(tmp_path, "t_subject.txt", "S")
    _w(tmp_path, "t_text.txt", "Bonjour {{ prenom }},\nBienvenue !")
    msg = _renderer(tmp_path).render("t", {"prenom": "Roger"}, to="a@x.test")
    assert "Roger" in msg.body_text
    assert "Bienvenue" in msg.body_text


def test_render_body_html_interpole(tmp_path):
    _w(tmp_path, "t_subject.txt", "S")
    _w(tmp_path, "t_text.txt", "C")
    _w(tmp_path, "t_html.html", "<p>{{ contenu }}</p>")
    msg = _renderer(tmp_path).render("t", {"contenu": "Bonjour"}, to="a@x.test")
    assert msg.body_html == "<p>Bonjour</p>"


def test_render_body_html_absent_retourne_none(tmp_path):
    _w(tmp_path, "t_subject.txt", "S")
    _w(tmp_path, "t_text.txt", "C")
    msg = _renderer(tmp_path).render("t", {}, to="a@x.test")
    assert msg.body_html is None


def test_render_context_vide_fonctionne(tmp_path):
    _w(tmp_path, "t_subject.txt", "Notification")
    _w(tmp_path, "t_text.txt", "Aucun paramètre.")
    msg = _renderer(tmp_path).render("t", {}, to="a@x.test")
    assert msg.subject == "Notification"


# ── Champs de destination ─────────────────────────────────────────────────────

def test_render_passe_to_chaine(tmp_path):
    _w(tmp_path, "t_subject.txt", "S")
    _w(tmp_path, "t_text.txt", "C")
    msg = _renderer(tmp_path).render("t", {}, to="dest@x.test")
    assert msg.to_addresses == ["dest@x.test"]


def test_render_passe_to_liste(tmp_path):
    _w(tmp_path, "t_subject.txt", "S")
    _w(tmp_path, "t_text.txt", "C")
    msg = _renderer(tmp_path).render("t", {}, to=["a@x.test", "b@x.test"])
    assert msg.to_addresses == ["a@x.test", "b@x.test"]


def test_render_passe_from_email(tmp_path):
    _w(tmp_path, "t_subject.txt", "S")
    _w(tmp_path, "t_text.txt", "C")
    msg = _renderer(tmp_path).render("t", {}, to="a@x.test", from_email="exp@x.test")
    assert msg.from_email == "exp@x.test"


def test_render_passe_cc(tmp_path):
    _w(tmp_path, "t_subject.txt", "S")
    _w(tmp_path, "t_text.txt", "C")
    msg = _renderer(tmp_path).render("t", {}, to="a@x.test", cc="b@x.test")
    assert "b@x.test" in msg.cc_addresses


def test_render_passe_bcc(tmp_path):
    _w(tmp_path, "t_subject.txt", "S")
    _w(tmp_path, "t_text.txt", "C")
    msg = _renderer(tmp_path).render("t", {}, to="a@x.test", bcc="hidden@x.test")
    assert "hidden@x.test" in msg.bcc_addresses


def test_render_passe_reply_to(tmp_path):
    _w(tmp_path, "t_subject.txt", "S")
    _w(tmp_path, "t_text.txt", "C")
    msg = _renderer(tmp_path).render("t", {}, to="a@x.test", reply_to="r@x.test")
    assert "r@x.test" in msg.reply_to_addresses


def test_render_from_email_absent_par_defaut(tmp_path):
    _w(tmp_path, "t_subject.txt", "S")
    _w(tmp_path, "t_text.txt", "C")
    msg = _renderer(tmp_path).render("t", {}, to="a@x.test")
    assert msg.from_email is None


# ── Erreurs explicites ────────────────────────────────────────────────────────

def test_render_subject_manquant_leve_erreur(tmp_path):
    _w(tmp_path, "t_text.txt", "C")
    with pytest.raises(MailTemplateError, match="subject"):
        _renderer(tmp_path).render("t", {}, to="a@x.test")


def test_render_text_manquant_leve_erreur(tmp_path):
    _w(tmp_path, "t_subject.txt", "S")
    with pytest.raises(MailTemplateError, match="text"):
        _renderer(tmp_path).render("t", {}, to="a@x.test")


def test_render_template_inexistant_leve_erreur(tmp_path):
    with pytest.raises(MailTemplateError):
        _renderer(tmp_path).render("fantome", {}, to="a@x.test")


def test_render_erreur_message_contient_nom_fichier(tmp_path):
    _w(tmp_path, "t_text.txt", "C")
    with pytest.raises(MailTemplateError, match="t_subject.txt"):
        _renderer(tmp_path).render("t", {}, to="a@x.test")


def test_render_erreur_message_contient_nom_template(tmp_path):
    _w(tmp_path, "t_text.txt", "C")
    with pytest.raises(MailTemplateError, match="'t'"):
        _renderer(tmp_path).render("t", {}, to="a@x.test")


def test_render_mail_template_error_est_mail_configuration_error(tmp_path):
    from forge_mvc_mail.exceptions import MailConfigurationError
    assert issubclass(MailTemplateError, MailConfigurationError)


# ── Anti-injection headers ────────────────────────────────────────────────────

def test_render_subject_injection_newline_leve_erreur(tmp_path):
    _w(tmp_path, "t_subject.txt", "Bonjour\r\nBcc: evil@x.test")
    _w(tmp_path, "t_text.txt", "C")
    with pytest.raises(MailValidationError, match="injection"):
        _renderer(tmp_path).render("t", {}, to="a@x.test")


def test_render_subject_injection_via_context_leve_erreur(tmp_path):
    _w(tmp_path, "t_subject.txt", "Bonjour {{ nom }}")
    _w(tmp_path, "t_text.txt", "C")
    with pytest.raises(MailValidationError, match="injection"):
        _renderer(tmp_path).render("t", {"nom": "Alice\r\nBcc: evil@x.test"}, to="a@x.test")


# ── Autoescape Jinja2 ─────────────────────────────────────────────────────────

def test_render_html_autoescape_caracteres_speciaux(tmp_path):
    _w(tmp_path, "t_subject.txt", "S")
    _w(tmp_path, "t_text.txt", "C")
    _w(tmp_path, "t_html.html", "<p>{{ contenu }}</p>")
    msg = _renderer(tmp_path).render(
        "t", {"contenu": "<script>alert(1)</script>"}, to="a@x.test"
    )
    assert "<script>" not in msg.body_html
    assert "&lt;script&gt;" in msg.body_html


def test_render_text_pas_autoescape(tmp_path):
    _w(tmp_path, "t_subject.txt", "S")
    _w(tmp_path, "t_text.txt", "{{ contenu }}")
    msg = _renderer(tmp_path).render("t", {"contenu": "<test>"}, to="a@x.test")
    assert "<test>" in msg.body_text


def test_render_subject_pas_autoescape(tmp_path):
    _w(tmp_path, "t_subject.txt", "{{ contenu }}")
    _w(tmp_path, "t_text.txt", "C")
    msg = _renderer(tmp_path).render("t", {"contenu": "A & B"}, to="a@x.test")
    assert msg.subject == "A & B"


# ── Import public ─────────────────────────────────────────────────────────────

def test_import_public_mail_template_renderer():
    from forge_mvc_mail import MailTemplateRenderer  # noqa: F401
