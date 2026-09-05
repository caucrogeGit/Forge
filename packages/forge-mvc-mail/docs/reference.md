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

??? note "2. Installation"

    !!! warning "Prérequis : activez le venv du projet"

        Quelle que soit la source, installez **dans le venv du projet** :

        ```bash
        source .venv/bin/activate
        ```

        Lancé hors d'un venv, `pip` vise le Python **système** (Debian 12+, Ubuntu 23.04+),
        protégé par PEP 668. Il refuse alors d'installer, pour ne pas écraser les paquets
        gérés par `apt`, et affiche `externally-managed-environment`.
        Le venv de projet créé par `forge new` n'a pas ce verrou.

    #### Installer le paquet

    <div class="canal">

    #### A. Depuis PyPI (stable)

    La dernière version publiée :

    ```bash
    pip install --pre forge-mvc-mail
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-mail"
    ```

    </div>

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-mail`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-mail==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    ```bash
    forge opt-in:enable mail --apply
    ```

    L'opt-in est inscrit dans `optins/registry.py` (ADR-061), ce qui le rend visible du
    projet.
    `--apply` est **obligatoire** : sans lui, la commande simule et n'écrit rien.

    #### 3. Poser ce dont il a besoin

    Cet opt-in n'apporte aucune table, mais il a tout de même une initialisation :

    ```bash
    forge mail:init
    ```

    Elle crée `storage/mail/`, où le transport de développement dépose les messages.
    Ne pas avoir de tables ne veut pas dire n'avoir rien à faire.

    #### 4. Le brancher là où il agit

    Il s'importe dans le code qui s'en sert. Il n'y a ni route à monter ni middleware
    à poser.

    #### 5. Le prouver

    ```bash
    make check
    forge doctor
    ```

    Puis un premier usage réel.
    Un opt-in installé, inscrit et provisionné qu'aucun code n'appelle n'est pas
    opérationnel : il est seulement présent.


??? note "4. Désinstallation"

    ```bash
    forge opt-in:disable mail
    pip uninstall forge-mvc-mail
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre (le code n'était pas câblé), sans toucher au paquet.
    `forge opt-in:remove mail` affiche la commande `pip uninstall` sans l'exécuter.

??? note "5. Commandes"

    `forge-mvc-mail` ajoute ces commandes (entry point `forge_mvc.commands`) :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `mail:init` | Crée les dossiers, templates d'exemple et la DDL `mail_log` (idempotent). | `forge mail:init` |
    | `mail:doctor` | Diagnostique la configuration (OK/WARN/FAIL/SKIP). | `forge mail:doctor` |
    | `mail:test` | Envoie un mail de test via le transport configuré. | `forge mail:test --to vous@exemple.com` |
    | `mail:render` | Rend un gabarit sans envoi (prévisualisation). | `forge mail:render bienvenue --context ctx.json` |
    | `mail:logs` | Derniers enregistrements de `mail_log`. | `forge mail:logs --limit 20` |

??? note "6. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-mail` |
    | Module | `forge_mvc_mail` |
    | Catégorie | Communication (ADR-055) |
    | Couche | opt-in (brique optionnelle) |
    | Dépend de | `forge-mvc` (Jinja pour les gabarits) |
    | API publique | `Mailer`, `MailMessage`, transports, `MailTemplateRenderer`, `MailConfig`, `MailLogger`, `message_to_payload`, `make_mail_job_handler`, `Attachment` |
    | Transports | `console`, `log` (défaut dev), `smtp`, `fake`, `null` |
    | Configuration | `MAIL_*` (`MailConfig`) |
    | Commandes | `mail:init`, `mail:test`, `mail:render`, `mail:doctor`, `mail:logs` |
    | Journal optionnel | table `mail_log` (`MAIL_LOG_ENABLED=true`) |
    | Exceptions | `MailError` et ses sous-classes |
    | Décisions d'architecture | ADR-022 (extraction), ADR-031 (config via environnement) |
    | Installation | `pip install --pre forge-mvc-mail` |

??? note "7. Schémas UML"

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

??? note "8. API publique"

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

??? note "9. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Construire un mailer configuré | `Mailer.from_config()` |
    | Composer un message | `MailMessage(subject=..., to=...)` |
    | Envoyer | `mailer.send(message)` |
    | Rendre un gabarit | `MailTemplateRenderer` |
    | Tester sans envoyer | `FakeTransport` / `NullTransport` |
    | Vérifier la configuration | `forge mail:doctor` |
    | Relire les envois | `forge mail:logs` |

??? note "10. Configuration (`MAIL_*`)"

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


??? note "10 bis. Différer l'envoi par la file de tâches"

    Envoyer un email pendant une requête HTTP la fait attendre le serveur SMTP.

    Une seconde de latence est courante, dix le sont aussi quand le relais est lent, et une panne du relais devient une panne du formulaire : l'utilisateur voit une erreur alors que son inscription est enregistrée (`MAIL-QUEUE-VIA-JOBS-001`).

    Le module `queueing` fournit de quoi confier l'envoi à `forge-mvc-jobs`.

    | Élément | Rôle |
    |---|---|
    | `MAIL_JOB_TASK` | nom de tâche, nommé une fois pour les deux côtés |
    | `message_to_payload(message, ...)` | traduit un message en charge utile JSON |
    | `message_from_payload(payload)` | reconstruit le message côté ouvrier |
    | `make_mail_job_handler(mailer=None)` | rend le gestionnaire à enregistrer |
    | `MailPayloadError` | charge utile inexploitable |

    Côté requête, on met en file au lieu d'envoyer.

    ```python
    from forge_mvc_jobs import enqueue
    from forge_mvc_mail import MAIL_JOB_TASK, message_to_payload

    enqueue(MAIL_JOB_TASK, message_to_payload(message, message_type="bienvenue"))
    ```

    Côté ouvrier, on enregistre le gestionnaire.

    ```python
    from forge_mvc_jobs import run_worker
    from forge_mvc_mail import MAIL_JOB_TASK, make_mail_job_handler

    run_worker({MAIL_JOB_TASK: make_mail_job_handler()})
    ```

    !!! info "Les deux opt-ins ne se connaissent pas"
        `forge-mvc-mail` n'importe jamais `forge_mvc_jobs`, et l'inverse est vrai aussi.

        Ce module traduit un message et rend un gestionnaire ; c'est l'application qui met les deux en présence, et elle seule décide d'installer les deux paquets.
        Un test le vérifie sur l'arbre syntaxique du module, le docstring montrant justement l'exemple d'import.

    !!! warning "Le gestionnaire lève quand l'envoi échoue"
        C'est ce qui déclenche le réessai de la file.

        Rendre `None` en silence ferait marquer la tâche comme réussie, et l'email ne partirait jamais.
        Un envoi **sauté** par `NullTransport` n'est pas un échec : réessayer sans fin un envoi que personne ne veut serait absurde.

    !!! danger "Une pièce jointe ne passe pas par la file"
        Les pièces jointes et la mise en file ont été livrées séparément, et **ne composaient pas** (`MAIL-QUEUE-ATTACHMENTS-REFUSED-001`).

        `message_to_payload` recopie huit champs nommés, et `attachments` n'en faisait pas partie : un message avec pièce jointe passait la sérialisation sans erreur et ressortait sans elle.
        L'email partait, le journal inscrivait `sent`, et le destinataire recevait un corps annonçant un document absent.

        La charge utile est du JSON rangé dans la colonne `payload` de la table `jobs`, de type `text`.
        Sur MariaDB, un `TEXT` tient soixante-cinq mille octets ; une pièce jointe de dix mégaoctets, plafond du paquet, en ferait quatorze millions une fois encodée. Deux cent treize fois la capacité de la colonne.
        Élargir la colonne ferait de la file une réserve de fichiers, ce qu'elle n'est pas.

        `message_to_payload` **refuse** donc, en nommant les fichiers concernés.

    !!! info "Le refus est uniforme, et non conditionné à la taille"
        Accepter les petites pièces jointes ferait dépendre le comportement du poids du fichier.

        Cela marcherait en développement avec un PDF d'essai, et échouerait en production sur un vrai document, par une erreur de base opaque.
        Une fonctionnalité qui marche parfois est la plus difficile à diagnostiquer.

    !!! tip "Ce qu'il faut faire à la place"
        Rangez le fichier, mettez en file sa **référence**, et attachez le dans le gestionnaire au moment de l'envoi.

        ```python
        enqueue(MAIL_JOB_TASK, message_to_payload(message) | {"facture_id": 12})
        ```

        Le gestionnaire relit la référence, charge le fichier et appelle `message.with_attachment(...)` avant d'envoyer.

    !!! info "Le message est validé à la mise en file"
        Un sujet vide ou une adresse forgée est refusé dans la requête, là où l'utilisateur le voit.

        Différer l'erreur jusqu'à l'ouvrier la rendrait invisible, et la tâche échouerait sans que personne ne sache pourquoi.

    !!! info "Le journal des envois suit"
        `message_type`, `related_entity` et `related_id` sont transportés avec le message.

        Sans eux, différer un envoi rendrait `mail_log` muet, alors que c'est précisément quand l'envoi est asynchrone qu'on a besoin de sa trace.

??? note "11. Envoi par code"

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

??? note "12. Journal `mail_log` et exceptions"

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

## Pièces jointes

Une facture, un export, un justificatif : un email en porte souvent un.

```python
message = MailMessage(subject="Facture", to=client.email, body_text="Ci-joint.")
message = message.with_attachment("facture.pdf", pdf_bytes)
mailer.send(message)
```

!!! info "Le message n'est pas modifié, un nouveau est rendu"
    `with_attachment` rend un message augmenté plutôt que de changer celui qu'on lui donne.

    Un message mis en file puis complété ailleurs partirait sinon dans deux états selon l'ordre des appels.

!!! danger "Le nom de fichier est assaini"
    Il voyage dans un en-tête MIME et s'affiche chez le destinataire, et vient souvent d'un fichier déposé par un utilisateur.

    Un chemin est réduit à son dernier segment, `../../etc/passwd` devenant `passwd`, et un saut de ligne est retiré : il couperait l'en-tête en deux.

!!! info "Un type inconnu vaut mieux qu'un type faux"
    Le type MIME est deviné du nom, et retombe sur `application/octet-stream`.

    Un type erroné serait suivi par le client mail pour ouvrir le fichier.
    Il peut être déclaré explicitement, et une forme malformée est refusée.

La taille est bornée à dix mégaoctets. Un relais refuserait au delà, et un message refusé après coup est plus difficile à diagnostiquer qu'un refus à la construction.

## Gabarits réutilisables

Un en-tête et un pied de page réécrits dans chaque gabarit sont oubliés quelque part le jour où l'adresse change.

L'héritage Jinja fonctionne depuis toujours, le moteur montant un chargeur sur le dossier des gabarits.
Rien ne le disait, et rien ne le figeait : c'est ce que corrige `MAIL-LAYOUTS-001`.

```html
<!-- layout_html.html -->
<header>Mon École</header>
{% block corps %}{% endblock %}
<footer>Ne pas répondre à ce message.</footer>
```

```html
<!-- bienvenue_html.html -->
{% extends "layout_html.html" %}
{% block corps %}<p>Bonjour {{ prenom }}</p>{% endblock %}
```

Le corps texte a le sien, `layout_text.txt` : donner un layout à l'un sans l'autre rendrait les deux versions du message incohérentes.

!!! info "Un layout n'est pas un gabarit de message"
    Il n'a ni sujet ni corps propre, et le rendre directement échoue.

    Seuls les trios `<nom>_subject.txt`, `<nom>_text.txt` et `<nom>_html.html` sont des messages.

!!! warning "L'échappement reste actif"
    Hériter n'ouvre pas d'injection : une variable de contexte est échappée dans le corps HTML comme avant.

## Vérifier sa configuration sans écrire à personne

`mail:test` envoyait toujours. Vérifier sa configuration commençait donc par écrire à quelqu'un, et exigeait un relais joignable (`MAIL-TEST-GUIDED-001`).

```bash
forge mail:test --to vous@exemple.com --dry-run   # montre ce qui partirait
forge mail:test --to vous@exemple.com             # envoie
```

Le diagnostic précède désormais l'envoi : transport, `MAIL_ENABLED`, expéditeur et serveur.

!!! info "Un « non envoyé » annoncé après coup se lit comme un échec"
    `MAIL_ENABLED=false` est signalé **avant** la tentative, avec la façon de l'activer.

    C'est une configuration voulue, pas une panne, et l'ordre de l'affichage le dit.

Un transport local affiche « aucun serveur » plutôt que `None:0`, qui ferait chercher une configuration absente.
