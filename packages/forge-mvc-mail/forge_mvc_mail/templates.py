# pyright: strict
"""Rendu de templates mail Jinja2 — produit un MailMessage, n'envoie rien."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import jinja2

from forge_mvc_mail.config import mail_templates_dir
from forge_mvc_mail.exceptions import MailTemplateError
from forge_mvc_mail.message import MailMessage


class MailTemplateRenderer:
    """Rend un jeu de templates Jinja2 en MailMessage.

    Pour un template nommé "bienvenue", cherche dans le dossier configuré :
        bienvenue_subject.txt   (requis)
        bienvenue_text.txt      (requis)
        bienvenue_html.html     (optionnel)

    Usage :
        renderer = MailTemplateRenderer()           # lit mail_templates_dir
        renderer = MailTemplateRenderer(tmp_path)   # dossier explicite (tests)
        msg = renderer.render("bienvenue", {"prenom": "Alice"}, to="a@x.test")
    """

    def __init__(self, template_dir: str | Path | None = None) -> None:
        if template_dir is None:
            template_dir = mail_templates_dir()
        self._dir = Path(template_dir)
        self._env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self._dir)),
            autoescape=jinja2.select_autoescape(enabled_extensions=["html", "htm"]),
        )

    def render(
        self,
        template_name: str,
        context: dict[str, Any],
        *,
        to: str | Iterable[str],
        from_email: str | None = None,
        cc: str | Iterable[str] | None = None,
        bcc: str | Iterable[str] | None = None,
        reply_to: str | Iterable[str] | None = None,
    ) -> MailMessage:
        """Rend les templates et retourne un MailMessage prêt à être envoyé."""
        subject = self._render_required(
            f"{template_name}_subject.txt", context, template_name, "subject"
        ).strip()
        body_text = self._render_required(
            f"{template_name}_text.txt", context, template_name, "text"
        )
        body_html = self._render_optional(f"{template_name}_html.html", context)
        return MailMessage(
            subject=subject,
            to=to,
            body_text=body_text,
            body_html=body_html,
            from_email=from_email,
            cc=cc,
            bcc=bcc,
            reply_to=reply_to,
        )

    def _render_required(
        self, filename: str, context: dict[str, Any], template_name: str, part: str
    ) -> str:
        try:
            tpl = self._env.get_template(filename)
        except jinja2.TemplateNotFound:
            raise MailTemplateError(
                f"Template mail manquant : {filename!r} "
                f"(partie '{part}' du template {template_name!r})."
            ) from None
        try:
            return tpl.render(**context)
        except jinja2.TemplateError as exc:
            raise MailTemplateError(
                f"Erreur de rendu du template {filename!r} : {exc}"
            ) from exc

    def _render_optional(self, filename: str, context: dict[str, Any]) -> str | None:
        try:
            tpl = self._env.get_template(filename)
            return tpl.render(**context)
        except jinja2.TemplateNotFound:
            return None
        except jinja2.TemplateError as exc:
            raise MailTemplateError(
                f"Erreur de rendu du template {filename!r} : {exc}"
            ) from exc
