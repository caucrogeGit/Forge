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

    # ── Schémas JSON & RBAC (CLI-HELP-FLAGS-SCHEMA-RBAC-001) ─────────────────

    "schema:list": """\
Usage:
  forge schema:list [--json]

Description:
  Liste les schémas JSON Forge embarqués (registre interne).

Effets:
  - lit forge_cli/schemas/forge.schema.index.json (registre des schémas) ;
  - pour chaque schéma référencé, vérifie l'existence du fichier ;
  - affiche le nom, le chemin et le statut OK / MANQUANT ;
  - ne modifie aucun fichier du projet ni du framework.

Options:
  --json        Sortie machine JSON stable (aucune ligne humaine).
  -h, --help    Affiche cette aide sans exécuter la commande.

Codes de retour:
  0  registre lisible et tous les schémas présents
  1  registre illisible OU au moins un schéma manquant

Limites:
  - ne valide pas le contenu des schémas (voir forge schema:doctor) ;
  - ne valide pas les entités utilisateur (voir forge entity:validate).""",

    "schema:doctor": """\
Usage:
  forge schema:doctor [--json]

Description:
  Diagnostique chaque schéma JSON Forge référencé dans le registre :
  présence, validité JSON, conformité Draft 2020-12 et résolution des $ref
  locaux.

Effets:
  - lit forge_cli/schemas/forge.schema.index.json ;
  - pour chaque schéma référencé : fichier présent, JSON valide,
    $schema = https://json-schema.org/draft/2020-12/schema, $id présent,
    chaque $ref local (hors '#' et 'http') pointe vers un fichier existant ;
  - affiche un rapport humain ou JSON ;
  - ne modifie aucun fichier.

Options:
  --json        Sortie machine JSON stable (aucune ligne humaine).
  -h, --help    Affiche cette aide sans exécuter la commande.

Codes de retour:
  0  aucun problème détecté
  1  au moins une erreur (registre illisible, schéma absent/invalide,
     $ref mort, $schema/$id manquant)

Limites:
  - ne valide pas les entités utilisateur mvc/entities/*.json
    (c'est le rôle de forge entity:validate) ;
  - ne valide pas les contrats applicatifs comme mvc/security/rbac.json
    (voir forge rbac:validate).""",

    "rbac:validate": """\
Usage:
  forge rbac:validate [--json]

Description:
  Valide mvc/security/rbac.json contre le schéma RBAC Forge
  (forge_cli/schemas/rbac.schema.json, JSON Schema Draft 2020-12).

Effets:
  - cherche mvc/security/rbac.json à la racine du projet ;
  - si absent : exit 0 (RBAC est opt-in, son absence n'est pas une erreur) ;
  - sinon : charge le fichier, instancie un Draft202012Validator,
    parcourt les erreurs schéma et affiche un rapport humain ou JSON.

Prérequis:
  - jsonschema et referencing installés (déjà dans requirements.txt).

Options:
  --json        Sortie machine JSON (errors_count, errors, roles_count…).
  -h, --help    Affiche cette aide sans exécuter la commande.

Codes de retour:
  0  fichier absent OU fichier valide
  1  fichier présent mais invalide (JSON ou schéma) OU schémas Forge
     introuvables

Limites:
  - validation structurelle uniquement (conformité au schéma) ;
  - pour l'audit fonctionnel (rôles orphelins, permissions inutilisées,
    entités sans CRUD), voir forge rbac:audit.""",

    "rbac:audit": """\
Usage:
  forge rbac:audit [--json]

Description:
  Audit de cohérence fonctionnelle de mvc/security/rbac.json. Va au-delà
  de la validation schéma : détecte les rôles sans permissions, les entités
  sans actions CRUD, les permissions non déclarées et les permissions
  inutilisées.

Effets:
  - applique d'abord la validation schéma (équivalent rbac:validate) ;
  - puis parcourt rôles, entités et permissions pour détecter les
    incohérences ;
  - affiche un rapport humain ou JSON avec compte d'erreurs et
    d'avertissements ;
  - ne modifie aucun fichier.

Options:
  --json        Sortie machine JSON (warnings_count, errors_count, détails).
  -h, --help    Affiche cette aide sans exécuter la commande.

Codes de retour:
  0  fichier absent OU fichier valide (avec ou sans avertissements)
  1  fichier présent mais invalide (JSON ou schéma) OU option inconnue

Limites:
  - n'altère ni rbac.json ni le code applicatif ;
  - ne corrige rien automatiquement — les avertissements doivent être
    traités manuellement.""",

    # ── Pages publiques (CLI-HELP-FLAGS-PUBLIC-PAGES-001) ────────────────────
    # Convention Forge : une page publique est distincte du CRUD admin. Elle
    # est faite pour le visiteur, pas pour l'administrateur, et ne doit jamais
    # exposer directement les actions destructives d'un CRUD.

    "make:public-page": """\
Usage:
  forge make:public-page <nom>

Description:
  Génère une page publique statique distincte du CRUD admin.
  Le <nom> est slugifié (kebab-case) ; les caractères acceptés sont
  lettres, chiffres et tirets internes.

Effets (write-if-new — aucun fichier existant n'est écrasé) :
  - crée mvc/views/public/<slug>.html (template Jinja2 héritant de
    layouts/public.html) ;
  - crée ou complète mvc/controllers/public_pages_controller.py avec une
    méthode <slug>() ;
  - insère la route GET /<slug> dans mvc/routes.py (public, sans CSRF) ;
  - n'écrase ni le template, ni la méthode, ni la route si déjà présents.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - page statique uniquement (aucun lien automatique vers une entité) ;
  - ne remplace pas make:crud ;
  - ne publie rien automatiquement ;
  - n'expose aucune action destructive au visiteur.""",

    "make:public-list": """\
Usage:
  forge make:public-list <Entite>

Description:
  Génère une liste publique paginée pour une entité existante.
  Lecture seule, conçue pour le visiteur — pas un CRUD admin exposé.

Effets (write-if-new — aucun fichier existant n'est écrasé) :
  - lit mvc/entities/<Entite>/<entite>.json pour découvrir les champs
    publics ;
  - crée mvc/views/public/<plural>/list.html (template Jinja2 paginé) ;
  - ajoute la méthode liste publique au contrôleur correspondant ;
  - insère la route GET /<plural> dans mvc/routes.py.

Prérequis:
  - l'entité <Entite> doit exister (forge make:entity <Entite>).

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - lecture seule — aucune action de création/modification/suppression ;
  - différent du CRUD admin : pas d'écran de gestion ;
  - ne génère pas de fiche détaillée (voir forge make:public-show).""",

    "make:public-show": """\
Usage:
  forge make:public-show <Entite>

Description:
  Génère une fiche publique détaillée pour une entité existante.
  Affichage en lecture seule destiné au visiteur.

Effets (write-if-new — aucun fichier existant n'est écrasé) :
  - lit mvc/entities/<Entite>/<entite>.json pour découvrir les champs
    publics ;
  - crée mvc/views/public/<plural>/show.html (template fiche) ;
  - ajoute la méthode fiche publique au contrôleur correspondant ;
  - insère la route GET /<plural>/<id> dans mvc/routes.py.

Prérequis:
  - l'entité <Entite> doit exister.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - lecture seule — n'expose aucune action destructive ;
  - différent de la vue détaillée du CRUD admin ;
  - ne génère pas la liste publique (voir forge make:public-list).""",

    "make:public-form": """\
Usage:
  forge make:public-form <Entite>

Description:
  Génère un formulaire public pour soumettre une instance d'entité,
  avec protection CSRF intégrée.

Effets (write-if-new — aucun fichier existant n'est écrasé) :
  - lit mvc/entities/<Entite>/<entite>.json pour découvrir les champs ;
  - crée mvc/views/public/<plural>/form.html (template avec
    {{ csrf_token }}) ;
  - ajoute la méthode formulaire (GET) et la méthode soumission (POST) au
    contrôleur ;
  - insère les routes GET et POST /<plural>/form dans mvc/routes.py.

Prérequis:
  - l'entité <Entite> doit exister ;
  - core.security.csrf actif pour valider le jeton à la soumission.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - protège contre CSRF mais ne remplace pas la validation métier
    côté contrôleur ;
  - différent du formulaire admin du CRUD ;
  - n'expose ni édition ni suppression — un formulaire public sert à
    soumettre, pas à éditer en place.""",

    "make:public-contact": """\
Usage:
  forge make:public-contact

Description:
  Génère la page de contact publique du projet (cas particulier de page
  publique avec route /contact figée). N'attend aucun argument.

Effets (write-if-new — aucun fichier existant n'est écrasé) :
  - crée mvc/views/public/contact.html (formulaire de contact Jinja2) ;
  - crée ou complète mvc/controllers/public_pages_controller.py avec la
    méthode contact() ;
  - insère la route GET /contact (et POST si applicable) dans
    mvc/routes.py.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - route /contact figée (non paramétrable) ;
  - aucun envoi de mail n'est branché par défaut — la soumission est à
    raccorder dans le contrôleur (voir forge mail:test pour tester
    l'envoi).""",
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
