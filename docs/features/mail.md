# Brique mail générique — Forge 1.2

> **En développement, Forge n'envoie pas de vrais mails par défaut.**
>
> `MAIL_ENABLED=false` et `MAIL_TRANSPORT=log` sont les valeurs par défaut de `env/example`.
> Aucune connexion SMTP n'est tentée tant que vous ne les changez pas explicitement dans `env/dev`.

---

## Principe d'architecture

`core/mail/` est une brique générique du framework. Elle ne contient aucune logique métier, aucun template applicatif, aucun workflow et aucune queue.

Elle fournit :

- **`MailMessage`** — représentation d'un message (sujet, corps texte, HTML, destinataires) ;
- **Transports interchangeables** — `null`, `fake`, `console`, `log`, `smtp` ;
- **`Mailer`** — point d'entrée unique pour envoyer un message via le transport configuré ;
- **`MailTemplateRenderer`** — rendu Jinja2 de templates de mails ;
- **`MailLogger`** — journalisation optionnelle des envois dans `mail_log`.

Les templates applicatifs (`bienvenue.txt`, `commande_confirmee.txt`, etc.) appartiennent à `mvc/mail/templates/`, pas à `core/`.

---

## Initialisation

```bash
forge mail:init
```

Crée ou complète la structure nécessaire :

```
mvc/mail/templates/          ← templates Jinja2 de vos mails
    test_subject.txt         ← exemple de sujet (préservé si modifié)
    test_text.txt            ← exemple de corps texte
    test_html.html           ← exemple de corps HTML
storage/mail/                ← logs .eml du transport log
    .gitkeep
mvc/models/sql/mail_log.sql  ← DDL de la table mail_log (préservé si existant)
```

Idempotent : les fichiers existants ne sont jamais écrasés. Lance ensuite :

```bash
forge db:apply               # crée la table mail_log si MAIL_LOG_ENABLED=true
```

---

## Vérification de la configuration

```bash
forge mail:doctor
```

Affiche le résultat de chaque contrôle :

```
Forge mail:doctor

  [WARN]  MAIL_ENABLED — false — aucun mail ne sera envoyé (NullTransport activé)
  [OK]    MAIL_TRANSPORT — log
  [OK]    Dossier templates — mvc/mail/templates — 3 fichier(s)
  [OK]    Stockage mail — storage/mail présent
  [OK]    MAIL_FROM — Forge <noreply@localhost>
  [SKIP]  MAIL_LOG_ENABLED — false — journalisation désactivée

1 avertissement(s), 0 erreur(s).
```

Statuts possibles : `OK`, `WARN`, `FAIL`, `SKIP`. Un `FAIL` provoque un code de retour 1.

---

## Test d'envoi

```bash
forge mail:test --to vous@exemple.com
```

Crée un message de test et l'envoie via le transport configuré. Affiche le nom du transport utilisé et le statut.

En développement avec `MAIL_TRANSPORT=log` :

```
[INFO]      Transport    : LogTransport
[INFO]      MAIL_ENABLED : True
[OK]        Mail envoyé (ou journalisé).
```

Le fichier `.eml` est déposé dans `storage/mail/`.

---

## Rendu d'un template sans envoi

```bash
forge mail:render bienvenue
forge mail:render bienvenue --context ctx.json
```

Charge le template `bienvenue` depuis `mvc/mail/templates/`, interpole le contexte et affiche le sujet, le corps texte et le corps HTML dans le terminal. Utile pour vérifier l'interpolation Jinja2 avant de connecter un vrai SMTP.

Structure des fichiers pour le template `bienvenue` :

```
mvc/mail/templates/
    bienvenue_subject.txt    ← obligatoire
    bienvenue_text.txt       ← obligatoire
    bienvenue_html.html      ← optionnel
```

Le fichier `--context` est un JSON quelconque :

```json
{
  "prenom": "Alice",
  "lien": "https://exemple.com/activer/abc123"
}
```

---

## Journal des envois

```bash
forge mail:logs
forge mail:logs --limit 5
```

Affiche les derniers enregistrements de `mail_log` (20 par défaut). Nécessite `MAIL_LOG_ENABLED=true` et que la table existe (`forge db:apply`).

