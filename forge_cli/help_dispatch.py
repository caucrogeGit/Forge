"""
forge_cli/help_dispatch.py — Interception centrale de `--help` / `-h`.

Ticket : CLI-HELP-FLAGS-DISPATCHER-001.

Audit préalable : docs/history/audits/cli-help-flags-audit-001.md (62 commandes
auditées, 44 sans `--help` exploitable, 6 avec effets de bord critiques).

Ce module fournit une aide générique courte pour les commandes qui ne gèrent
pas elles-mêmes `--help`, et un test booléen pour détecter le flag dans `argv`.

Politique d'inclusion : seules les commandes **sans** support `--help` natif
sont listées dans `HELP_DESCRIPTIONS`. Les commandes argparse-iso
(`auth:user:*`) et celles qui font déjà un check `--help` manuel
(`make:entity`, `make:relation`, `db:apply`, `migration:make`,
`starter:build`, `module:*`) restent gérées par leur propre `main()` afin
d'afficher leur aide détaillée — l'interception centrale ne s'applique pas
à elles.
"""
from __future__ import annotations

HELP_FLAGS: frozenset[str] = frozenset({"--help", "-h"})


# Description courte par commande — une ligne, ton constant avec forge_cli/help.py.
# Ne contient PAS les commandes qui ont déjà un `--help` natif fonctionnel.
HELP_DESCRIPTIONS: dict[str, str] = {
    # Projet
    "new":              "Crée un nouveau projet Forge.",
    "doctor":           "Diagnostic large et tolérant (lecture seule).",
    "project:check":    "Contrôle strict des conventions (CI-ready).",
    "project:audit":    "Rapport d'audit détaillé non destructif.",
    "routes:list":      "Affiche les routes déclarées par l'application.",
    # Entités
    "make:crud":        "Génère un CRUD complet (liste, fiche, formulaires).",
    "make:pivot-crud":  "Génère un sous-CRUD dédié pour un pivot avec attributs.",
    "entity:validate":  "Valide les entités et relations contre les schémas JSON.",
    "sync:entity":      "Régénère les fichiers modèles d'une entité.",
    "sync:relations":   "Régénère mvc/entities/relations.sql.",
    "sync:landing":     "Synchronise la landing page vers docs/.",
    "build:model":      "Régénère tous les modèles Python depuis leurs entités JSON.",
    "check:model":      "Vérifie la cohérence des modèles.",
    # Pages publiques
    "make:public-page":    "Génère une page statique publique.",
    "make:public-list":    "Génère une liste publique paginée.",
    "make:public-show":    "Génère une fiche publique détaillée.",
    "make:public-form":    "Génère un formulaire public.",
    "make:public-contact": "Génère une page de contact publique.",
    # Base de données
    "db:init":          "Crée la base de données depuis les entités (MariaDB).",
    "migration:status": "Statut des migrations SQL.",
    "migration:apply":  "Applique les migrations en attente.",
    "migration:diff":   "Génère un diff SQL entre entité et base.",
    # Schémas JSON
    "schema:list":      "Liste les schémas JSON Forge disponibles localement.",
    "schema:doctor":    "Diagnostique les schémas JSON Forge (présence, validité, $ref).",
    # RBAC
    "rbac:validate":    "Valide mvc/security/rbac.json avec le schéma RBAC Forge.",
    "rbac:audit":       "Audit de cohérence fonctionnelle de mvc/security/rbac.json.",
    # Starters
    "starter:list":     "Liste les starter apps disponibles.",
    # Auth
    "auth:init":        "Initialise les tables d'authentification.",
    "auth:doctor":      "Diagnostic du système d'authentification.",
    "auth:status":      "État des briques d'authentification installées.",
    "auth:list-sql":    "Affiche les fichiers SQL d'authentification.",
    "auth:user:list":   "Liste les comptes utilisateurs.",
    # Mail
    "mail:init":        "Initialise la configuration mail (dossiers et templates).",
    "mail:test":        "Envoie un mail de test.",
    "mail:render":      "Rend un template de mail (preview).",
    "mail:doctor":      "Diagnostic de la configuration mail.",
    "mail:logs":        "Affiche les derniers logs mail.",
    # Documentation
    "docs:pdf":         "Génère un PDF depuis la documentation.",
    # Internationalisation
    "i18n:init":        "Initialise les fichiers de traduction.",
    "i18n:check":       "Vérifie la complétude des traductions.",
    # Médias et JavaScript
    "upload:init":      "Configure les uploads de fichiers (dossiers storage/uploads).",
    "media:init":       "Configure les médias (alias de upload:init).",
    "js:init":          "Installe htmx, alpine ou les deux.",
    # Déploiement
    "deploy:init":      "Initialise la configuration de déploiement.",
    "deploy:check":     "Vérifie la configuration de déploiement.",
}


