# Envoyer un email

Objectif : composer un email et l'**envoyer**, sans serveur SMTP en
développement.

**Ce que vous allez apprendre :** le module `core.mail`. On construit un
`MailMessage` (sujet, destinataire, corps) puis on le confie à un `Mailer`
branché sur un **transport**. En développement, `ConsoleTransport` **affiche**
l'email dans la console du serveur : vous apprenez le flux complet sans
configurer le moindre SMTP.

Palier 3 du **niveau avancé** de la
[progression officielle des starters](../../index.md#progression-recommandee),
après [Téléverser un fichier](file-upload.md).

## Ce que ce starter montre

- un formulaire qui saisit destinataire et message (POST + CSRF) ;
- la construction d'un `MailMessage` ;
- l'envoi via `Mailer(ConsoleTransport())` — l'email s'affiche dans la console ;
- la gestion d'une erreur d'envoi (`MailError`).

Aucune base de données.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `MailMessage` | Décrire l'email (sujet, destinataire, corps). | [Mail](../../../reference/api.md#coremail) |
| `Mailer` / `ConsoleTransport` | Envoyer l'email ; en dev, l'afficher dans la console. | [Mail](../../../reference/api.md#coremail) |
| `BaseController.csrf_token` | Protéger le formulaire d'envoi. | [BaseController](../../../reference/api.md#coremvccontroller) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/send-email`, saisissez un destinataire et un
message, puis cliquez **Envoyer** : la page confirme l'envoi et l'email complet
s'affiche **dans la console du serveur**.

## Le contrôleur

```python
# mvc/controllers/send_email_controller.py
from core.mail import ConsoleTransport, MailError, Mailer, MailMessage


class SendEmailController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "send_email/index.html",
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
            return BaseController.render("send_email/index.html", context=context, request=request)
        context["sent"] = result.success
        context["recipient"] = recipient
        return BaseController.render("send_email/index.html", context=context, request=request)
```

### Comprendre ce code

- `MailMessage(...)` décrit l'email. Il **valide** les adresses : un destinataire
  vide ou invalide lève une `MailError`, que l'on attrape pour afficher l'erreur.
- `Mailer(ConsoleTransport())` envoie via le transport **console** : l'email
  apparaît dans la sortie du serveur. En production, on brancherait un transport
  SMTP — le code du contrôleur ne changerait pas.
- `result.success` confirme l'envoi.

## La vue

```html
<!-- mvc/views/send_email/index.html -->
{% if sent %}
<p data-level="success">Email envoyé à <strong>{{ recipient }}</strong>.</p>
{% endif %}

<form method="post" action="/send-email">
  <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
  <label>Destinataire <input type="email" name="recipient" required></label>
  <label>Message <textarea name="message" required></textarea></label>
  <button type="submit">Envoyer</button>
</form>
```

### Comprendre ce code

- Le `type="email"` aide le navigateur ; la **vraie** validation reste côté
  serveur (`MailMessage`).
- Le formulaire est protégé par **CSRF**, comme tout POST.

## À retenir

- `core.mail` sépare le **message** (`MailMessage`) du **transport**
  (`ConsoleTransport`, SMTP…).
- En développement, `ConsoleTransport` affiche l'email — aucun SMTP requis.
- Changer de transport ne change pas le code métier : c'est l'intérêt de
  l'abstraction.

## Après ce starter

Vous savez composer et envoyer un email. Faites le point dans le bilan du
niveau.

[Bilan du niveau avancé](bilan.md)
