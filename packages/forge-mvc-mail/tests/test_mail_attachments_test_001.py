"""MAIL-ATTACHMENTS-001 et MAIL-TEST-GUIDED-001 : joindre un fichier, essayer à blanc.

Une facture, un export, un justificatif : un email en porte souvent un, et le
paquet ne savait pas en joindre.

Un nom de pièce jointe voyage dans un en-tête MIME et s'affiche chez le
destinataire. Il vient souvent d'un fichier déposé par un utilisateur, donc
d'une saisie.

Et `mail:test` envoyait toujours : vérifier sa configuration commençait par
écrire à quelqu'un, et exigeait un relais joignable.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_mail")

from forge_mvc_mail.exceptions import MailValidationError  # noqa: E402
from forge_mvc_mail.message import (  # noqa: E402
    MAX_ATTACHMENT_BYTES,
    Attachment,
    MailMessage,
)


def _message() -> MailMessage:
    return MailMessage(subject="Facture", to="a@b.fr", body_text="Ci-joint")


class TestNomDeFichier:
    def test_un_nom_simple_est_conserve(self) -> None:
        assert Attachment("facture.pdf", b"x").filename == "facture.pdf"

    @pytest.mark.parametrize(
        ("saisi", "attendu"),
        [("../../etc/passwd", "passwd"), ("/tmp/a.pdf", "a.pdf"),
         ("dossier/b.pdf", "b.pdf"), ("C:\\\\Windows\\\\c.pdf", "c.pdf")],
    )
    def test_un_chemin_est_reduit_au_nom(self, saisi: str, attendu: str) -> None:
        """Un nom de fichier ne contient jamais de chemin."""
        assert Attachment(saisi, b"x").filename == attendu

    @pytest.mark.parametrize("hostile", ["a\r\nb.pdf", "a\nb.pdf"])
    def test_un_saut_de_ligne_est_retire(self, hostile: str) -> None:
        """Il couperait l'en-tête MIME en deux."""
        nom = Attachment(hostile, b"x").filename
        assert "\r" not in nom and "\n" not in nom

    @pytest.mark.parametrize("vide", ["", "   ", "/", "..", "."])
    def test_un_nom_vide_ou_reduit_a_rien_est_refuse(self, vide: str) -> None:
        with pytest.raises(MailValidationError):
            Attachment(vide, b"x")


class TestTypeMime:
    def test_le_type_est_devine_du_nom(self) -> None:
        assert Attachment("a.pdf", b"x").resolved_mime_type == "application/pdf"
        assert Attachment("a.csv", b"x").resolved_mime_type == "text/csv"

    def test_un_type_inconnu_reste_generique(self) -> None:
        """Un type faux serait suivi par le client mail pour ouvrir le fichier."""
        assert Attachment("a.xyzzy", b"x").resolved_mime_type == "application/octet-stream"

    def test_un_type_declare_l_emporte(self) -> None:
        piece = Attachment("a.bin", b"x", mime_type="application/pdf")
        assert piece.resolved_mime_type == "application/pdf"

    @pytest.mark.parametrize("mauvais", ["pdf", "application/", "/pdf", "a/b/c"])
    def test_un_type_malforme_est_refuse(self, mauvais: str) -> None:
        with pytest.raises(MailValidationError, match="MIME"):
            Attachment("a.bin", b"x", mime_type=mauvais)


class TestContenu:
    def test_le_contenu_doit_etre_des_octets(self) -> None:
        with pytest.raises(MailValidationError, match="octets"):
            Attachment("a.pdf", "du texte")  # type: ignore[arg-type]

    def test_une_piece_trop_volumineuse_est_refusee(self) -> None:
        """Un relais refuserait après coup, plus difficile à diagnostiquer."""
        with pytest.raises(MailValidationError, match="volumineuse"):
            Attachment("a.bin", b"x" * (MAX_ATTACHMENT_BYTES + 1))

    def test_la_limite_exacte_passe(self) -> None:
        Attachment("a.bin", b"x" * MAX_ATTACHMENT_BYTES)


