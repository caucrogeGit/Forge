# pyright: strict
"""Catalogue canonique des opt-ins officiels Forge.

Ticket : OPTIN-CLI-VERBS-001 (ADR-016, palier 3a).

Source de vérité unique pour la famille de commandes ``opt-in:*``. Chaque opt-in
officiel est une brique optionnelle distribuée comme package PyPI
``forge-mvc-*`` (voir docs/reference/vocabulaire-opt-in.md). Le catalogue ne
décrit que *ce qui existe* (plan distribution) ; l'état d'activation d'un projet
donné se lit ailleurs (couche ``optins/``).
"""
from __future__ import annotations

from typing import NamedTuple


# Les trois formes d'intégration d'un opt-in dans une application (ADR-016 D8) :
#   - "route"        : la brique possède ses routes (register_*_routes) →
#                      câblage projet via la couche optins/ ;
#   - "library"      : bibliothèque pure → on importe et on appelle, rien à
#                      brancher côté projet ;
#   - "crosscutting" : se greffe dans un flux existant (décorateurs, starter).
KIND_ROUTE = "route"
KIND_LIBRARY = "library"
KIND_CROSSCUTTING = "crosscutting"
#   - "cli"          : opt-in piloté par ses propres commandes (ex. deploy:*),
#                      sans câblage applicatif ni import bibliothèque (ADR-053).
KIND_CLI = "cli"


# Destination fonctionnelle d'un opt-in (ADR-055), distincte du kind technique :
# le kind dit *comment* la brique se branche, la catégorie dit *à quoi* elle sert.
# Slugs en anglais (ADR-003) ; libellés d'affichage en français.
CATEGORY_DATABASE = "database"
CATEGORY_MEDIA = "media"
CATEGORY_SECURITY = "security"
CATEGORY_COMMUNICATION = "communication"
CATEGORY_DATA = "data"
CATEGORY_I18N = "i18n"
CATEGORY_CONTENT = "content"
CATEGORY_CONFIGURATION = "configuration"
CATEGORY_OPERATIONS = "operations"

# Liste canonique + ordre d'affichage (CLI et docs partagent cette taxonomie).
CATEGORY_LABELS: dict[str, str] = {
    CATEGORY_DATABASE:      "Bases de données",
    CATEGORY_MEDIA:         "Médias et fichiers",
    CATEGORY_SECURITY:      "Sécurité et accès",
    CATEGORY_COMMUNICATION: "Communication",
    CATEGORY_DATA:          "Données et modélisation",
    CATEGORY_I18N:          "Internationalisation",
    CATEGORY_CONTENT:       "Contenu",
    CATEGORY_CONFIGURATION: "Configuration",
    CATEGORY_OPERATIONS:    "Exploitation et outillage",
}
CATEGORY_ORDER: tuple[str, ...] = tuple(CATEGORY_LABELS)


class OptIn(NamedTuple):
    """Une brique opt-in officielle."""

    name: str            # identifiant court (mfa, rbac, …)
    package_dist: str    # nom de distribution PyPI (forge-mvc-…)
    package_import: str  # namespace Python importable (forge_mvc_…)
    kind: str            # forme d'intégration : route | library | crosscutting | cli
    category: str        # destination fonctionnelle (ADR-055), voir CATEGORY_*
    summary: str         # description d'une ligne


