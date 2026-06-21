# Les erreurs mail dans Forge

Ce document décrit les exceptions levées par le service mail.

Le fichier de code correspondant est `forge_mvc_mail/exceptions.py`.

## 1. À quoi servent ces erreurs ?

Le service mail distingue ses erreurs pour que l'application puisse réagir précisément : configuration absente, message invalide, envoi échoué, gabarit cassé.
Toutes héritent de `MailError`.

## 2. La hiérarchie

| Exception | Quand elle est levée |
|---|---|
| `MailError` | erreur de base du service mail |
| `MailConfigurationError` | configuration SMTP incomplète ou incohérente |
| `MailValidationError` | message invalide (champ manquant ou injection détectée) |
| `MailSendError` | l'envoi SMTP a échoué |
| `MailTemplateError` | un gabarit est absent, illisible, ou produit une erreur de rendu |

## 3. Bien les attraper

```python
from forge_mvc_mail import Mailer, MailError, MailSendError

try:
    mailer.send(message)
except MailSendError as err:
    # l'envoi a échoué (SMTP)
    ...
except MailError as err:
    # toute autre erreur mail
    ...
```

Attraper `MailError` couvre tout le service ; attraper une sous-classe cible un cas précis.

## 4. Contextes d'utilisation

- **Validation** : `MailValidationError` protège contre l'injection d'en-têtes.
- **Robustesse** : `MailSendError` pour gérer un échec SMTP sans casser la requête.

## 5. Voir aussi

- [Le mailer](mailer.md) : lève `MailSendError` à l'envoi.
- [Le rendu de gabarits](templates.md) : lève `MailTemplateError`.
- [Vue d'ensemble Mail](../reference.md).