class TestMessageImmuable:
    def test_joindre_rend_un_nouveau_message(self) -> None:
        """Un message mis en file puis complété ailleurs partirait dans deux états."""
        origine = _message()
        avec = origine.with_attachment("a.pdf", b"x")

        assert origine.attachments == []
        assert len(avec.attachments) == 1

    def test_le_reste_du_message_est_preserve(self) -> None:
        origine = MailMessage(
            subject="Facture", to=["a@b.fr", "c@d.fr"], body_text="Corps",
            body_html="<p>Corps</p>", cc="e@f.fr",
        )
        avec = origine.with_attachment("a.pdf", b"x")

        assert avec.subject == origine.subject
        assert avec.to_addresses == origine.to_addresses
        assert avec.cc_addresses == origine.cc_addresses
        assert avec.body_html == origine.body_html

    def test_plusieurs_pieces_s_accumulent(self) -> None:
        message = _message().with_attachment("a.pdf", b"x").with_attachment("b.csv", b"y")
        assert [p.filename for p in message.attachments] == ["a.pdf", "b.csv"]


class TestRenduMime:
    def test_la_piece_apparait_dans_le_message(self) -> None:
        email = _message().with_attachment("facture.pdf", b"%PDF").as_email_message("x@y.fr")
        types = [part.get_content_type() for part in email.walk()]

        assert "application/pdf" in types
        assert types[0] == "multipart/mixed"

    def test_le_corps_reste_present(self) -> None:
        email = _message().with_attachment("a.pdf", b"x").as_email_message("x@y.fr")
        types = [part.get_content_type() for part in email.walk()]

        assert "text/plain" in types

    def test_sans_piece_le_message_reste_simple(self) -> None:
        """Rétro-compatibilité : un message sans pièce ne devient pas multipart."""
        email = _message().as_email_message("x@y.fr")
        assert email.get_content_type() == "text/plain"

    def test_le_nom_de_fichier_est_porte(self) -> None:
        email = _message().with_attachment("facture.pdf", b"x").as_email_message("x@y.fr")
        noms = [part.get_filename() for part in email.walk()]

        assert "facture.pdf" in noms


