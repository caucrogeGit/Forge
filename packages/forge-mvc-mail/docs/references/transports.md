# Les transports mail dans Forge

Ce document décrit les transports interchangeables qui décident *comment* un mail part.

Le fichier de code correspondant est `forge_mvc_mail/transports.py`.

## 1. À quoi sert ce module ?

Un transport est la stratégie d'expédition : écrire dans la console, déposer un fichier, envoyer par SMTP, ou ne rien faire.
Tous partagent la même interface (`BaseTransport`), si bien que le [`Mailer`](mailer.md) fonctionne avec n'importe lequel sans changer de code.

## 2. Les transports disponibles

| Transport | Comportement |
|---|---|
| `BaseTransport` | l'interface commune à tous les transports |
| `ConsoleTransport(stream=None)` | écrit une représentation lisible du mail dans un flux (stdout par défaut) |
| `LogTransport(log_dir="storage/mail")` | écrit un fichier `.eml` dans `storage/mail/`, sans rien envoyer |
| `SmtpTransport(host, port, username, password, ...)` | envoi SMTP réel via `smtplib` ; à ne pas utiliser par défaut en développement |
| `FakeTransport()` | capture les messages en mémoire ; conçu pour les tests unitaires |
| `NullTransport()` | no-op : n'envoie rien, ne journalise rien ; utile pour désactiver le mail |

## 3. Le résultat (`TransportResult`)

```python
@dataclass
class TransportResult:
    success: bool
    transport: str
    skipped: bool = False
    detail: str = ""
```

Chaque envoi retourne un `TransportResult`, qu'il ait eu lieu ou non (`skipped=True` pour `NullTransport`).

## 4. Choisir un transport

```python
from forge_mvc_mail import Mailer, SmtpTransport, LogTransport, FakeTransport

mailer = Mailer(SmtpTransport(host="smtp.example.org", port=587, use_tls=True))  # prod
mailer = Mailer(LogTransport())     # dev : fichiers .eml
mailer = Mailer(FakeTransport())    # tests : capture mémoire
```

`SmtpTransport` accepte `verify_tls=True` par défaut : la vérification du certificat n'est désactivée qu'explicitement.

## 5. Contextes d'utilisation

- **Production** : `SmtpTransport`.
- **Développement** : `LogTransport` ou `ConsoleTransport`.
- **Tests** : `FakeTransport`.
- **Désactivation** : `NullTransport`.

## 6. Voir aussi

- [Le mailer](mailer.md) : consomme un transport.
- [La configuration mail](config.md) : `transport_name` sélectionne le transport.
- [Vue d'ensemble Mail](../reference.md).