```
ID      DATE                STATUS    TRANSPORT     TO                              SUJET
1       2026-05-01 10:04:12 [OK]      log           dest@example.com                Test Forge — 2026-05-01
```

Si `MAIL_LOG_ENABLED=false`, la commande affiche un avertissement et ne tente aucune connexion DB.

---

## Configuration

### Variables d'environnement

| Variable | Défaut | Rôle |
|---|---|---|
| `MAIL_ENABLED` | `false` | Active l'envoi réel. `false` force `NullTransport` — aucun mail ne part. |
| `MAIL_TRANSPORT` | `log` | Transport actif quand `MAIL_ENABLED=true` : `null`, `fake`, `console`, `log`, `smtp`. |
| `MAIL_FROM` | _(vide)_ | Adresse expéditeur complète. Prioritaire sur les deux variables suivantes. |
| `MAIL_FROM_ADDRESS` | `noreply@localhost` | Partie adresse (utilisée si `MAIL_FROM` est vide). |
| `MAIL_FROM_NAME` | `Forge` | Partie nom (utilisée si `MAIL_FROM` est vide). |
| `MAIL_HOST` | _(vide)_ | Hôte SMTP (requis si `MAIL_TRANSPORT=smtp`). |
| `MAIL_PORT` | `587` | Port SMTP. |
| `MAIL_USERNAME` | _(vide)_ | Identifiant SMTP. |
| `MAIL_PASSWORD` | _(vide)_ | Mot de passe SMTP. |
| `MAIL_USE_TLS` | `false` | Active `STARTTLS`. |
| `MAIL_USE_SSL` | `false` | Utilise `SMTP_SSL` (port 465). |
| `MAIL_TIMEOUT` | `10` | Timeout de connexion en secondes. |
| `MAIL_LOG_DIR` | `storage/mail` | Dossier des fichiers `.eml` du transport `log`. |
| `MAIL_TEMPLATES_DIR` | `mvc/mail/templates` | Dossier des templates Jinja2. |
| `MAIL_LOG_ENABLED` | `false` | Active la journalisation SQL dans `mail_log`. |

### Transports disponibles

| Valeur | Comportement |
|---|---|
| `null` | Avale silencieusement chaque message. |
| `fake` | Stocke les messages en mémoire (`FakeTransport.messages`). Idéal pour les tests unitaires. |
| `console` | Affiche le message dans le terminal. |
| `log` | Écrit un fichier `.eml` dans `storage/mail/`. **Défaut en développement.** |
| `smtp` | Connexion SMTP réelle via `smtplib`. À n'utiliser qu'avec un vrai serveur SMTP. |

### Adresse expéditeur par défaut

Si `MAIL_FROM` est vide, Forge compose l'adresse automatiquement :

```
Forge <noreply@localhost>
```

En production, définissez `MAIL_FROM` explicitement :

```env
MAIL_FROM=MonApp <noreply@mondomaine.fr>
```

---

## Envoi par code

### Envoi simple

```python
from core.mail import Mailer, MailMessage

message = MailMessage(
    subject="Bienvenue",
    to="utilisateur@example.com",
    body_text="Bienvenue dans l'application.",
)
result = Mailer.from_config().send(message)
```

### Envoi avec template

```python
from core.mail import Mailer, MailTemplateRenderer

renderer = MailTemplateRenderer()
message  = renderer.render(
    "bienvenue",
    {"prenom": "Alice", "lien": "https://exemple.com/activer/abc123"},
    to="alice@example.com",
)
result = Mailer.from_config().send(
    message,
    message_type="bienvenue",
    related_entity="contact",
    related_id=42,
)
```

### Journalisation

Les kwargs optionnels `message_type`, `related_entity` et `related_id` sont enregistrés dans `mail_log` si `MAIL_LOG_ENABLED=true`. Le corps du message (`body_text`, `body_html`) n'est **jamais** stocké dans le journal.

### Envoi vers plusieurs destinataires

