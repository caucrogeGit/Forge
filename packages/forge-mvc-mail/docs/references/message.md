# Le message mail dans Forge

Ce document décrit `MailMessage`, l'objet qui représente un email à envoyer.

Le fichier de code correspondant est `forge_mvc_mail/message.py`.

## 1. À quoi sert ce module ?

`MailMessage` rassemble tout ce qui compose un email : destinataires, sujet, corps texte et HTML, copies.
C'est la donnée que l'on passe au `Mailer` pour l'expédier.

## 2. L'objet `MailMessage`

```python
@dataclass
class MailMessage:
    subject: str
    to: str | Iterable[str]
    body_text: str | None = None
    body_html: str | None = None
    from_email: str | None = None
    cc: str | Iterable[str] | None = None
    bcc: str | Iterable[str] | None = None
    reply_to: str | Iterable[str] | None = None
```

`to`, `cc`, `bcc` et `reply_to` acceptent une adresse unique ou une liste d'adresses.
`from_email` retombe sur l'expéditeur par défaut de la configuration si absent.

## 3. Construire un message

```python
from forge_mvc_mail import MailMessage

msg = MailMessage(
    subject="Bienvenue",
    to="alice@example.org",
    body_text="Bonjour Alice",
    body_html="<p>Bonjour Alice</p>",
)
```

Un message invalide (champ manquant, injection détectée dans un en-tête) provoque une `MailValidationError` au moment de l'envoi.

## 4. Contextes d'utilisation

- **Envoi direct** : construire un `MailMessage` et le passer au [`Mailer`](mailer.md).
- **Depuis un gabarit** : le [`MailTemplateRenderer`](templates.md) produit un `MailMessage`.

## 5. Voir aussi

- [Le mailer](mailer.md) : envoie un `MailMessage`.
- [Le rendu de gabarits](templates.md) : produit un `MailMessage`.
- [Vue d'ensemble Mail](../reference.md).
