# L'envoi d'emails dans Forge (forge-mvc-mail)

Ce document explique ce que fait l'opt-in `forge-mvc-mail`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-mail` compose des messages, les envoie via des transports interchangeables (console, SMTP, log), rend des gabarits Jinja, journalise les envois, et fournit la CLI `mail:*`.

Extrait du cœur (ADR-022), il lit sa configuration depuis l'environnement (`MAIL_*`, ADR-031).

!!! warning "En développement, Forge n'envoie pas de vrais mails"
    Sans variables `MAIL_*` dans l'environnement, `MAIL_ENABLED` vaut `false` et le transport `log` est utilisé : aucune connexion SMTP n'est tentée.

    Le squelette nu ne pré-câble pas `MAIL_*` ; ajoutez le bloc à `env/dev` pour activer l'envoi.

??? note "1. Rôle du module"

    Envoyer un email demande de composer un message, de choisir un canal d'envoi, et de tracer le résultat.

    L'opt-in sépare ces trois préoccupations : un `MailMessage` (le contenu), un **transport** (le canal), un `Mailer` (l'orchestrateur qui envoie et journalise).

    Le **transport est interchangeable** : `console` ou `log` en développement, `smtp` en production, `fake`/`null` en test.
    Le code applicatif ne change pas.

??? note "2. Installation et désinstallation"

    ### Installation

    === "Depuis PyPI (stable)"

        La dernière version publiée :

        ```bash
        pip install --pre forge-mvc-mail
        ```

    === "Depuis Git (avant-garde)"

        Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

        ```bash
        source .venv/bin/activate
        pip install "git+https://github.com/caucrogeGit/Forge.git@main"
        pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-mail"
        ```

        !!! warning "Erreur « externally-managed-environment » ?"

            Lancées hors d'un venv, ces commandes visent le Python **système** (Debian 12+, Ubuntu 23.04+), protégé par PEP 668.
            La cible correcte est le venv du projet (`source .venv/bin/activate`), jamais le Python système.

    Puis activez l'opt-in :

    ```bash
    forge opt-in:enable mail
    ```


    `opt-in:enable` inscrit l'opt-in dans `optins/registry.py` (ADR-061) (l'opt-in s'importe et s'utilise directement, sans route).
    `forge opt-in:install mail` affiche la commande `pip` sans l'exécuter.

    ### Désinstallation

    ```bash
    forge opt-in:disable mail
    pip uninstall forge-mvc-mail
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre (le code n'était pas câblé), sans toucher au paquet.
    `forge opt-in:remove mail` affiche la commande `pip uninstall` sans l'exécuter.

??? note "3. Commandes"

    `forge-mvc-mail` ajoute ces commandes (entry point `forge_mvc.commands`) :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `mail:init` | Crée les dossiers, templates d'exemple et la DDL `mail_log` (idempotent). | `forge mail:init` |
    | `mail:doctor` | Diagnostique la configuration (OK/WARN/FAIL/SKIP). | `forge mail:doctor` |
    | `mail:test` | Envoie un mail de test via le transport configuré. | `forge mail:test --to vous@exemple.com` |
    | `mail:render` | Rend un gabarit sans envoi (prévisualisation). | `forge mail:render bienvenue --context ctx.json` |
    | `mail:logs` | Derniers enregistrements de `mail_log`. | `forge mail:logs --limit 20` |

??? note "4. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-mail` |
    | Module | `forge_mvc_mail` |
    | Catégorie | Communication (ADR-055) |
    | Couche | opt-in (brique optionnelle) |
    | Dépend de | `forge-mvc` (Jinja pour les gabarits) |
    | API publique | `Mailer`, `MailMessage`, transports, `MailTemplateRenderer`, `MailConfig`, `MailLogger` |
    | Transports | `console`, `log` (défaut dev), `smtp`, `fake`, `null` |
    | Configuration | `MAIL_*` (`MailConfig`) |
    | Commandes | `mail:init`, `mail:test`, `mail:render`, `mail:doctor`, `mail:logs` |
    | Journal optionnel | table `mail_log` (`MAIL_LOG_ENABLED=true`) |
    | Exceptions | `MailError` et ses sous-classes |
    | Décisions d'architecture | ADR-022 (extraction), ADR-031 (config via environnement) |
    | Installation | `pip install --pre forge-mvc-mail` |

