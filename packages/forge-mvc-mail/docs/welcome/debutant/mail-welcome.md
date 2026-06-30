# Welcome Mail

## Niveau débutant : envoyer un premier email

Premier contact avec l'opt-in `forge-mvc-mail`.
Un formulaire saisit un destinataire et un message.
Le contrôleur construit un `MailMessage` et l'envoie via `Mailer` sur un `ConsoleTransport`.
L'email s'affiche alors dans la console du serveur, aucun serveur SMTP n'est requis.

Ce palier suppose que l'opt-in est installé.
Voir [Installer welcome-mail](../installation.md).

??? note "Contrôleur"
    Créez le fichier `mvc/controllers/mail_welcome_controller.py` :

    ```python
    # mvc/controllers/mail_welcome_controller.py
    from core.http.request import Request
    from core.http.response import Response
    from forge_mvc_mail import ConsoleTransport, MailError, Mailer, MailMessage
    from core.mvc.controller.base_controller import BaseController


    class MailWelcomeController(BaseController):
        """Composer et envoyer un email sur le transport console."""

        @staticmethod
        def index(request: Request) -> Response:
            return BaseController.render(
                "mail_welcome/index.html",
                context={"csrf_token": BaseController.csrf_token(request)},
                request=request,
            )

        @staticmethod
        def send(request: Request) -> Response:
            recipient = (request.form("recipient") or "").strip()
            body = (request.form("message") or "").strip()
            context = {"csrf_token": BaseController.csrf_token(request)}
            try:
                message = MailMessage(
                    subject="Message depuis Forge",
                    to=recipient,
                    body_text=body,
                    from_email="noreply@example.test",
                )
                result = Mailer(ConsoleTransport()).send(message)
            except MailError as exc:
                context["error"] = str(exc)
                return BaseController.render(
                    "mail_welcome/index.html", context=context, request=request
                )
            context["sent"] = result.success
            context["recipient"] = recipient
            return BaseController.render(
                "mail_welcome/index.html", context=context, request=request
            )
    ```

    | Élément | Rôle |
    |---|---|
    | `MailMessage` | Décrit l'email : sujet, destinataire, corps, expéditeur. |
    | `ConsoleTransport` | Affiche l'email dans la console au lieu de l'envoyer. |
    | `Mailer(...).send(...)` | Confie le message au transport et retourne un résultat. |
    | `MailError` | Erreur levée si le message est invalide. |

??? note "Vue"
    Créez le fichier `mvc/views/mail_welcome/index.html` :

    ```html
    <!DOCTYPE html>
    <html lang="fr">
    <head>
      <meta charset="UTF-8">
      <title>Envoyer un email</title>
    </head>
    <body>
      <h1>Envoyer un email</h1>

      {% if error %}
      <p data-level="error"><strong>{{ error }}</strong></p>
      {% endif %}

      {% if sent %}
      <p data-level="success">
        Email envoyé à <strong>{{ recipient }}</strong>
        (affiché dans la console du serveur).
      </p>
      {% endif %}

      <form method="post" action="/mail-welcome">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <label>Destinataire <input type="email" name="recipient" required></label>
        <label>Message <textarea name="message" required></textarea></label>
        <button type="submit">Envoyer</button>
      </form>
    </body>
    </html>
    ```

??? note "Route"
    Dans `mvc/routes.py`, ajoutez l'import du contrôleur puis les deux routes à l'intérieur du groupe public :

    ```python
    # mvc/routes.py
    from mvc.controllers.mail_welcome_controller import MailWelcomeController

    with router.group("", public=True) as public:
        public.add("GET", "/mail-welcome", MailWelcomeController.index, name="mail_welcome_index")
        public.add("POST", "/mail-welcome", MailWelcomeController.send, name="mail_welcome_send")
    ```

    La route `GET` affiche le formulaire, la route `POST` reçoit la soumission et envoie l'email.

## À retenir
- Un email se décrit avec un `MailMessage` (sujet, destinataire, corps).
- Un `Mailer` envoie le message via un transport.
- `ConsoleTransport` affiche l'email dans la console, sans serveur SMTP.
- Le jeton CSRF protège le formulaire d'envoi.

## Palier suivant
Vous allez composer un message plus riche et inspecter ses champs sans l'envoyer.

[Continuer avec Composer un message](mail-message.md)
