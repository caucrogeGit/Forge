# Opt-ins officiels de Forge

Le cœur de Forge est minimal.
Les fonctionnalités au-delà du noyau sont des opt-ins : des paquets indépendants, installés et activés séparément.

Le cœur ne dépend d'aucun d'eux.
Cette page liste les opt-ins officiels par usage ; chaque nom renvoie à sa documentation de référence.

!!! note "Installer un opt-in"
    Chaque opt-in s'installe avec `pip install --pre forge-mvc-<nom>`, puis s'active selon son contrat.
    Voir le [contrat d'installation des opt-ins](../install/opt-ins.md) et le [vocabulaire opt-in](../reference/vocabulaire-opt-in.md).

## Sécurité et accès

| Opt-in | Rôle |
|--------|------|
| [RBAC](../rbac/reference.md) | rôles et permissions déclaratives |
| [MFA](../mfa/reference.md) | authentification multi-facteurs (TOTP, codes de récupération) |
| [Audit](../audit/reference.md) | journal d'audit applicatif (table `audit_log`) |

## Données et persistance

| Opt-in | Rôle |
|--------|------|
| [Settings](../settings/reference.md) | paramètres applicatifs persistés en base SQL |
| [Jobs](../jobs/reference.md) | file de tâches de fond adossée à la base SQL, sans broker |
| [Notifications](../notifications/reference.md) | notifications in-app (table `notifications`) |
| [Import/Export CSV](../import-export/reference.md) | import validé et export programmatique en CSV |
| [Statistiques](../stats/reference.md) | agrégats et compteurs d'événements |
| [Pivot](../pivot/reference.md) | tables pivot enrichies (`many_to_many` avec attributs) |

## Médias et fichiers

| Opt-in | Rôle |
|--------|------|
| [Fichiers](../files/reference.md) | upload générique : écriture sécurisée, stockage, service de fichiers (HTTP Range) |
| [Images](../images/reference.md) | traitement et gestion applicative des images (Pillow) |
| [Audio](../audio/reference.md) | upload, sondage, transcodage MP3 et lecture en streaming |
| [Vidéo](../video/reference.md) | upload, transcodage MP4 (H.264/AAC) et lecture en streaming |

## Contenu et communication

| Opt-in | Rôle |
|--------|------|
| [Mail](../mail/reference.md) | envoi de courriels, transports interchangeables |
| [i18n](../i18n/reference.md) | internationalisation par catalogues JSON, helper `trans()` |
| [QR Code](../qrcode/reference.md) | génération de QR Codes PNG/SVG servables depuis un contrôleur |

## Applicatif et exploitation

| Opt-in | Rôle |
|--------|------|
| [Workflow](../workflow/reference.md) | cycles de vie applicatifs (statuts, transitions, historique) |
| [Admin](../admin/reference.md) | back-office applicatif : CRUD générique, auth, CSRF, RBAC optionnel |
| [IoT](../iot/reference.md) | réception et exposition de données IoT (MQTT, stockage, API HTTP) |
| [Déploiement](../deploy/reference.md) | outillage de déploiement CLI : gabarits Nginx/systemd/WSGI |

## Bases de données (backends)

Les backends sont mutuellement exclusifs : un seul par projet (ADR-054).
Vue d'ensemble et aide au choix : [Bases de données dans Forge](../guide/bases-de-donnees.md).

| Backend | Moteur | Maturité |
|---------|--------|----------|
| [MariaDB](../mariadb/index.md) | MariaDB / MySQL | RC |
| [SQLite](../sqlite/index.md) | SQLite (sans serveur) | RC |
| [PostgreSQL](../postgres/index.md) | PostgreSQL | Alpha |
| [SQL Server](../mssql/index.md) | SQL Server | Alpha |

## Outils de développement

| Opt-in | Rôle |
|--------|------|
| [Infrastructure de test](../testing/reference.md) | `FakeRequest` et plugin pytest pour tester Forge et ses opt-ins (dev-only) |

## Voir aussi

- [Contrat d'installation des opt-ins](../install/opt-ins.md) : installer et activer un opt-in.
- [Vocabulaire opt-in](../reference/vocabulaire-opt-in.md) : les termes du cycle de vie.
- [Système de modules](../reference/modules.md) : le mécanisme technique sous-jacent.