??? note "5. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

    Le diagramme de classe montre le mailer, les transports et le message.

    Le diagramme de séquence montre un envoi de bout en bout.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre que le `Mailer` envoie un `MailMessage` via un `BaseTransport` interchangeable et renvoie un `TransportResult`.

    ```mermaid
    classDiagram
        direction LR

        class Mailer {
            +from_config() Mailer
            +send(message, message_type, related_entity, related_id) TransportResult
        }

        class MailMessage {
            <<dataclass>>
            +str subject
            +to
            +str body_text
            +str body_html
            +from_email
            +cc
            +bcc
        }

        class BaseTransport {
            <<abstract>>
            +send(message) TransportResult
        }

        class TransportResult {
            +bool success
            +str detail
        }

        Mailer --> BaseTransport : utilise
        Mailer --> MailMessage : envoie
        BaseTransport --> TransportResult : renvoie
        ConsoleTransport --|> BaseTransport
        SmtpTransport --|> BaseTransport
        LogTransport --|> BaseTransport
        NullTransport --|> BaseTransport
        FakeTransport --|> BaseTransport
    ```

    À retenir :

    - le `Mailer` orchestre ; le **transport** fait l'envoi réel ;
    - tous les transports partagent l'interface `BaseTransport.send` ;
    - changer de transport ne change pas le code applicatif ;
    - `from_config` construit le `Mailer` depuis `MAIL_*`.

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre un envoi via le transport configuré.

    ```mermaid
    sequenceDiagram
        participant App as Code applicatif
        participant Mailer as Mailer
        participant Transport as Transport (console/smtp/log)
        participant Log as MailLogger

        App->>Mailer: Mailer.from_config()
        App->>Mailer: send(MailMessage(...))
        Mailer->>Transport: send(message)
        Transport-->>Mailer: TransportResult (succès / détail)
        Mailer->>Log: journalise (si MAIL_LOG_ENABLED)
        Mailer-->>App: TransportResult
    ```

    À retenir :

    - l'application compose un `MailMessage` et appelle `send` ;
    - le `Mailer` délègue au transport et journalise ;
    - le résultat est un `TransportResult` (succès et détail) ;
    - en cas d'échec SMTP, `MailSendError` est interceptée en `TransportResult(success=False)`.

??? note "6. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `Mailer` | `Mailer(transport)` / `Mailer.from_config() -> Mailer` | orchestrateur d'envoi |
    | `Mailer.send` | `send(message, *, message_type="", related_entity="", related_id=None) -> TransportResult` | envoie un message |
    | `MailMessage` | dataclass | `subject`, `to`, `body_text`, `body_html`, `from_email`, `cc`, `bcc`, `reply_to` |
    | `MailTemplateRenderer` | classe | rend un message depuis un gabarit Jinja |
    | `MailConfig` | dataclass | configuration lue de `MAIL_*` |
    | transports | `ConsoleTransport`, `SmtpTransport`, `LogTransport`, `NullTransport`, `FakeTransport` | canaux d'envoi |
    | `TransportResult` | dataclass | résultat d'un envoi |
    | `MailLogger`, `MailLogRecord` | classes | journal des envois |
    | exceptions | `MailError`, `MailConfigurationError`, `MailSendError`, `MailTemplateError`, `MailValidationError` | erreurs |

??? note "7. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Construire un mailer configuré | `Mailer.from_config()` |
    | Composer un message | `MailMessage(subject=..., to=...)` |
    | Envoyer | `mailer.send(message)` |
    | Rendre un gabarit | `MailTemplateRenderer` |
    | Tester sans envoyer | `FakeTransport` / `NullTransport` |
    | Vérifier la configuration | `forge mail:doctor` |
    | Relire les envois | `forge mail:logs` |

??? note "8. Configuration (`MAIL_*`)"

    Le mail est lu directement depuis l'environnement (ADR-031), sans passer par le noyau.

    Le squelette nu ne fournit pas ces variables ; ajoutez le bloc `MAIL_*` à `env/dev`.
    Les défauts s'appliquent quand une variable est absente.

    | Variable | Défaut | Rôle |
    |---|---|---|
    | `MAIL_ENABLED` | `false` | Active l'envoi réel. `false` force `NullTransport` : aucun mail ne part. |
    | `MAIL_TRANSPORT` | `log` | Transport actif quand `MAIL_ENABLED=true` : `null`, `fake`, `console`, `log`, `smtp`. |
    | `MAIL_FROM` | _(vide)_ | Adresse expéditeur complète, prioritaire sur les deux suivantes. |
    | `MAIL_FROM_ADDRESS` | `noreply@localhost` | Partie adresse (si `MAIL_FROM` vide). |
    | `MAIL_FROM_NAME` | `Forge` | Partie nom (si `MAIL_FROM` vide). |
    | `MAIL_HOST` | _(vide)_ | Hôte SMTP (requis si `MAIL_TRANSPORT=smtp`). |
    | `MAIL_PORT` | `587` | Port SMTP. |
    | `MAIL_USERNAME` / `MAIL_PASSWORD` | _(vide)_ | Identifiants SMTP. |
    | `MAIL_USE_TLS` | `false` | Active `STARTTLS`. |
    | `MAIL_USE_SSL` | `false` | Utilise `SMTP_SSL` (port 465). |
    | `MAIL_TIMEOUT` | `10` | Timeout de connexion (secondes). |
    | `MAIL_LOG_DIR` | `storage/mail` | Dossier des `.eml` du transport `log`. |
    | `MAIL_TEMPLATES_DIR` | `mvc/mail/templates` | Dossier des gabarits Jinja. |
    | `MAIL_LOG_ENABLED` | `false` | Active la journalisation SQL dans `mail_log`. |

    ### Transports disponibles

    | Valeur | Comportement |
    |---|---|
    | `null` | Avale silencieusement chaque message. |
    | `fake` | Mémorise les messages (`FakeTransport.messages`). Idéal en test unitaire. |
    | `console` | Affiche le message dans le terminal. |
    | `log` | Écrit un fichier `.eml` dans `storage/mail/`. **Défaut en développement.** |
    | `smtp` | Connexion SMTP réelle via `smtplib`. À n'utiliser qu'avec un vrai serveur. |