OFFICIAL_OPTINS: dict[str, OptIn] = {
    "mfa": OptIn(
        "mfa", "forge-mvc-mfa", "forge_mvc_mfa", KIND_CROSSCUTTING, CATEGORY_SECURITY,
        "Authentification multi-facteurs (TOTP, codes de récupération).",
    ),
    "rbac": OptIn(
        "rbac", "forge-mvc-rbac", "forge_mvc_rbac", KIND_CROSSCUTTING, CATEGORY_SECURITY,
        "Contrôle d'accès par rôles et permissions déclaratives.",
    ),
    "audit": OptIn(
        "audit", "forge-mvc-audit", "forge_mvc_audit", KIND_LIBRARY, CATEGORY_SECURITY,
        "Journal d'audit applicatif (table audit_log), API record_audit/get_audit_log, borné, SQL visible.",
    ),
    "workflow": OptIn(
        "workflow", "forge-mvc-workflow", "forge_mvc_workflow", KIND_LIBRARY, CATEGORY_DATA,
        "Statuts et transitions applicatives.",
    ),
    "stats": OptIn(
        "stats", "forge-mvc-stats", "forge_mvc_stats", KIND_LIBRARY, CATEGORY_DATA,
        "Journal d'événements et agrégats par comptage (par nom ou catégorie).",
    ),
    "pivot": OptIn(
        "pivot", "forge-mvc-pivot", "forge_mvc_pivot", KIND_LIBRARY, CATEGORY_DATA,
        "Tables pivot enrichies (many_to_many avec attributs) et générateur make:pivot-crud.",
    ),
    "import-export": OptIn(
        "import-export", "forge-mvc-import-export", "forge_mvc_import_export", KIND_LIBRARY, CATEGORY_DATA,
        "Échange CSV : import (validation par champ, rapport d'erreurs) et export programmatique (to_csv).",
    ),
    "images": OptIn(
        "images", "forge-mvc-images", "forge_mvc_images", KIND_LIBRARY, CATEGORY_MEDIA,
        "Traitement d'image (Pillow) + gestion applicative des médias (galerie, couverture).",
    ),
    "files": OptIn(
        "files", "forge-mvc-files", "forge_mvc_files", KIND_LIBRARY, CATEGORY_MEDIA,
        "Upload générique : écriture sécurisée, storage, service de fichiers, rate-limit.",
    ),
    "video": OptIn(
        "video", "forge-mvc-video", "forge_mvc_video", KIND_ROUTE, CATEGORY_MEDIA,
        "Upload, transcodage MP4 et lecture vidéo en streaming (HTTP Range).",
    ),
    "audio": OptIn(
        "audio", "forge-mvc-audio", "forge_mvc_audio", KIND_ROUTE, CATEGORY_MEDIA,
        "Upload, sondage, transcodage MP3 et lecture audio en streaming (HTTP Range).",
    ),
    "mail": OptIn(
        "mail", "forge-mvc-mail", "forge_mvc_mail", KIND_LIBRARY, CATEGORY_COMMUNICATION,
        "Envoi d'emails : composition, transports interchangeables, templates Jinja, CLI mail:*.",
    ),
    "notifications": OptIn(
        "notifications", "forge-mvc-notifications", "forge_mvc_notifications", KIND_LIBRARY, CATEGORY_COMMUNICATION,
        "Notifications in-app (table notifications), API notify/get_notifications/mark_read, SQL visible.",
    ),
    "iot": OptIn(
        "iot", "forge-mvc-iot", "forge_mvc_iot", KIND_ROUTE, CATEGORY_COMMUNICATION,
        "Réception/exposition de données IoT (MQTT, stockage, API HTTP).",
    ),
    "i18n": OptIn(
        "i18n", "forge-mvc-i18n", "forge_mvc_i18n", KIND_LIBRARY, CATEGORY_I18N,
        "Internationalisation : catalogues JSON, locale par défaut/fallback, helper trans().",
    ),
    "qrcode": OptIn(
        "qrcode", "forge-mvc-qrcode", "forge_mvc_qrcode", KIND_LIBRARY, CATEGORY_CONTENT,
        "Génération de QR Codes (PNG/SVG) depuis texte ou URL, réponse HTTP servable depuis un contrôleur.",
    ),
    "settings": OptIn(
        "settings", "forge-mvc-settings", "forge_mvc_settings", KIND_LIBRARY, CATEGORY_CONFIGURATION,
        "Paramètres applicatifs persistés en base (table app_settings), API get_setting/set_setting, SQL visible.",
    ),
    "admin": OptIn(
        "admin", "forge-mvc-admin", "forge_mvc_admin", KIND_CROSSCUTTING, CATEGORY_OPERATIONS,
        "Back-office applicatif : CRUD générique sur les entités, auth + CSRF, RBAC optionnel, commandes admin:init/admin:doctor.",
    ),
    "jobs": OptIn(
        "jobs", "forge-mvc-jobs", "forge_mvc_jobs", KIND_LIBRARY, CATEGORY_OPERATIONS,
        "File de tâches de fond adossée à la base : enqueue depuis une requête, worker explicite, sans broker ni async.",
    ),
    "deploy": OptIn(
        "deploy", "forge-mvc-deploy", "forge_mvc_deploy", KIND_CLI, CATEGORY_OPERATIONS,
        "Outillage de déploiement : deploy:init (wsgi.py, Nginx, systemd) et deploy:check, CLI-only.",
    ),
}


# Backends BDD : famille EXCLUSIVE (ADR-054), un seul par projet, découvert par
# l'entry point forge_mvc.db_backend. Hors OFFICIAL_OPTINS : ils ne s'« enable »
# pas comme les autres opt-ins (sémantique « choisis-en un »), ils sont pilotés
# par la famille db:* et présentés à part par opt-in:list (ADR-055).
class DbBackend(NamedTuple):
    name: str
    package_dist: str
    package_import: str
    summary: str


DB_BACKENDS: tuple[DbBackend, ...] = (
    DbBackend(
        "mariadb", "forge-mvc-mariadb", "forge_mvc_mariadb",
        "Backend MariaDB (pool de connexions). Backend de production de référence.",
    ),
    DbBackend(
        "sqlite", "forge-mvc-sqlite", "forge_mvc_sqlite",
        "Backend SQLite (stdlib), sans serveur. Idéal développement, tests et onboarding.",
    ),
    DbBackend(
        "postgres", "forge-mvc-postgres", "forge_mvc_postgres",
        "Backend PostgreSQL (psycopg). Statut Alpha (intégration serveur à valider).",
    ),
    DbBackend(
        "mssql", "forge-mvc-mssql", "forge_mvc_mssql",
        "Backend Microsoft SQL Server (pyodbc). Statut Alpha (intégration serveur à valider).",
    ),
)


def optin_names() -> list[str]:
    """Identifiants courts des opt-ins officiels, triés."""
    return sorted(OFFICIAL_OPTINS)


def optins_by_category() -> dict[str, list[OptIn]]:
    """Opt-ins officiels groupés par catégorie, dans l'ordre CATEGORY_ORDER.

    Ne retourne que les catégories non vides. Taxonomie unique partagée par la
    CLI (opt-in:list) et la documentation (ADR-055).
    """
    grouped: dict[str, list[OptIn]] = {category: [] for category in CATEGORY_ORDER}
    for opt in OFFICIAL_OPTINS.values():
        grouped.setdefault(opt.category, []).append(opt)
    return {category: grouped[category] for category in CATEGORY_ORDER if grouped.get(category)}


# La famille opt-in:* ne gère que les opt-ins officiels. Un module local que
# le développeur écrit lui-même reste géré par module:* (ADR-016 A2).
LOCAL_MODULE_HINT = (
    "Pour un module local que vous écrivez vous-même, voir : forge module:install"
)
