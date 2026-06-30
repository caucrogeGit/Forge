# forge-mvc-mail

Opt-in Forge pour l'**envoi d'emails**. Extrait du core (ADR-022) : le core ne
contient que les primitives générales ; l'email est une brique spécialisée,
optionnelle.

## Contenu

- `MailMessage` : composition d'un message (destinataires, sujet, texte, HTML).
- Transports interchangeables : `ConsoleTransport` (affichage), `SmtpTransport`
  (SMTP réel), `LogTransport`, `NullTransport`, `FakeTransport` (tests).
- `MailTemplateRenderer` : rendu de templates d'email via Jinja2.
- `Mailer` : orchestration envoi + journalisation (`MailLogger`).
- `MailConfig` : configuration depuis l'environnement.
- CLI `mail:init`, `mail:test`, `mail:render`, `mail:doctor`, `mail:logs`.

## Installation

```bash
pip install --pre forge-mvc-mail
```

## Usage

```python
from forge_mvc_mail import Mailer, MailMessage, ConsoleTransport

mailer = Mailer(transport=ConsoleTransport())
mailer.send(MailMessage(
    subject="Bienvenue",
    to="client@example.com",
    body_text="Merci de votre inscription.",
))
```

Le transport est interchangeable : `ConsoleTransport` (développement),
`SmtpTransport` (SMTP réel), `LogTransport`, `FakeTransport` (tests).
En production, `MailConfig` lit la configuration SMTP depuis l'environnement.

Le parcours pédagogique `welcome-mail` (documentation `docs/starters/welcome-mail/`)
montre l'usage pas à pas.
