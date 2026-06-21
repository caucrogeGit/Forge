# Le mailer dans Forge

Ce document décrit `Mailer`, qui envoie un message via le transport configuré.

Le fichier de code correspondant est `forge_mvc_mail/mailer.py`.

## 1. À quoi sert ce module ?

Le `Mailer` est la façade d'envoi : on lui donne un transport à la construction, puis on lui passe des `MailMessage` à expédier.
Il ne sait pas *comment* le mail part : c'est le rôle du [transport](transports.md).

## 2. Envoyer un message

```python
from forge_mvc_mail import Mailer, MailMessage, LogTransport

mailer = Mailer(transport=LogTransport())
result = mailer.send(MailMessage(subject="Salut", to="alice@example.org", body_text="..."))
result.success   # bool
```

`Mailer(transport)` prend n'importe quel transport (`BaseTransport`).
La méthode d'envoi retourne un `TransportResult` décrivant l'issue (succès, ignoré, détail).

## 3. Le découplage transport

Changer de transport ne change pas le code d'envoi : on passe de `LogTransport` à `SmtpTransport` à la construction, le reste est identique.
C'est ce qui permet de tester avec `FakeTransport` et de produire avec `SmtpTransport`.

## 4. Contextes d'utilisation

- **Production** : `Mailer(SmtpTransport(...))`.
- **Développement** : `Mailer(LogTransport())` ou `ConsoleTransport()`.
- **Tests** : `Mailer(FakeTransport())` pour inspecter les messages capturés.

## 5. Voir aussi

- [Les transports](transports.md) : les implémentations injectables.
- [Le message mail](message.md) : ce que l'on envoie.
- [Vue d'ensemble Mail](../reference.md).