# Aides détaillées pour les commandes à effets de bord critiques.
# Texte utilisé tel quel (override du template générique). Ticket
# CLI-HELP-FLAGS-INIT-COMMANDS-001 : décrit usage, rôle, effets,
# prérequis, limites et rappel que --help n'exécute rien.
HELP_TEXTS_RICH: dict[str, str] = {
    "db:init": """\
Usage:
  forge db:init

Description:
  Provisionne MariaDB pour le projet Forge : base, utilisateur applicatif,
  privilèges et table forge_migrations.

Effets:
  - se connecte à MariaDB en tant que DB_ADMIN_LOGIN ;
  - CREATE DATABASE <DB_NAME> CHARACTER SET <DB_CHARSET> si la base est absente ;
  - CREATE USER <DB_APP_LOGIN>@<DB_APP_HOST> si l'utilisateur est absent ;
  - GRANT des privilèges DB_APP_PRIVILEGES (défaut : SELECT, INSERT, UPDATE,
    DELETE, CREATE, ALTER, DROP, INDEX, REFERENCES) ;
  - CREATE TABLE IF NOT EXISTS forge_migrations.

Prérequis:
  - MariaDB joignable sur DB_ADMIN_HOST:DB_ADMIN_PORT ;
  - DB_ADMIN_LOGIN avec droits CREATE DATABASE, CREATE USER et GRANT ;
  - variables DB_NAME, DB_APP_LOGIN, DB_APP_PWD, DB_APP_HOST définies dans
    env/dev ou env/prod.

Limites:
  - ne modifie ni le mot de passe ni les droits d'un utilisateur existant ;
  - refuse de continuer si DB_APP_LOGIN existe pour un autre hôte ;
  - n'efface aucune table ni aucune donnée.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.""",

    "mail:init": """\
Usage:
  forge mail:init

Description:
  Prépare l'environnement mail de développement du projet Forge.

Effets:
  - crée storage/mail/ avec un .gitkeep si absent ;
  - crée mvc/mail/templates/ si absent ;
  - écrit les templates d'exemple test_subject.txt, test_text.txt,
    test_html.html (write-if-new — un template existant n'est pas écrasé) ;
  - crée mvc/models/sql/mail_log.sql (write-if-new) ;
  - crée sample.json (contexte d'exemple, préservé s'il existe) ;
  - affiche les commandes suivantes utiles (mail:doctor, mail:test, db:apply).

Limites:
  - n'envoie aucun mail ;
  - ne modifie pas la configuration env/dev ;
  - ne touche pas aux templates existants (write-if-new).

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.""",

    "i18n:init": """\
Usage:
  forge i18n:init

Description:
  Crée le dossier translations/ et le catalogue par défaut fr.json
  (Forge i18n minimal).

Effets:
  - crée translations/ si absent (sinon message « dossier déjà présent ») ;
  - crée translations/fr.json avec un catalogue de base
    (common.*, crud.*, validation.*) ;
  - préserve un catalogue fr.json existant (jamais écrasé).

Limites:
  - ne génère aucune autre langue ;
  - ne réindexe ni ne fusionne un catalogue existant ;
  - voir forge i18n:check pour valider un catalogue déjà présent.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.""",

    "upload:init": """\
Usage:
  forge upload:init

Description:
  Initialise le stockage des uploads de fichiers utilisateurs.

Effets:
  - crée storage/uploads/ et les sous-dossiers images/, documents/, tmp/ ;
  - pose un .gitkeep dans chaque dossier créé ;
  - n'écrase aucun fichier existant.

Prérequis:
  - être à la racine d'un projet Forge.

Limites:
  - ne configure pas core.uploads (UPLOAD_MAX_SIZE, extensions autorisées,
    MIME types — voir env/dev) ;
  - ne crée pas les variantes d'image (voir forge media:init pour cela).

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.""",

    "media:init": """\
Usage:
  forge media:init

Description:
  Surensemble de upload:init pour le sous-système média (variantes d'image).

Effets:
  - crée storage/uploads/{images,documents,tmp} comme forge upload:init ;
  - crée en plus storage/uploads/images/thumbnail et
    storage/uploads/images/medium ;
  - pose un .gitkeep dans chaque dossier créé.

Limites:
  - ne génère aucune variante existante ;
  - ne traite aucune image déjà uploadée ;
  - la génération réelle des variantes est faite à l'upload par
    core.uploads, pas ici.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.""",

    "deploy:init": """\
Usage:
  forge deploy:init

Description:
  Génère les fichiers de déploiement Nginx + systemd dans deploy/.

Effets (write-if-new — aucun fichier existant n'est écrasé) :
  - deploy/nginx/forge-app.conf       (configuration Nginx reverse proxy) ;
  - deploy/systemd/forge-app.service  (unité systemd du daemon Forge) ;
  - deploy/README_DEPLOY.md           (procédure d'installation manuelle).

Prérequis:
  - être à la racine d'un projet Forge (app.py + mvc/) ;
  - UPLOAD_MAX_SIZE lisible depuis env/dev pour calibrer client_max_body_size.

Limites:
  - ne déploie rien ;
  - ne contacte aucun serveur distant ;
  - ne lance ni Nginx ni systemd — la mise en place reste manuelle ;
  - voir forge deploy:check pour valider l'environnement.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.""",
}


def wants_help(args: list[str]) -> bool:
    """Retourne True si `--help` ou `-h` figure dans `args`."""
    return any(arg in HELP_FLAGS for arg in args)


def format_command_help(command: str) -> str | None:
    """Retourne le texte d'aide centralisé pour `command`, ou None si non géré.

    Cherche d'abord une aide riche (HELP_TEXTS_RICH) ; sinon construit un
    texte court à partir d'une description (HELP_DESCRIPTIONS).
    """
    rich = HELP_TEXTS_RICH.get(command)
    if rich is not None:
        return rich
    description = HELP_DESCRIPTIONS.get(command)
    if description is None:
        return None
    return (
        f"Usage:\n"
        f"  forge {command} [options]\n"
        f"\n"
        f"Description:\n"
        f"  {description}\n"
        f"\n"
        f"Options:\n"
        f"  -h, --help    Affiche cette aide.\n"
        f"\n"
        f"Voir docs/reference/cli-commands.md pour les arguments détaillés."
    )
