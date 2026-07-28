# Choisir un transport

## Niveau intermédiaire

Envoyer un `MailMessage` via un transport et lire le `TransportResult`.
Le `FakeTransport` capture les messages pour les tests.
En production, on choisit `ConsoleTransport`, `LogTransport`, `NullTransport` ou `SmtpTransport`.

??? note "Contrôleur"
    Créez le fichier `mvc/controllers/mail_transport_controller.py` :

    ```python
    # mvc/controllers/mail_transport_controller.py
    from core.http.request import Request
    from core.http.response import Response
    from forge_mvc_mail import FakeTransport, Mailer, MailMessage
    from core.mvc.controller.base_controller import BaseController


    class MailTransportController(BaseController):
        """Envoyer via un transport et lire le TransportResult, sans SMTP réel."""

        @staticmethod
        def index(request: Request) -> Response:
            transport = FakeTransport()
            result = Mailer(transport).send(MailMessage(
                subject="Test transport",
                to="dest@example.test",
                body_text="Contenu de test.",
            ))
            return BaseController.render(
                "mail_transport/index.html",
                context={
                    "transport_name": transport.name,
                    "sent_count": transport.sent_count,
                    "success": result.success,
                    "skipped": result.skipped,
                },
                request=request,
            )
    ```

    | Élément | Rôle |
    |---|---|
    | `FakeTransport` | Transport de test qui capture les messages au lieu de les envoyer. |
    | `transport.sent_count` | Nombre de messages capturés. |
    | `TransportResult.success` | Indique si l'envoi a réussi. |
    | `TransportResult.skipped` | Indique si l'envoi a été ignoré. |

??? note "Vue"
    Créez le fichier `mvc/views/mail_transport/index.html` :

    ```html
    {% extends "layouts/app.html" %}
    {% block content %}
    <h1>Choisir un transport</h1>
    <p>Message envoyé via <code>{{ transport_name }}</code> (transport de test) :</p>
    <ul>
      <li>Messages capturés : {{ sent_count }}</li>
      <li>Succès : {{ success }}</li>
      <li>Ignoré : {{ skipped }}</li>
    </ul>
    <p>Autres transports disponibles : ConsoleTransport, LogTransport, NullTransport, SmtpTransport.</p>
    {% endblock %}
    ```

??? note "Route"
    Dans `mvc/routes/__init__.py`, ajoutez l'import puis la route à l'intérieur du groupe public :

    ```python
    # mvc/routes/__init__.py
    from mvc.controllers.mail_transport_controller import MailTransportController

    with router.group("", public=True) as public:
        public.add("GET", "/mail-transport", MailTransportController.index, name="mail_transport_index")
    ```

## À retenir
- Un `Mailer` est branché sur un transport interchangeable.
- `FakeTransport` capture les messages, idéal pour les tests.
- L'envoi retourne un `TransportResult` (succès, ignoré).

## Palier suivant
Vous allez produire un email à partir d'un template Jinja.

[Continuer avec Rendre un template](mail-template.md)