??? note "9. Envoi par code"

    ### Envoi simple

    ```python
    from forge_mvc_mail import Mailer, MailMessage

    message = MailMessage(
        subject="Bienvenue",
        to="utilisateur@example.com",
        body_text="Bienvenue dans l'application.",
    )
    result = Mailer.from_config().send(message)
    ```

    ### Envoi avec gabarit et journalisation

    ```python
    from forge_mvc_mail import Mailer, MailTemplateRenderer

    renderer = MailTemplateRenderer()
    message = renderer.render(
        "bienvenue",
        {"prenom": "Alice", "lien": "https://exemple.com/activer/abc123"},
        to="alice@example.com",
    )
    Mailer.from_config().send(
        message,
        message_type="bienvenue",
        related_entity="contact",
        related_id=42,
    )
    ```

    Les kwargs `message_type`, `related_entity`, `related_id` sont enregistrés dans `mail_log` si `MAIL_LOG_ENABLED=true`.
    Le corps du message n'est **jamais** stocké dans le journal.

    ### Test unitaire avec `FakeTransport`

    ```python
    from forge_mvc_mail import Mailer, FakeTransport, MailMessage

    transport = FakeTransport()
    Mailer(transport).send(MailMessage(subject="Test", to="dest@test.com", body_text="Corps."))

    assert transport.sent_count == 1
    assert transport.messages[0].subject == "Test"
    ```

    !!! tip "Aide-mémoire"
        Trois objets, une responsabilité chacun :

        - `MailMessage` : le contenu ;
        - un transport : le canal ;
        - `Mailer` : envoyer et journaliser.

??? note "10. Journal `mail_log` et exceptions"

    La table `mail_log` (optionnelle, `MAIL_LOG_ENABLED=true`) trace les envois sans stocker le corps : `message_type`, `to_email`, `subject`, `transport`, `status`, métadonnées.

    | Statut | Signification |
    |---|---|
    | `sent` | mail transmis au transport |
    | `failed` | erreur SMTP (`error_message` détaille) |
    | `skipped` | `MAIL_ENABLED=false` ou transport `null` : rien envoyé, événement traçable |

    | Exception | Quand |
    |---|---|
    | `MailValidationError` | sujet vide, aucun corps, header invalide |
    | `MailConfigurationError` | transport inconnu, `MAIL_HOST` absent en `smtp` |
    | `MailTemplateError` | gabarit `_subject.txt` / `_text.txt` introuvable |
    | `MailSendError` | erreur `smtplib` (interceptée en `TransportResult(success=False)`) |

    !!! warning "Configuration via l'environnement"
        Le module lit `MAIL_*` depuis l'environnement (ADR-031), ne commitez jamais de mot de passe SMTP (`env/dev`, `env/prod` sont ignorés par Git).

        `forge mail:init` aide à poser le bloc ; `forge mail:doctor` le vérifie.

    !!! note "Sécurité par défaut"
        `MAIL_ENABLED=false` par défaut : un oubli de configuration ne déclenche jamais d'envoi accidentel.

        Les gabarits applicatifs vivent dans `mvc/mail/templates/`, pas dans l'opt-in.

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-mail` (extrait par ADR-022) : la dépendance va de l'opt-in vers le cœur.

## Voir aussi

- [Configuration (config.py)](references/config.md) : `MailConfig`, variables `MAIL_*`.
- [Message (message.py)](references/message.md) : `MailMessage`.
- [Transports (transports.py)](references/transports.md) : console, log, SMTP, fake, null.
- [Mailer (mailer.py)](references/mailer.md) : envoi et journalisation.
- [Rendu de gabarits (templates.py)](references/templates.md) : `MailTemplateRenderer`.
- [Journal des envois (log.py)](references/log.md) et [Erreurs (exceptions.py)](references/exceptions.md).
- [Welcome-Mail](welcome/debutant/mail-welcome.md) : parcours d'apprentissage.