```python
message = MailMessage(
    subject="Rappel",
    to=["alice@example.com", "bob@example.com"],
    cc="equipe@example.com",
    bcc="archive@example.com",
    reply_to="support@example.com",
    body_text="Message envoyé par Forge.",
)
```

### Tests unitaires avec `FakeTransport`

```python
from core.mail import Mailer, FakeTransport, MailMessage

transport = FakeTransport()
mailer    = Mailer(transport)
mailer.send(MailMessage(subject="Test", to="dest@test.com", body_text="Corps."))

assert transport.sent_count == 1
assert transport.messages[0].subject == "Test"
```

---

## Table `mail_log`

Créée par `forge mail:init` (génère `mvc/models/sql/mail_log.sql`) et appliquée par `forge db:apply`.

```sql
CREATE TABLE IF NOT EXISTS mail_log (
    id             INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    message_type   VARCHAR(100) NOT NULL DEFAULT '',
    to_email       VARCHAR(255) NOT NULL DEFAULT '',
    subject        VARCHAR(500) NOT NULL DEFAULT '',
    transport      VARCHAR(50)  NOT NULL DEFAULT '',
    status         ENUM('sent', 'failed', 'skipped') NOT NULL,
    error_message  TEXT,
    related_entity VARCHAR(100),
    related_id     INT,
    created_at     DATETIME     NOT NULL,
    sent_at        DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Statuts :**

| Statut | Signification |
|---|---|
| `sent` | Mail effectivement transmis au transport. |
| `failed` | Erreur SMTP — `error_message` contient le détail. |
| `skipped` | `MAIL_ENABLED=false` ou transport `null` — aucun mail parti, événement traçable. |

Le statut `skipped` est intentionnel : il permet de comprendre pourquoi aucun mail n'est parti sans avoir à chercher dans les logs serveur.

---

## Exceptions

| Exception | Levée par | Quand |
|---|---|---|
| `MailValidationError` | `MailMessage` | Sujet vide, aucun corps, caractère interdit dans un header. |
| `MailConfigurationError` | `MailConfig` | Transport inconnu, `MAIL_HOST` absent en mode `smtp`. |
| `MailTemplateError` | `MailTemplateRenderer` | Template `_subject.txt` ou `_text.txt` introuvable. |
| `MailSendError` | `SmtpTransport` | Erreur `smtplib`. `Mailer.send()` l'intercepte → `TransportResult(success=False)`. |

---

## Cycle de mise en place

```bash
# 1. Créer les fichiers nécessaires
forge mail:init

# 2. Vérifier la configuration
forge mail:doctor

# 3. Tester sans SMTP réel (MAIL_TRANSPORT=log par défaut)
forge mail:test --to vous@exemple.com

# 4. Vérifier le rendu d'un template
forge mail:render test --context sample.json

# 5. Si MAIL_LOG_ENABLED=true : créer la table
forge db:apply

# 6. Consulter les logs
forge mail:logs --limit 20
```

Pour activer un SMTP réel en développement, ajoutez dans `env/dev` (non commité) :

```env
MAIL_ENABLED=true
MAIL_TRANSPORT=smtp
MAIL_HOST=smtp.mailtrap.io
MAIL_PORT=587
MAIL_USERNAME=votre_identifiant
MAIL_PASSWORD=votre_mot_de_passe
MAIL_USE_TLS=true
MAIL_FROM=MonApp <noreply@exemple.com>
```

Ne commitez jamais de mots de passe SMTP. `env/dev` et `env/prod` sont ignorés par Git.

---

## Bonnes pratiques

- `MAIL_ENABLED=false` est la valeur par défaut — un oubli de configuration ne déclenche jamais d'envoi accidentel.
- `MAIL_TRANSPORT=log` est le transport par défaut — les mails sont lisibles dans `storage/mail/` sans serveur SMTP.
- `MAIL_LOG_ENABLED=false` est le défaut — pas de table SQL requise pour démarrer.
- Le corps du mail n'est jamais stocké dans `mail_log` : seuls le sujet, le destinataire, le transport, le statut et les métadonnées métier sont enregistrés.
- `core/mail/` ne contient aucun template applicatif — placez vos templates dans `mvc/mail/templates/`.