class TestEssaiABlanc:
    @pytest.fixture(autouse=True)
    def _sans_projet(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """La commande exige un projet Forge : hors sujet pour l'essai à blanc."""
        from forge_mvc_mail import cli

        monkeypatch.setattr(cli, "_load_env_and_configure_forge", lambda root: None)

    def _lancer(self, args: list[str], tmp_path, capsys):
        from forge_mvc_mail.cli import cmd_mail_test

        cmd_mail_test(args, root=tmp_path)
        return capsys.readouterr().out

    def test_l_essai_a_blanc_n_envoie_rien(self, tmp_path, capsys) -> None:
        """Tester sa configuration ne devrait pas commencer par écrire à quelqu'un."""
        sortie = self._lancer(["--to", "a@b.fr", "--dry-run"], tmp_path, capsys)

        assert "Essai à blanc" in sortie
        assert "rien n'a été envoyé" in sortie

    def test_l_essai_a_blanc_montre_ce_qui_partirait(self, tmp_path, capsys) -> None:
        sortie = self._lancer(["--to", "a@b.fr", "--dry-run"], tmp_path, capsys)

        assert "Sujet" in sortie
        assert "a@b.fr" in sortie

    def test_le_diagnostic_precede_l_envoi(self, tmp_path, capsys) -> None:
        """Un « non envoyé » qui arrive à la fin se lit comme un échec."""
        sortie = self._lancer(["--to", "a@b.fr", "--dry-run"], tmp_path, capsys)

        assert "Transport" in sortie
        assert "Expéditeur" in sortie
        assert "Serveur" in sortie

    def test_un_transport_local_n_affiche_pas_de_serveur_fantome(
        self, tmp_path, capsys
    ) -> None:
        """« None:0 » ferait chercher une configuration qui n'a pas lieu d'être."""
        sortie = self._lancer(["--to", "a@b.fr", "--dry-run"], tmp_path, capsys)

        assert "None:0" not in sortie

    def test_une_option_sans_valeur_est_une_faute(self, tmp_path) -> None:
        from forge_mvc_mail.cli import cmd_mail_test

        with pytest.raises(SystemExit):
            cmd_mail_test(["--to", "--dry-run"], root=tmp_path)


class TestGabaritsReutilisables:
    """MAIL-LAYOUTS-001 : la capacité existait, rien ne la figeait ni ne la disait.

    Le moteur monte un `FileSystemLoader` sur le dossier des gabarits, si bien
    que `{% extends %}` fonctionne depuis toujours. Personne ne le savait : la
    référence n'en parlait pas, et un en-tête réécrit dans chaque gabarit est
    oublié quelque part le jour où l'adresse change.

    Ces tests figent la capacité, qu'une refonte du renderer pourrait sinon
    retirer sans que rien ne le signale.
    """

    def _dossier(self, tmp_path):
        (tmp_path / "layout_html.html").write_text(
            "<header>Mon École</header>"
            "{% block corps %}{% endblock %}"
            "<footer>Ne pas répondre</footer>",
            encoding="utf-8",
        )
        (tmp_path / "layout_text.txt").write_text(
            "Mon École\n{% block corps %}{% endblock %}\nNe pas répondre",
            encoding="utf-8",
        )
        (tmp_path / "bienvenue_subject.txt").write_text(
            "Bienvenue {{ prenom }}", encoding="utf-8"
        )
        (tmp_path / "bienvenue_text.txt").write_text(
            '{% extends "layout_text.txt" %}'
            "{% block corps %}Bonjour {{ prenom }}{% endblock %}",
            encoding="utf-8",
        )
        (tmp_path / "bienvenue_html.html").write_text(
            '{% extends "layout_html.html" %}'
            "{% block corps %}<p>Bonjour {{ prenom }}</p>{% endblock %}",
            encoding="utf-8",
        )
        return tmp_path

    def test_un_gabarit_html_herite_de_son_layout(self, tmp_path) -> None:
        from forge_mvc_mail.templates import MailTemplateRenderer

        message = MailTemplateRenderer(self._dossier(tmp_path)).render(
            "bienvenue", {"prenom": "Alice"}, to="a@b.fr"
        )

        assert "Mon École" in (message.body_html or "")
        assert "Bonjour Alice" in (message.body_html or "")
        assert "Ne pas répondre" in (message.body_html or "")

    def test_un_gabarit_texte_herite_aussi(self, tmp_path) -> None:
        """Les deux corps ont leur layout : l'un sans l'autre serait incohérent."""
        from forge_mvc_mail.templates import MailTemplateRenderer

        message = MailTemplateRenderer(self._dossier(tmp_path)).render(
            "bienvenue", {"prenom": "Alice"}, to="a@b.fr"
        )

        assert "Mon École" in (message.body_text or "")
        assert "Bonjour Alice" in (message.body_text or "")

    def test_un_layout_n_est_pas_un_gabarit_de_message(self, tmp_path) -> None:
        """Il n'a ni sujet ni corps propre : le rendre directement doit échouer."""
        from forge_mvc_mail.exceptions import MailTemplateError
        from forge_mvc_mail.templates import MailTemplateRenderer

        with pytest.raises(MailTemplateError):
            MailTemplateRenderer(self._dossier(tmp_path)).render(
                "layout", {}, to="a@b.fr"
            )

    def test_l_echappement_html_reste_actif_dans_un_layout(self, tmp_path) -> None:
        """Hériter ne doit pas ouvrir une injection dans le corps."""
        from forge_mvc_mail.templates import MailTemplateRenderer

        message = MailTemplateRenderer(self._dossier(tmp_path)).render(
            "bienvenue", {"prenom": "<script>alert(1)</script>"}, to="a@b.fr"
        )

        assert "<script>" not in (message.body_html or "")
        assert "&lt;script&gt;" in (message.body_html or "")
