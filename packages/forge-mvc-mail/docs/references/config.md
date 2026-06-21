# La configuration mail dans Forge

Ce document décrit la configuration du service mail, lue depuis l'environnement.

Le fichier de code correspondant est `forge_mvc_mail/config.py`.

## 1. À quoi sert ce module ?

Le service mail a besoin de savoir quel transport utiliser, depuis quelle adresse expédier, et comment joindre le serveur SMTP.
`MailConfig` rassemble ces réglages, lus depuis les variables d'environnement.

## 2. L'objet `MailConfig`

| Attribut | Type | Rôle |
|---|---|---|
| `enabled` | `bool` | le mail est-il actif |
| `transport_name` | `str` | transport choisi (`log`, `console`, `smtp`, `null`…) |
| `from_email` | `str` | adresse d'expédition par défaut |
| `log_dir` | `str` | dossier des fichiers `.eml` (transport `log`) |
| `host`, `port` | `str`, `int` | serveur SMTP |
| `username`, `password` | `str` | identifiants SMTP |
| `use_tls`, `use_ssl` | `bool` | mode de chiffrement de la connexion |
| `timeout` | `float` | délai SMTP en secondes |
| `verify_tls` | `bool` | vérifier le certificat TLS (défaut `True`) |

## 3. Les variables d'environnement

Les réglages se positionnent via les variables `MAIL_*` de l'environnement : `MAIL_ENABLED`, `MAIL_TRANSPORT`, `MAIL_FROM`, `MAIL_HOST`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_USE_TLS`, `MAIL_USE_SSL`, `MAIL_TIMEOUT`, `MAIL_LOG_ENABLED`.

En développement, le transport par défaut est `log` : aucun SMTP réel n'est requis.

## 4. Contextes d'utilisation

- **Démarrage** : la configuration est lue une fois et fournie au transport.
- **Tests** : injecter des valeurs pour viser le transport `fake` ou `console`.

## 5. Voir aussi

- [Les transports](transports.md) : ce que `transport_name` sélectionne.
- [Le journal des envois](log.md) : piloté par `MAIL_LOG_ENABLED`.
- [Vue d'ensemble Mail](../reference.md).
