# Le journal des envois dans Forge Mail

Ce document décrit la journalisation des envois mail dans la table `mail_log`.

Le fichier de code correspondant est `forge_mvc_mail/log.py`.

## 1. À quoi sert ce module ?

Pour le suivi et l'audit, on veut savoir quels mails ont été envoyés, à qui, avec quel statut.
Ce module journalise chaque envoi dans la table `mail_log`, **sans jamais stocker le corps** du message (ni `body_text` ni `body_html`).

La journalisation est **opt-in** : active seulement si `MAIL_LOG_ENABLED=true`.

## 2. L'enregistrement (`MailLogRecord`)

| Attribut | Rôle |
|---|---|
| `message_type` | type logique du message (ex. `welcome`) |
| `to_email` | destinataire principal |
| `subject` | sujet |
| `transport` | transport utilisé |
| `status` | issue de l'envoi |
| `error_message` | message d'erreur éventuel |
| `related_entity`, `related_id` | rattachement métier optionnel |
| `created_at`, `sent_at` | horodatages |

Aucun corps de message n'est stocké, par conception.

## 3. Le logger (`MailLogger`)

`MailLogger` écrit dans `mail_log` si `MAIL_LOG_ENABLED=true`.
Il est **silencieux en cas d'erreur DB** : un problème de journalisation ne fait jamais échouer un envoi.

## 4. La table `mail_log`

La table doit être créée quand la journalisation est activée.
Elle conserve les métadonnées d'envoi (destinataire, sujet, transport, statut, horodatages), sans contenu de message.

## 5. Contextes d'utilisation

- **Audit** : consulter `mail_log` pour retracer les envois.
- **Désactivé par défaut** : sans `MAIL_LOG_ENABLED=true`, aucune écriture.

## 6. Voir aussi

- [La configuration mail](config.md) : `MAIL_LOG_ENABLED`.
- [Les exceptions](exceptions.md) : les erreurs d'envoi journalisées.
- [Vue d'ensemble Mail](../reference.md).
