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


def wants_help(args: list[str]) -> bool:
    """Retourne True si `--help` ou `-h` figure dans `args`."""
    return any(arg in HELP_FLAGS for arg in args)


def format_command_help(command: str) -> str | None:
    """Retourne le texte d'aide centralisé pour `command`, ou None si non géré.

    Le texte reste court : il décrit la commande, signale `-h, --help` et
    renvoie vers la documentation pour les arguments détaillés.
    """
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
