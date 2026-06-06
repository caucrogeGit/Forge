# forge-mvc-mail

Opt-in Forge pour l'**envoi d'emails**. Extrait du core (ADR-022) : le core ne
contient que les primitives générales ; l'email est une brique spécialisée,
optionnelle.

## Contenu

- `MailMessage` : composition d'un message (destinataires, sujet, texte, HTML).
- Transports interchangeables : `ConsoleTransport` (affichage), `SmtpTransport`
  / `SMTPMailer` (SMTP réel), `LogTransport`, `NullTransport`, `FakeTransport`
  (tests).
- `MailTemplateRenderer` : rendu de templates d'email via Jinja2.
- `Mailer` : orchestration envoi + journalisation (`MailLogger`).
- `MailConfig` : configuration depuis l'environnement.
- CLI `mail:init`, `mail:test`, `mail:render`, `mail:doctor`, `mail:logs`.

## Installation

```bash
pip install --pre forge-mvc-mail
```

Le parcours pédagogique `welcome-mail` (`forge starter:build mail-welcome`)
montre l'usage pas à pas.
