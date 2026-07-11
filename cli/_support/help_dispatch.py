# pyright: strict
"""
cli/_support/help_dispatch.py — Interception centrale de `--help` / `-h`.

Tickets : CLI-HELP-FLAGS-DISPATCHER-001 (mécanisme),
          CLI-HELP-FLAGS-* (enrichissements par groupe),
          CLI-HELP-FLAGS-CLOSING-AUDIT-001 (clôture du chantier).

Audit initial   : docs/history/audits/cli-help-flags-audit-001.md.
Audit de clôture : docs/history/audits/cli-help-flags-closing-audit-001.md
(62 commandes dispatchées par forge.py, 45 aide riche, 17 aide native,
 0 aide générique non assumée).

Ce module fournit deux niveaux d'aide centrale pour les commandes qui ne
gèrent pas elles-mêmes `--help`, et un test booléen pour détecter le flag
dans `argv`.

Politique d'inclusion : seules les commandes **sans** support `--help` natif
sont listées dans ce module. Les commandes argparse-iso (`auth:user:*`,
8 cas) et celles qui font déjà un check `--help` manuel (`make:entity`,
`make:relation`, `db:apply`, `migration:make`, `module:*`,
8 cas) restent gérées par leur propre `main()` afin d'afficher leur aide
détaillée — l'interception centrale ne s'applique pas à elles.

Architecture en deux dictionnaires :

- `HELP_TEXTS_RICH`  : aide longue par commande (Usage / Description /
                       Effets / Prérequis / Options / Limites). Consultée
                       en priorité par `format_command_help`.
- `HELP_DESCRIPTIONS` : description d'une ligne. Sert de **filet de
                        sécurité** :
                        1. Si une commande est dans HELP_DESCRIPTIONS et
                           absente de HELP_TEXTS_RICH, le gabarit
                           générique de `format_command_help` est
                           produit ;
                        2. Si une nouvelle commande est ajoutée à
                           HELP_DESCRIPTIONS sans entrée riche, elle
                           reçoit immédiatement un `--help` propre, sans
                           effet de bord ;
                        3. Si une commande est dans `forge.py` mais
                           absente des deux dicts ET sans aide native,
                           `tests/meta/test_cli_help_flags_closing_audit_001.py`
                           lève une erreur de classification (garde-fou).

Aujourd'hui les 45 commandes riches sont aussi présentes dans
HELP_DESCRIPTIONS — la version riche prend le pas. La duplication est
**délibérée** : elle garantit qu'aucune future entrée riche introuvable
ne tombe pas dans le fallback.
"""
from __future__ import annotations

HELP_FLAGS: frozenset[str] = frozenset({"--help", "-h"})


# Description courte par commande — une ligne, ton constant avec cli/_support/help.py.
# Ne contient PAS les commandes qui ont déjà un `--help` natif fonctionnel.
# Filet de sécurité : si une commande arrive ici sans entrée riche
# correspondante dans HELP_TEXTS_RICH, format_command_help produit un
# gabarit générique (Usage + Description + Options) — pas d'effet de bord.
# Décision CLI-HELP-FLAGS-CLOSING-AUDIT-001 : on conserve la duplication
# pour qu'une future commande oubliée bénéficie quand même d'une aide
# minimale et de l'interception dispatcher.
HELP_DESCRIPTIONS: dict[str, str] = {
    # Projet
    "new":              "Crée un nouveau projet Forge.",
    "skeleton:upgrade": "Ajoute au projet les fichiers du squelette manquants (write-if-new).",
    "run":              "Lance Forge (dev) ou affiche la stratégie WSGI (prod).",
    "update":           "Met à jour Forge dans l'environnement courant (.venv / pipx).",
    "doctor":           "Diagnostic large et tolérant (lecture seule).",
    "project:check":    "Contrôle strict des conventions (CI-ready).",
    "project:audit":    "Rapport d'audit détaillé non destructif.",
    "routes:list":      "Affiche les routes déclarées par l'application.",
    "agents:init":      "Génère/rafraîchit la guidance agent IA (CLAUDE.md, AGENTS.md, ADR-001) ; --check, --force, --settings.",
    # Entités
    "make:crud":        "Génère un CRUD complet (liste, fiche, formulaires).",
    "make:pivot-crud":  "Génère un sous-CRUD dédié pour un pivot avec attributs.",
    "entity:validate":  "Valide les entités et relations contre les schémas JSON.",
    "entity:doc":       "Documente entités et relations (Markdown + diagramme Mermaid).",
    "sync:entity":      "Régénère les fichiers modèles d'une entité.",
    "sync:relations":   "Régénère mvc/entities/relations.sql.",
    "build:model":      "Régénère tous les modèles Python depuis leurs entités JSON.",
    "check:model":      "Vérifie la cohérence des modèles.",
    # Pages publiques
    "make:public-page":    "Génère une page statique publique.",
    "make:public-list":    "Génère une liste publique paginée.",
    "make:public-show":    "Génère une fiche publique détaillée.",
    "make:public-form":    "Génère un formulaire public.",
    "make:public-contact": "Génère une page de contact publique.",
    # Base de données
    "db:config":        "Amorce les variables d'environnement du backend BDD.",
    "db:init":          "Affiche le SQL de provisioning de la base MariaDB (--run pour exécuter).",
    "migration:status": "Statut des migrations SQL.",
    "migration:apply":  "Applique les migrations en attente.",
    "migration:diff":   "Génère un diff SQL entre entité et base.",
    # Schémas JSON
    "schema:list":      "Liste les schémas JSON Forge disponibles localement.",
    "schema:doctor":    "Diagnostique les schémas JSON Forge (présence, validité, $ref).",
    # RBAC
    "rbac:validate":    "Valide mvc/security/rbac.json avec le schéma RBAC Forge.",
    "rbac:audit":       "Audit de cohérence fonctionnelle de mvc/security/rbac.json.",
    # Auth
    "auth:init":        "Initialise les tables d'authentification.",
    "make:auth":        "Scaffolde le flux de connexion (contrôleur, vue, routes).",
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
    # IoT
    "iot:doctor":       "Diagnostic du module IoT (statique ; --db pour la table, --mqtt pour le broker).",
    "iot:init":         "Copie la migration IoT vers mvc/migrations/ (idempotent, sans appliquer).",
    "iot:simulate":     "Publie des mesures MQTT factices conformes au contrat (sans capteur).",
    "iot:listen":       "Écoute le broker MQTT et insère les mesures reçues dans iot_events.",
    # Vidéo
    "video:doctor":     "Diagnostic du module vidéo (package, config, présence ffmpeg/ffprobe).",
    "video:init":       "Copie la migration vidéo vers mvc/migrations/ (idempotent, sans appliquer).",
    "video:upload":     "Upload une vidéo source : <fichier> [--title]  (statut uploaded).",
    "video:process":    "Traite une vidéo (probe + poster + MP4) : <id> ou --pending.",
    "video:cleanup":    "Purge vidéos failed / fichiers orphelins (dry-run par défaut, --apply).",
    # Audio
    "audio:doctor":     "Diagnostic du module audio (package, config, présence ffmpeg/ffprobe).",
    # Admin
    "admin:init":       "Prépare la structure mvc/admin/ du back-office (write-if-new, sans écrasement).",
    "admin:doctor":     "Vérifie la cohérence des ressources admin avec les contrats d'entité (lecture seule).",
    # Opt-ins (branchement projet)
    "opt-in:install":   "Affiche la commande d'installation du package d'un opt-in officiel.",
    "opt-in:remove":    "Affiche la commande de désinstallation du package d'un opt-in officiel.",
    "opt-in:enable":    "Branche un opt-in dans le projet (optins/) ; dry-run par défaut, --apply pour écrire.",
    "opt-in:disable":   "Débranche un opt-in du projet (retire optins/) ; dry-run par défaut, --apply pour écrire.",
    "opt-in:list":      "Affiche les opt-ins officiels et leur état (lecture seule).",
    # Documentation
    "docs:pdf":         "Génère un PDF depuis la documentation.",
    # Internationalisation
    "i18n:init":        "Initialise les fichiers de traduction.",
    "i18n:check":       "Vérifie la complétude des traductions.",
    # Médias et JavaScript
    "upload:init":      "Configure les uploads de fichiers (dossiers storage/uploads).",
    "media:init":       "Configure les médias (alias de upload:init).",
    "images:init":      "Copie la migration Images vers mvc/migrations/ (idempotent, sans appliquer).",
    "js:init":          "Installe htmx, alpine ou les deux.",
    # Déploiement
    "deploy:init":      "Initialise la configuration de déploiement.",
    "deploy:check":     "Vérifie la configuration de déploiement.",
    # Opt-ins applicatifs (ADR-052)
    "settings:init":      "Prépare la table des paramètres applicatifs (forge-mvc-settings).",
    "audit:init":         "Prépare le journal d'audit applicatif (forge-mvc-audit).",
    "jobs:init":          "Prépare la file de tâches de fond (forge-mvc-jobs).",
    "notifications:init": "Prépare les notifications in-app (forge-mvc-notifications).",
    "sessions:init":      "Copie la migration Sessions vers mvc/migrations/ (idempotent, sans appliquer).",
    "sessions:gc":        "Purge les sessions expirées (à brancher sur cron/systemd).",
}


# Aides détaillées pour les commandes à effets de bord critiques.
# Texte utilisé tel quel (override du template générique). Ticket
# CLI-HELP-FLAGS-INIT-COMMANDS-001 : décrit usage, rôle, effets,
# prérequis, limites et rappel que --help n'exécute rien.
HELP_TEXTS_RICH: dict[str, str] = {
    "settings:init": """\
Usage:
  forge settings:init

Description:
  Prépare la migration SQL de l'opt-in forge-mvc-settings (table app_settings)
  dans mvc/migrations/, sans exécuter de SQL.

Effets (write-if-new — aucun fichier existant n'est écrasé) :
  - copie la migration embarquée du paquet vers mvc/migrations/.

Prérequis:
  - forge-mvc-settings installé (pip install --pre forge-mvc-settings) ;
  - être à la racine d'un projet Forge (dossier mvc/).

Limites:
  - n'exécute aucun SQL et ne contacte pas MariaDB ;
  - lancer ensuite forge migration:apply pour appliquer la migration.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.""",
    "audit:init": """\
Usage:
  forge audit:init

Description:
  Prépare la migration SQL de l'opt-in forge-mvc-audit (table audit_log)
  dans mvc/migrations/, sans exécuter de SQL.

Effets (write-if-new — aucun fichier existant n'est écrasé) :
  - copie la migration embarquée du paquet vers mvc/migrations/.

Prérequis:
  - forge-mvc-audit installé (pip install --pre forge-mvc-audit) ;
  - être à la racine d'un projet Forge (dossier mvc/).

Limites:
  - n'exécute aucun SQL et ne contacte pas MariaDB ;
  - lancer ensuite forge migration:apply pour appliquer la migration.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.""",
    "jobs:init": """\
Usage:
  forge jobs:init

Description:
  Prépare la migration SQL de l'opt-in forge-mvc-jobs (table jobs)
  dans mvc/migrations/, sans exécuter de SQL.

Effets (write-if-new — aucun fichier existant n'est écrasé) :
  - copie la migration embarquée du paquet vers mvc/migrations/.

Prérequis:
  - forge-mvc-jobs installé (pip install --pre forge-mvc-jobs) ;
  - être à la racine d'un projet Forge (dossier mvc/).

Limites:
  - n'exécute aucun SQL et ne contacte pas MariaDB ;
  - lancer ensuite forge migration:apply pour appliquer la migration.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.""",
    "notifications:init": """\
Usage:
  forge notifications:init

Description:
  Prépare la migration SQL de l'opt-in forge-mvc-notifications (table
  notifications) dans mvc/migrations/, sans exécuter de SQL.

Effets (write-if-new — aucun fichier existant n'est écrasé) :
  - copie la migration embarquée du paquet vers mvc/migrations/.

Prérequis:
  - forge-mvc-notifications installé (pip install --pre forge-mvc-notifications) ;
  - être à la racine d'un projet Forge (dossier mvc/).

Limites:
  - n'exécute aucun SQL et ne contacte pas MariaDB ;
  - lancer ensuite forge migration:apply pour appliquer la migration.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.""",
    "images:init": """\
Usage:
  forge images:init

Description:
  Prépare la migration SQL de l'opt-in forge-mvc-images (table media)
  dans mvc/migrations/, sans exécuter de SQL.

Effets (write-if-new — aucun fichier existant n'est écrasé) :
  - copie la migration embarquée du paquet vers mvc/migrations/.

Prérequis:
  - forge-mvc-images installé (pip install --pre forge-mvc-images) ;
  - être à la racine d'un projet Forge (dossier mvc/).

Limites:
  - n'exécute aucun SQL et ne contacte pas MariaDB ;
  - lancer ensuite forge migration:apply pour appliquer la migration.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.""",
    "sessions:init": """\
Usage:
  forge sessions:init

Description:
  Prépare la migration SQL de l'opt-in forge-mvc-sessions-db (table
  forge_sessions) dans mvc/migrations/, sans exécuter de SQL (ADR-071).

Effets (write-if-new — aucun fichier existant n'est écrasé) :
  - copie la migration embarquée du paquet vers mvc/migrations/.

Prérequis:
  - forge-mvc-sessions-db installé (pip install --pre forge-mvc-sessions-db) ;
  - être à la racine d'un projet Forge (dossier mvc/).

Limites:
  - n'exécute aucun SQL et ne contacte pas MariaDB ;
  - lancer ensuite forge migration:apply pour appliquer la migration.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.""",
    "sessions:gc": """\
Usage:
  forge sessions:gc

Description:
  Purge les sessions expirées de la table forge_sessions (opt-in
  forge-mvc-sessions-db). À brancher sur une tâche planifiée (cron,
  systemd timer).

Effets:
  - supprime les lignes dont la date d'expiration est dépassée ;
  - affiche le nombre de sessions purgées.

Prérequis:
  - forge-mvc-sessions-db installé et table forge_sessions provisionnée ;
  - être à la racine d'un projet Forge (dossier mvc/).

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.""",
    "iot:init": """\
Usage:
  forge iot:init

Description:
  Copie la (les) migration(s) SQL Forge IoT depuis le package
  `forge-mvc-iot` (ressources packagées) vers le dossier
  `mvc/migrations/` du projet courant.

  La commande **n'applique pas** la migration : c'est `forge
  migration:apply` qui le fait, dans un second temps. Cette séparation
  permet de relire la migration avant de la jouer en base.

Comportement:
  - Si `mvc/migrations/` n'existe pas → il est créé.
  - Si la migration n'est pas encore présente → copiée.
  - Si elle est déjà présente avec un contenu identique → idempotent,
    exit 0.
  - Si elle est présente avec un contenu différent → aucun écrasement,
    `[WARN]` affiché, exit 0 (la décision reste à l'humain).

Prérequis:
  - dossier `mvc/` à la racine du dossier courant (sinon `[ERREUR]`,
    exit 1).
  - module opt-in `forge-mvc-iot` installé.

Limites:
  - aucune option à ce ticket.
  - n'exécute aucun SQL, ne se connecte à aucune base.
  - ne supprime ni ne rollback aucune migration.

Suite recommandée:
  forge iot:doctor       # vérifier que tout est prêt
  forge iot:init         # copier la migration
  forge migration:apply  # appliquer en base
  forge run              # lancer l'application
""",
    "iot:doctor": """\
Usage:
  forge iot:doctor          # diagnostic statique (sans réseau, sans base)
  forge iot:doctor --db     # + vérification de la table iot_events
  forge iot:doctor --mqtt   # + connexion brève au broker MQTT
  forge iot:doctor --db --mqtt   # les deux options sont cumulables

Description:
  Diagnostic du module opt-in `forge-mvc-iot`. Par défaut, ne se
  connecte à aucun broker MQTT et à aucune base de données — utile
  avant un starter pédagogique ou avant de brancher l'API HTTP IoT.

Vérifications statiques (toujours actives):
  - package `forge-mvc-iot` importable (et version) ;
  - configuration `load_iot_config()` chargeable, mot de passe masqué ;
  - fichier de migration `*_create_iot_events.sql` présent dans le
    package ;
  - fonction `register_iot_routes` exposée pour brancher l'API HTTP.

Vérification optionnelle (--db):
  - connexion MariaDB Forge (via core.database.db.fetch_one) +
    `SELECT COUNT(*) FROM iot_events`.
  - Résultats :
      [OK]   table accessible (N événement(s))
      [WARN] table absente → lance forge iot:init && forge migration:apply
      [FAIL] connexion MariaDB impossible (exit 1)
  - Si la table est accessible, le schéma réel est aussi comparé au
    contrat Forge IoT (colonnes, types, nullabilité, AUTO_INCREMENT)
    via INFORMATION_SCHEMA :
      [OK]   schéma iot_events — conforme
      [WARN] colonne manquante / type ou nullable inattendu (exit 0)
  - Diagnostic seulement : aucun ALTER TABLE, aucune migration auto.

Vérification optionnelle (--mqtt):
  - connexion brève au broker MQTT configuré (paho-mqtt) : ouverture
    TCP, attente du CONNACK, déconnexion. Pas d'abonnement, pas de
    publication, pas de boucle durable.
  - Résultats :
      [OK]   connexion réussie à host:port
      [FAIL] authentification refusée (exit 1)
      [FAIL] connexion impossible à host:port (exit 1)
  - Le mot de passe MQTT n'est jamais affiché. L'import `paho` reste
    paresseux : rien n'est importé tant que `--mqtt` n'est pas passé.

Code de sortie:
  0 si aucun check en erreur, 1 sinon. Les statuts `warn` et `skip`
  n'affectent pas le code de sortie.
""",
    "iot:simulate": """\
Usage:
  forge iot:simulate
  forge iot:simulate --site atelier --device esp32-001
  forge iot:simulate --kind humidity --value 55 --unit %
  forge iot:simulate --count 10 --interval 1
  forge iot:simulate --profile humidity --count 5

Description:
  Publie des mesures **factices** mais conformes au contrat MQTT Forge
  IoT vers le broker configuré (`load_iot_config()`), sans capteur
  physique. But pédagogique : tester le flux complet
  doctor --mqtt → simulate → subscriber → iot_events → /api/iot/events.

Comportement par défaut:
  - topic   : forge/atelier/esp32-001/telemetry
  - payload : {"kind": "temperature", "value": 22.4, "unit": "°C",
              "timestamp": "<UTC Z>", "metadata": {"source":
              "forge-iot-simulator"}}
  - une seule mesure publiée (QoS 0, pas de retain).

Profils (--profile):
  Fournissent des défauts prêts à l'emploi (kind/value/unit) :
  - temperature  → kind=temperature value=22.4 unit=°C
  - humidity     → kind=humidity    value=55.0 unit=%
  - presence     → kind=presence    value=1.0  unit=state (0=absence, 1=présence)
  - energy       → kind=energy      value=120.5 unit=W
  Un profil ajoute `metadata.profile`. `--kind`/`--value`/`--unit`
  surchargent encore le profil. Profil inconnu → exit 2.

Options:
  --profile <nom>    Profil pédagogique : temperature|humidity|presence|energy.
  --site <slug>      Site (défaut: atelier). Slug [a-z0-9-]+.
  --device <slug>    Identifiant capteur (défaut: esp32-001).
  --kind <slug>      Type de mesure (défaut: temperature).
  --value <nombre>   Valeur mesurée (défaut: 22.4).
  --unit <texte>     Unité (défaut: °C).
  --count <n>        Nombre de messages, borné 1..1000 (défaut: 1).
  --interval <s>     Délai entre messages, borné 0..60 s (défaut: 1).
  -h, --help         Affiche cette aide sans rien publier.

Effets:
  - se connecte brièvement au broker, publie puis se déconnecte ;
  - n'ouvre aucune connexion si une option est invalide (validation
    contre le contrat AVANT toute connexion) ;
  - le mot de passe MQTT n'est jamais affiché.

Limites (hors périmètre):
  - ne lance pas le subscriber, n'écrit pas en base, n'appelle pas
    l'API HTTP ;
  - pas de retain, pas de QoS avancé, pas de downlink ;
  - vérifie d'abord le broker avec `forge iot:doctor --mqtt`.

Code de sortie:
  0 publication réussie ; 2 option invalide ; 1 configuration invalide
  ou échec de connexion / publication.
""",
    "iot:listen": """\
Usage:
  forge iot:listen

Description:
  Écoute le broker MQTT configuré (`load_iot_config()`) et **insère** en
  base chaque mesure reçue, via `IotEventRepository`. Relie les briques
  Forge IoT en un flux local :
  Mosquitto → forge iot:listen → MqttSubscriber → iot_events.

  Commande de **développement / pédagogie**, pas un service de
  production : pas de daemon, pas de retry/backoff, pas de batch.

Comportement:
  - s'abonne au topic configuré (défaut: forge/+/+/telemetry) ;
  - pour chaque mesure valide : INSERT dans iot_events + ligne `[OK]` ;
  - reste active jusqu'à Ctrl+C, puis s'arrête proprement ;
  - s'arrête au **premier échec base** (message pédagogique).

Prérequis:
  - un broker MQTT joignable — vérifier avec `forge iot:doctor --mqtt` ;
  - la table iot_events créée — `forge iot:init` puis
    `forge migration:apply` (vérifier avec `forge iot:doctor --db`).

Options:
  -h, --help   Affiche cette aide sans rien écouter.

Limites (hors périmètre):
  - ne lance pas le simulateur (voir `forge iot:simulate`) ;
  - ne modifie pas l'API HTTP ni le contrat MQTT ;
  - pas de TLS/auth avancé, pas de service systemd.

Code de sortie:
  0 arrêt normal (Ctrl+C) ; 1 configuration invalide, connexion MQTT
  impossible, ou échec d'insertion en base.
""",
    "video:doctor": """\
Usage:
  forge video:doctor        # diagnostic statique du module vidéo

Description:
  Diagnostic du module opt-in `forge-mvc-video`. Statique : ne lance aucun
  ffmpeg, n'ouvre aucun fichier vidéo, ne touche à aucune base.

Vérifications:
  - package `forge-mvc-video` importable (et version) ;
  - configuration `load_video_config()` chargeable (FORGE_VIDEO_*) ;
  - binaire `ffprobe` présent dans le PATH (validation + métadonnées) ;
  - binaire `ffmpeg` présent dans le PATH (transcodage MP4) ;
  - fonction `register_video_routes` exposée pour brancher les routes.

Code de sortie:
  0 si tout est OK ; 1 si une vérification échoue (ex. ffmpeg/ffprobe
  absent du PATH — requis pour le transcodage).
""",
    "audio:doctor": """\
Usage:
  forge audio:doctor        # diagnostic statique du module audio

Description:
  Diagnostic du module opt-in `forge-mvc-audio`. Statique : ne lance aucun
  ffmpeg, n'ouvre aucun fichier audio, ne touche à aucune base (il n'y en a pas).

Vérifications:
  - package `forge-mvc-audio` importable (et version) ;
  - configuration `load_audio_config()` chargeable (FORGE_AUDIO_*) ;
  - binaire `ffprobe` présent dans le PATH (validation + métadonnées) ;
  - binaire `ffmpeg` présent dans le PATH (transcodage MP3) ;
  - fonction `register_audio_routes` exposée pour brancher les routes.

Code de sortie:
  0 si tout est OK ; 1 si une vérification échoue (ex. ffmpeg/ffprobe
  absent du PATH — requis pour le sondage et le transcodage).
""",
    "admin:init": """\
Usage:
  forge admin:init          # prépare la structure mvc/admin/ du back-office

Description:
  Crée la structure du back-office Forge Admin dans le projet courant
  (module opt-in `forge-mvc-admin`). Génère `mvc/admin/__init__.py` et
  `mvc/admin/resources.py`, où l'application déclare ses ressources
  administrables.

Comportement:
  - write-if-new : un fichier absent est créé ;
  - un fichier déjà présent à l'identique n'est pas réécrit (idempotent) ;
  - un fichier présent au contenu différent n'est jamais écrasé (WARN) ;
  - aucune vue ni template générés à ce stade du châssis.

Prérequis:
  - être à la racine d'un projet Forge (dossier `mvc/` attendu).

Code de sortie:
  0 si la structure est prête ; 1 si `mvc/` est absent (pas un projet Forge).
""",
    "admin:doctor": """\
Usage:
  forge admin:doctor        # rapproche les ressources admin des contrats d'entité

Description:
  Diagnostic du back-office Forge Admin (module opt-in `forge-mvc-admin`).
  Lecture seule : importe `mvc/admin/resources.py` pour lire les ressources
  déclarées, lit les contrats `mvc/entities/*/*.json`, et signale les écarts
  (entité introuvable, table ou colonnes divergentes). Aucune connexion base.

Comportement:
  - `fail` seulement si `mvc/admin/resources.py` ne charge pas (déclaration cassée) ;
  - tout écart avec un contrat est un `warn` (le contrat peut être en retard sur
    la base, et l'admin interroge la table directement) ;
  - `skip` si `mvc/admin/resources.py` est absent (lance `forge admin:init`).

Code de sortie:
  0 si aucun `fail` ; 1 sinon.
""",
    "agents:init": """\
Usage:
  forge agents:init            # crée la guidance agent (write-if-new)
  forge agents:init --check    # diagnostic en lecture seule
  forge agents:init --force    # rafraîchit CLAUDE.md et AGENTS.md
  forge agents:init --settings # ajoute aussi .claude/settings.json

Description:
  Génère la couche de guidance agent IA d'une application Forge (ADR-047) :
  `CLAUDE.md` et `AGENTS.md` (briefing distillé : conventions, générateurs CLI,
  discipline ADR, validations) et l'ADR d'amorçage `docs/adr/001-adopter-forge.md`.

Comportement:
  - par défaut : write-if-new (un fichier existant n'est jamais écrasé) ;
  - `--force` : réécrit `CLAUDE.md` et `AGENTS.md` depuis la version installée,
    sans toucher l'ADR-001 (il appartient au projet) ;
  - `--check` : signale les fichiers absents ou un briefing divergé ;
  - `--settings` : écrit aussi `.claude/settings.json` (commandes pré-autorisées) ;
    opt-in, non généré par `forge new`.

Code de sortie:
  0 si tout est en place / à jour ; 1 si `--check` trouve un manque ou un écart.
""",
    "video:init": """\
Usage:
  forge video:init          # copie la migration vidéo vers mvc/migrations/

Description:
  Copie la migration SQL packagée (`*_create_videos.sql`) du module
  `forge-mvc-video` vers `mvc/migrations/` du projet. N'exécute aucun SQL,
  ne touche à aucune base : prépare seulement le fichier.

Comportement:
  - idempotent : une migration déjà copiée à l'identique est laissée telle quelle ;
  - jamais d'écrasement silencieux : un fichier existant qui diffère → WARN,
    aucune modification ;
  - suggère ensuite `forge migration:apply` pour créer la table `videos`.

Code de sortie:
  0 succès (y compris idempotent) ; 1 si le dossier `mvc/` est absent
  (pas un projet Forge).
""",
    "video:upload": """\
Usage:
  forge video:upload <fichier> [--title "Titre"]

Description:
  Entrée d'upload officielle : valide (taille, extension), stocke la source à
  un emplacement uuid-based et insère une ligne `videos` au statut `uploaded`.
  N'exécute aucun ffmpeg — relancer `forge video:process <id>` ensuite.

Options:
  --title "..."   Titre de la vidéo (optionnel).

Code de sortie:
  0 si l'upload réussit ; 1 si l'upload est refusé (taille, extension, vide) ;
  2 en cas d'usage invalide (fichier manquant ou introuvable).
""",
    "video:process": """\
Usage:
  forge video:process <id>        # traite une vidéo
  forge video:process --pending   # traite toutes les vidéos `uploaded`

Description:
  Worker de traitement : sonde la source (ffprobe), génère un poster et
  transcode en MP4 H.264/AAC (ffmpeg), puis passe la vidéo en `ready`. Le
  travail lourd se fait ici, jamais pendant une requête HTTP.

Comportement:
  - ffmpeg/ffprobe requis (vérifier avec `forge video:doctor`) ;
  - une vidéo dont le traitement échoue passe en `failed` (avec message),
    sans interrompre les autres en mode `--pending` ;
  - les sorties partielles d'un échec sont nettoyées.

Code de sortie:
  0 si tout est traité ; 1 si au moins une vidéo a échoué ou est introuvable ;
  2 en cas d'usage invalide (id manquant ou non numérique).
""",
    "video:cleanup": """\
Usage:
  forge video:cleanup --failed [--apply]
  forge video:cleanup --orphan-files [--apply]

Description:
  Purge sûre du module vidéo. **dry-run par défaut** : liste ce qui SERAIT
  supprimé sans rien toucher ; `--apply` exécute réellement.

Options:
  --failed         Supprime les vidéos en statut `failed` (ligne DB + fichiers
                   original/mp4/poster).
  --orphan-files   Supprime les fichiers du stockage non référencés en base.
  --apply          Exécute les suppressions (sinon dry-run).

Sécurité:
  - aucune suppression hors de `storage_root` (anti-traversal) ;
  - au moins une cible (`--failed` ou `--orphan-files`) est requise.

Code de sortie:
  0 (dry-run ou apply réussi) ; 2 si aucune cible n'est fournie.
""",
    "opt-in:install": """\
Usage:
  forge opt-in:install <name>          # affiche la commande d'installation

Description:
  Affiche la commande d'installation du **package** d'un opt-in officiel
  (`pip install --pre forge-mvc-<name>`, ou `pipx inject forge-mvc …` si
  Forge tourne depuis pipx). La commande **n'exécute rien** : la présence
  du package reste un geste explicite de l'utilisateur (ADR-016).

  Opt-ins officiels : admin, audio, audit, deploy, entities, files, fixtures,
  i18n, images, import-export, iot, jobs, mail, mfa, notifications, qrcode,
  rbac, sessions-db, settings, stats, video, workflow.

  Une fois le package présent, brancher l'opt-in avec :
  `forge opt-in:enable <name>`.

Code de sortie:
  0 succès (commande affichée) ; 2 opt-in inconnu ou nom manquant.
""",
    "opt-in:enable": """\
Usage:
  forge opt-in:enable <name>           # dry-run (n'écrit rien)
  forge opt-in:enable iot --apply      # crée réellement optins/iot/

Description:
  Nom canonique du branchement d'un opt-in (ADR-016). Branche un opt-in
  **localement** dans le projet courant en créant la couche `optins/`
  (registre explicite + dossier de l'opt-in). Le branchement reste
  explicite : `mvc/routes/__init__.py` appelle `register_optins(router)` →
  `optins/registry.py` → `optins/<name>/routes.py`. Aucune découverte
  automatique.

  Le package de l'opt-in doit être présent : voir `forge opt-in:install`.

Comportement:
  - **dry-run par défaut** : sans `--apply`, affiche ce qui serait créé ;
  - `--apply` : crée les fichiers absents ; idempotent.

Code de sortie:
  0 succès ; 2 opt-in inconnu ou nom manquant ; 1 package absent ou conflit.
""",
    "opt-in:list": """\
Usage:
  forge opt-in:list

Description:
  Nom canonique de la liste des opt-ins (ADR-016). Affiche les opt-ins
  officiels et leur état local dans un projet Forge. **Commande lecture
  seule** : ne crée, ne modifie et n'installe rien.

Code de sortie:
  0 toujours (lecture seule).
""",
    "opt-in:remove": """\
Usage:
  forge opt-in:remove <name>           # affiche la commande de désinstallation

Description:
  Axe présence (−), miroir d'`opt-in:install`. Affiche la commande de
  désinstallation du **package** d'un opt-in officiel (`pip uninstall …`,
  ou `pipx uninject forge-mvc …`). **N'exécute rien.**

  Pour seulement *débrancher* l'opt-in du projet sans désinstaller le
  package, utiliser `opt-in:disable`.

Code de sortie:
  0 succès (commande affichée) ; 2 opt-in inconnu ou nom manquant.
""",
    "opt-in:disable": """\
Usage:
  forge opt-in:disable <name>          # dry-run (n'écrit rien)
  forge opt-in:disable iot --apply     # retire optins/iot/ et débranche

Description:
  Axe activation (−), inverse exact d'`opt-in:enable`. Retire la couche de
  câblage `optins/<name>/` et débranche `register_optins(router)` de
  `mvc/routes/__init__.py`. **Laisse le package installé** (voir `opt-in:remove`).

Comportement:
  - **dry-run par défaut** : sans `--apply`, affiche ce qui serait retiré ;
  - **garde §9** : un fichier `optins/` modifié à la main est **conservé** ;
  - limité à `iot` jusqu'à l'adaptateur 3-formes (ticket 4).

Code de sortie:
  0 succès (ou déjà débranché) ; 2 opt-in non supporté ou nom manquant.
""",
    "update": """\
Usage:
  forge update [--pre] [--check] [--dry-run]

Description:
  Met à jour Forge dans l'environnement Python courant (`.venv` ou
  pipx isolé). Cible `sys.executable` pour rester dans le bon
  environnement, ne modifie aucun fichier projet, ne lance aucune
  migration.

  Cas typique : un utilisateur a créé son projet avec une ancienne
  beta de Forge et veut s'assurer qu'il utilise bien la dernière —
  `forge update --pre` met à jour `forge-mvc` dans le venv courant.

Modes:
  forge update            Lance `pip install --upgrade forge-mvc`
                          dans `sys.executable`.
  forge update --pre      Idem mais avec `--pre` (versions de
                          pré-release ; utile tant que Forge est en
                          beta).
  forge update --check    Affiche la version installée et la
                          commande qui serait lancée, sans rien
                          modifier.
  forge update --dry-run  Affiche la commande pip qui serait
                          exécutée, sans la lancer.

Options:
  --pre        Autorise les versions de pré-release.
  --check      Mode vérification, lecture seule.
  --dry-run    Affiche la commande sans l'exécuter.
  -h, --help   Affiche cette aide sans exécuter la commande.

Cas pipx:
  Si Forge a été installé via pipx (`pipx install forge-mvc`),
  `sys.executable` pointe vers `~/.local/share/pipx/venvs/forge-mvc/`.
  Dans ce cas, `forge update` n'exécute PAS pip : il affiche le bon
  `pipx upgrade forge-mvc` à lancer manuellement, car pipx isole
  chaque app et `pip install` depuis ce venv ne mettrait pas à jour
  l'install pipx globale.

Hors périmètre:
  - aucune migration projet, aucun fichier `env/*` touché ;
  - aucun fichier généré sous `mvc/` modifié ;
  - aucune mise à jour automatique du `pyproject.toml` du projet.

Après mise à jour:
  Lancez `forge doctor` pour vérifier la cohérence du projet.
""",

    "run": """\
Usage:
  forge run [--env dev|prod] [--no-reload]

Description:
  Point d'entrée officiel pour lancer Forge. Remplace l'usage direct
  de `python app.py` et `scripts/dev-server.sh`.

Comportement:
  - APP_ENV=dev  : superviseur d'autoreload (défaut).
                   Spawne `python app.py` en sous-processus, surveille
                   les fichiers du projet via stat() et redémarre
                   automatiquement quand un fichier surveillé change.
                   Avec --no-reload : délègue à scripts/dev-server.sh
                   (POSIX) ; fallback `python app.py`.
  - APP_ENV=prod : refuse le serveur intégré et affiche la stratégie
                   WSGI recommandée (Gunicorn + reverse proxy).

Fichiers surveillés (dev, autoreload):
  - app.py, config.py, env/dev ;
  - mvc/**/*.{py,html,json,sql} ;
  - core/**/*.py.

Dossiers ignorés:
  .venv/, __pycache__/, .pytest_cache/, .ruff_cache/, .mypy_cache/,
  storage/, logs/, site/, node_modules/, .git/, build/, dist/.

Options:
  --env dev|prod   Force l'environnement (sinon lit APP_ENV, défaut: dev).
  --no-reload      Désactive l'autoreload (mode legacy : dev-server.sh).
  -h, --help       Affiche cette aide sans exécuter la commande.

Prérequis:
  - lancé depuis la racine d'un projet Forge (app.py + mvc/) ;
  - en dev : env/dev configuré ; certificats SSL générés (forge new).

Limites:
  - autoreload par polling stat() (pas d'inotify) ;
  - pas de live reload navigateur ni de WebSocket ;
  - ne lance pas Gunicorn automatiquement en prod ;
  - aucun changement du routeur ni du chemin WSGI.""",

    "db:config": """\
Usage:
  forge db:config [--remove]

Description:
  Amorce les variables d'environnement du backend BDD installé dans les trois
  fichiers d'environnement du projet : env/example, env/dev et env/prod
  (ADR-064). Le backend est découvert par son entry point (ADR-054).
  Avec --remove, fait l'inverse : retire ces variables (à la désinstallation).

Effets:
  - ajoute les clés manquantes de l'env_template du backend (write-if-missing) ;
  - n'écrase jamais une valeur déjà renseignée ;
  - n'écrit aucun secret : uniquement des exemples (hôte, port) ou du vide ;
  - annonce les clés ajoutées et celles restant à renseigner.

Option --remove:
  - retire des trois fichiers les clés de l'env_template du backend ;
  - ne touche qu'à ces clés, jamais d'autres DB_* ;
  - annonce les clés retirées et prévient des valeurs renseignées perdues ;
  - à lancer avant `pip uninstall forge-mvc-<sgbd>`.

Prérequis:
  - un backend BDD installé (pip install forge-mvc-<sgbd>) ;
  - les fichiers env/example, env/dev, env/prod (créés par forge new).

Limites:
  - ne renseigne pas les valeurs (secrets) : à faire à la main dans env/dev
    et env/prod ;
  - ne provisionne pas la base : voir forge db:init.""",

    "db:init": """\
Usage:
  forge db:init [--run]

Description:
  Prépare la base de données MariaDB du projet (base + deux comptes). Par défaut,
  GÉNÈRE et affiche le SQL de provisioning dérivé de env/, à exécuter dans une
  session d'administration (ex. sudo mariadb). Forge ne demande jamais le root du
  serveur (ADR-067).

Effets par défaut (mode affiche):
  - lit env/dev (DB_NAME, DB_HOST, DB_ADMIN_*, DB_APP_*) ;
  - affiche un script SQL : CREATE DATABASE, deux comptes CREATE OR REPLACE USER
    scellés à DB_NAME (admin = DDL du schéma, applicatif = DML), FLUSH PRIVILEGES ;
  - ne se connecte pas et n'exécute rien.

Avec --run (mode exécution):
  - exécute directement le provisioning ; suppose que DB_ADMIN_* a les droits
    serveur (CREATE DATABASE, CREATE USER, GRANT). Destiné à la CI, aux conteneurs
    et aux serveurs auto-gérés.

Vérification préalable (dans les deux modes):
  - s'arrête si DB_NAME, DB_ADMIN_LOGIN, DB_ADMIN_PWD, DB_APP_LOGIN ou DB_APP_PWD
    sont absents ou vides (amorcez-les avec forge db:config) ;
  - s'arrête si DB_NAME n'est pas un nom de base valide.

Prérequis:
  - un serveur MariaDB joignable ;
  - env/dev renseigné.

Options:
  --run         Exécute le provisioning au lieu d'afficher le SQL.
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
  - lit cli/schemas/forge.schema.index.json (registre des schémas) ;
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
  - lit cli/schemas/forge.schema.index.json ;
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
  (forge_mvc_rbac/schemas/rbac.schema.json, JSON Schema Draft 2020-12).

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
  - insère la route GET /<slug> dans mvc/routes/__init__.py (public, sans CSRF) ;
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
  - insère la route GET /<plural> dans mvc/routes/__init__.py.

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
  - insère la route GET /<plural>/<id> dans mvc/routes/__init__.py.

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
  - insère les routes GET et POST /<plural>/form dans mvc/routes/__init__.py.

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
    mvc/routes/__init__.py.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - route /contact figée (non paramétrable) ;
  - aucun envoi de mail n'est branché par défaut — la soumission est à
    raccorder dans le contrôleur (voir forge mail:test pour tester
    l'envoi).""",

    # ── Mail (CLI-HELP-FLAGS-MAIL-001) ───────────────────────────────────────
    # mail:init est déjà couvert par CLI-HELP-FLAGS-INIT-COMMANDS-001.
    # Ce groupe traite les 4 commandes mail restantes.

    "mail:test": """\
Usage:
  forge mail:test --to <adresse>

Description:
  Construit et expédie un message de test via le transport mail configuré
  pour le projet (smtp, log ou null).

Arguments:
  --to <adresse>    Destinataire du mail de test (obligatoire).

Effets:
  - charge env/dev puis instancie MailConfig depuis les variables MAIL_* ;
  - construit le transport correspondant à MAIL_TRANSPORT (smtp|log|null) ;
  - prépare un MailMessage daté avec corps texte et HTML ;
  - délègue à forge_mvc_mail.mailer.Mailer.send().

Selon la configuration:
  - MAIL_ENABLED=false ou transport null  → AUCUN envoi réel
    (la commande l'indique explicitement) ;
  - MAIL_TRANSPORT=log                    → écriture sous storage/mail/,
                                            aucun envoi réseau ;
  - MAIL_TRANSPORT=smtp + MAIL_ENABLED=true → ENVOI RÉEL via SMTP.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - peut envoyer un mail réel selon la config (vérifier au préalable
    avec forge mail:doctor) ;
  - ne valide pas le contenu envoyé, ne consulte pas mail_log
    (voir forge mail:logs) ;
  - ne crée ni template ni dossier (voir forge mail:init).""",

    "mail:render": """\
Usage:
  forge mail:render <template> [--context fichier.json]

Description:
  Affiche le rendu d'un template mail Forge (sujet, corps texte et HTML)
  sans envoyer ni journaliser quoi que ce soit.

Arguments:
  <template>              Nom du template à rendre (sans extension).
  --context fichier.json  Optionnel — chemin vers un JSON fournissant le
                          contexte de rendu Jinja2.

Effets:
  - charge env/dev puis lit le template dans mail_templates_dir
    (par défaut mvc/mail/templates) ;
  - applique le contexte JSON s'il est fourni ;
  - instancie forge_mvc_mail.templates.MailTemplateRenderer ;
  - affiche le rendu encadré : Template, Sujet, corps texte, corps HTML ;
  - n'envoie aucun mail, ne touche ni storage/mail/ ni mail_log.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - ne crée pas de template (voir forge mail:init pour les exemples) ;
  - échoue si le template ou le fichier de contexte est introuvable
    ou JSON invalide ;
  - ne valide pas la configuration SMTP (voir forge mail:doctor).""",

    "mail:doctor": """\
Usage:
  forge mail:doctor

Description:
  Diagnostique la configuration mail du projet : variables
  d'environnement, transport, dossiers et journalisation.

Effets:
  - charge env/dev et reconstruit MailConfig depuis les variables MAIL_* ;
  - vérifie MAIL_ENABLED, MAIL_TRANSPORT (smtp|log|null), MAIL_FROM,
    dossier mvc/mail/templates et stockage storage/mail/ ;
  - pour MAIL_TRANSPORT=smtp : vérifie aussi MAIL_HOST et MAIL_PORT ;
  - vérifie MAIL_LOG_ENABLED ;
  - peut créer storage/mail/ s'il est absent (mkdir best-effort) ;
  - imprime un tableau de checks avec un compte d'avertissements et
    d'erreurs ; exit 1 s'il existe au moins une erreur.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - n'envoie aucun mail (utiliser forge mail:test pour cela) ;
  - ne consulte pas la table mail_log (voir forge mail:logs) ;
  - ne corrige rien — les warnings/erreurs sont à traiter manuellement
    dans env/dev.""",

    "mail:logs": """\
Usage:
  forge mail:logs [--limit N]

Description:
  Affiche les N derniers enregistrements de la table mail_log (par
  défaut 20). Lecture seule.

Arguments:
  --limit N    Nombre maximum d'enregistrements à afficher (défaut 20).

Effets:
  - charge env/dev ;
  - vérifie MAIL_LOG_ENABLED (sinon avertit et sort) ;
  - lit la table mail_log via forge_mvc_mail.log.MailLogger.fetch_recent(N) ;
  - imprime un tableau ID / DATE / STATUS / TRANSPORT / TO / SUJET ;
  - n'écrit, ne modifie et ne purge rien.

Prérequis:
  - MAIL_LOG_ENABLED=true dans env/dev ;
  - table mail_log présente (créée par forge db:apply après
    forge mail:init).

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - lecture seule — ne supprime pas et ne tronque pas mail_log ;
  - ne déclenche aucun envoi ;
  - --limit doit être un entier positif.""",

    # ── Migrations (CLI-HELP-FLAGS-MIGRATIONS-001) ───────────────────────────
    # migration:make est déjà couvert par une aide native (--help détaillé
    # dans forge_mvc_entities/migrations.py:458-487), hors périmètre de
    # ce ticket.

    "migration:status": """\
Usage:
  forge migration:status

Description:
  Affiche le statut des migrations SQL Forge en comparant les fichiers
  locaux du dossier mvc/migrations/ et la table de suivi
  forge_migrations en base.

Effets:
  - lit les fichiers de migration mvc/migrations/<version>_<slug>.sql ;
  - se connecte à la base configurée (env/dev → DB_APP_*) et lit
    SELECT version, name, filename, checksum FROM forge_migrations ;
  - calcule un statut par version :
      APPLIED  — fichier local + ligne en base, checksums identiques ;
      CHANGED  — fichier local + ligne en base, checksum différent ;
      PENDING  — fichier local sans ligne en base ;
      MISSING  — ligne en base sans fichier local correspondant ;
  - imprime un tableau version / statut / fichier ;
  - n'exécute AUCUN SQL de migration, n'écrit nulle part.

Prérequis:
  - mvc/migrations/ peut être absent (la commande l'indique) ;
  - table forge_migrations créée par forge db:init.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - lecture seule — n'applique aucune migration (voir migration:apply) ;
  - ne crée pas de fichier (voir migration:make) ;
  - ne compare pas le schéma SQL avec les entités (voir migration:diff).""",

    "migration:apply": """\
Usage:
  forge migration:apply [--dry-run]

Description:
  Applique sur la base configurée toutes les migrations SQL en statut
  PENDING, dans l'ordre de leur version (timestamp).

Effets:
  - lit mvc/migrations/ et la table forge_migrations ;
  - calcule le statut comme migration:status ;
  - refuse de continuer si une migration est en statut CHANGED ou
    MISSING (intégrité) ;
  - pour chaque migration PENDING (ordre version croissante) :
      ouvre une transaction, exécute chaque instruction SQL du fichier,
      insère une ligne dans forge_migrations (version, nom, checksum,
      date, durée), commit ;
  - imprime chaque fichier appliqué puis le total final.

ATTENTION:
  - cette commande MODIFIE RÉELLEMENT la base de données configurée
    dans env/dev (ou env/prod selon APP_ENV) ;
  - les instructions SQL des migrations sont exécutées telles quelles
    (CREATE TABLE, ALTER TABLE, INSERT, etc.) ;
  - vérifier l'état avec forge migration:status AVANT d'appliquer ;
  - en cas d'erreur SQL, la migration en cours est annulée mais les
    migrations déjà appliquées sont conservées.

Prérequis:
  - DB_APP_* configurés dans env/dev ;
  - table forge_migrations créée (forge db:init) ;
  - mvc/migrations/ contenant au moins un fichier PENDING.

Options:
  --dry-run     Liste les migrations PENDING et imprime leur SQL SANS rien
                appliquer ni écrire en base ; relancer sans --dry-run pour
                appliquer réellement.
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - ne crée pas de fichier (voir migration:make) ;
  - ne propose pas de rollback (annulation manuelle via SQL inverse) ;
  - différent de forge db:apply qui exécute le SQL des entités sans
    suivi de version.""",

    "migration:diff": """\
Usage:
  forge migration:diff --entity <Entite>

Description:
  Compare le schéma JSON d'une entité Forge à l'état réel de sa table
  en base, et imprime un rapport de différences (colonnes manquantes,
  types divergents, nullable/auto_increment, défauts).

Arguments:
  --entity <Entite>    Nom de l'entité à comparer (obligatoire).

Effets:
  - charge env/dev et se connecte à la base ;
  - lit mvc/entities/<Entite>/<entite>.json pour les colonnes attendues ;
  - lit INFORMATION_SCHEMA.COLUMNS pour les colonnes réelles ;
  - calcule le diff ligne à ligne (manquantes, supplémentaires,
    divergentes) ;
  - imprime un rapport humain ;
  - ne génère AUCUN fichier SQL et ne modifie ni la base ni les
    fichiers d'entité.

Prérequis:
  - DB_APP_* configurés dans env/dev ;
  - l'entité <Entite> existe (forge make:entity) ;
  - la table correspondante existe en base.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - lecture seule, aucun effet sur la base ni sur les fichiers ;
  - ne génère pas de migration prête à appliquer — utiliser
    forge migration:make <nom> --from-diff <Entite> pour produire un
    fichier .sql à partir du diff.""",

    # ── Diagnostic projet (CLI-HELP-FLAGS-PROJECT-DIAGNOSTICS-001) ───────────
    # 4 commandes lecture seule destinées à comprendre l'état d'un projet
    # Forge sans rien modifier.

    "doctor": """\
Usage:
  forge doctor

Description:
  Diagnostic large et tolérant d'un projet Forge. Inspecte
  l'environnement Python, la configuration, l'arborescence et les
  dépendances optionnelles. Ne modifie rien.

Effets (12 contrôles, lecture seule) :
  - Python : version >= 3.12 ;
  - env/example + env/dev : variables fusionnées valides ;
  - structure mvc/ : dossiers et fichiers attendus ;
  - entités mvc/entities/*.json : présence et lisibilité ;
  - migrations mvc/migrations/ : présence ;
  - i18n translations/ : présence ;
  - templates mvc/views/ : présence ;
  - modules : registre projet ;
  - dépendance MFA (forge_mvc_mfa / pyotp) si indices détectés ;
  - SSL : certificats cert.pem / key.pem si HTTPS activé ;
  - Node : npm disponible pour build:css ;
  - base de données : DB_APP_* renseignés, MariaDB joignable.

Comportement:
  - chaque contrôle remonte un état (ok / warn / fail / skip) ;
  - tolérant : un projet incomplet remonte des warnings sans bloquer ;
  - exit 1 uniquement si au moins un contrôle est fail.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - ne corrige rien — les warnings sont à traiter manuellement ;
  - pour un contrôle strict CI, voir forge project:check ;
  - pour un rapport détaillé multi-familles, voir forge project:audit ;
  - ne lance ni la suite de tests ni les migrations.""",

    "project:check": """\
Usage:
  forge project:check

Description:
  Contrôle strict des conventions Forge d'un projet, conçu pour la CI.
  Plus restrictif que doctor : se concentre sur la structure et les
  conventions, sans dépendances réseau ni base.

Effets (7 contrôles structurels, lecture seule) :
  - structure de projet (app.py, mvc/, config.py) ;
  - config.py et variables d'environnement essentielles ;
  - entités mvc/entities/ (format, nommage) ;
  - routes mvc/routes/__init__.py (déclaration cohérente) ;
  - templates mvc/views/ (arborescence attendue) ;
  - modules (registre, cohérence) ;
  - migrations mvc/migrations/ (nommage et intégrité).

Comportement:
  - chaque contrôle remonte un état ok / warn / fail ;
  - exit 1 dès qu'au moins un contrôle est fail ;
  - exit 0 sinon (avec ou sans avertissements).

Prérequis:
  - être à la racine d'un projet Forge (app.py + mvc/) ; sinon la
    commande échoue avec un message explicite.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - ne modifie aucun fichier ;
  - ne remplace pas une suite de tests pytest ;
  - ne fait pas d'appel réseau (utiliser forge doctor pour vérifier
    aussi MariaDB / Node / SSL) ;
  - pour un rapport détaillé multi-familles, voir forge project:audit.""",

    "project:audit": """\
Usage:
  forge project:audit

Description:
  Rapport d'audit détaillé non destructif d'un projet Forge. Plus
  profond que project:check : produit plusieurs résultats par famille
  pour offrir une vue exhaustive.

Effets (9 familles d'audit, lecture seule) :
  - structure (arborescence, fichiers attendus) ;
  - config (config.py, env/*, variables) ;
  - entités (mvc/entities/, cohérence multi-fichiers) ;
  - routes (mvc/routes/__init__.py, conventions) ;
  - templates (mvc/views/, présence des layouts) ;
  - modules (registre, fichiers, routes injectées) ;
  - migrations (nommage, séquence, intégrité) ;
  - documentation (présence et cohérence des fichiers .md) ;
  - tests (présence et structure du dossier tests/).

Comportement:
  - chaque famille produit une LISTE de résultats (ok / warn / fail
    / info) ;
  - le rapport groupe les résultats par famille puis affiche un
    résumé par statut ;
  - exit 1 dès qu'au moins un résultat est fail.

Prérequis:
  - être à la racine d'un projet Forge (app.py + mvc/).

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - ne modifie aucun fichier ;
  - ne contacte pas la base de données (voir forge doctor) ;
  - ne lance pas la suite de tests ;
  - pour un contrôle court CI, voir forge project:check.""",

    "routes:list": """\
Usage:
  forge routes:list

Description:
  Affiche les routes déclarées par l'application Forge, dans l'ordre
  d'enregistrement, sous forme de tableau.

Effets:
  - lit APP_ROUTES_MODULE depuis config.py (par défaut mvc.routes) ;
  - importe le module et récupère son router ;
  - itère router.iter_routes() ;
  - imprime un tableau à 7 colonnes :
      METHOD   méthode HTTP (ou liste)
      PATH     motif de route (pattern)
      NAME     nom logique de la route (ou « - »)
      PUBLIC   oui / non — accessible sans authentification
      CSRF     oui / non — protection CSRF requise
      API      oui / non — route déclarée comme API
      HANDLER  qualname du handler ;
  - signale si le router est vide ;
  - n'écrit, ne modifie et ne purge rien.

Prérequis:
  - être à la racine d'un projet Forge (app.py + config.py) ;
  - APP_ROUTES_MODULE importable.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - lecture seule ;
  - n'exécute aucune route ;
  - ne valide pas les handlers (utiliser forge project:check pour la
    cohérence des routes).""",

    # ── Cycle entité / modèle / CRUD (CLI-HELP-FLAGS-ENTITY-MODEL-CRUD-001) ──
    # JSON canonique → validation → modèle → contrôle → CRUD → pivot CRUD.
    # 5 commandes cœur génératif de Forge.

    "entity:validate": """\
Usage:
  forge entity:validate [--json]

Description:
  Valide les contrats JSON canoniques des entités et des relations Forge
  contre les schémas Draft 2020-12, puis applique la validation
  sémantique propre à Forge (types reconnus, références croisées, etc.).
  Lecture seule.

Effets:
  - parcourt mvc/entities/*/*.json (un dossier par entité) ;
  - lit aussi mvc/entities/relations.json s'il existe ;
  - applique le schéma entity.schema.json sur chaque définition
    d'entité ;
  - applique le schéma relations.schema.json sur le contrat de
    relations ;
  - applique ensuite une validation sémantique (types SQL valides,
    références entre entités, cohérence pivots) ;
  - imprime un rapport humain ou JSON ;
  - ne modifie aucun fichier, ne touche pas à la base.

Options:
  --json        Sortie machine JSON (valid, errors_count, warnings_count,
                liste detaillée des erreurs et avertissements).
  -h, --help    Affiche cette aide sans exécuter la commande.

Prérequis:
  - être à la racine d'un projet Forge (mvc/entities/ existe) ;
  - jsonschema installé (déjà dans requirements.txt).

Codes de retour:
  0  aucun problème détecté
  1  au moins une erreur (schéma ou sémantique) OU mvc/entities/ absent
     OU jsonschema/schemas Forge indisponibles

Limites:
  - lecture seule — voir forge build:model pour régénérer les
    artefacts Python/SQL ;
  - ne valide pas le schéma JSON Forge lui-même (voir forge
    schema:doctor).""",

    "entity:doc": """\
Usage:
  forge entity:doc [--output <fichier>]

Description:
  Produit une vue globale des entités et de leurs relations à partir des
  contrats du projet (mvc/entities/*.json et relations.json), en Markdown :
  un tableau par entité, la liste des relations avec leur cardinalité, et
  un diagramme Mermaid erDiagram. Aucun backend BDD ni connexion requis.

Effets:
  - lit mvc/entities/*/*.json et mvc/entities/relations.json ;
  - par défaut, AFFICHE le Markdown sur stdout (rien n'est écrit) ;
  - avec --output, écrit le résultat dans le fichier indiqué
    (écrasement annoncé si le fichier existait).

Options:
  --output <f>  Écrit la doc dans <f> au lieu de l'afficher.
  -h, --help    Affiche cette aide sans exécuter la commande.

Prérequis:
  - être à la racine d'un projet Forge (mvc/entities/ existe).

Codes de retour:
  0  documentation produite
  1  mvc/entities/ absent, contrat invalide, ou --output sans chemin

Limites:
  - documente les contrats DÉCLARÉS, pas la base réelle (pas
    d'introspection) ;
  - lecture seule des contrats ; n'écrit que le fichier de --output.""",

    "build:model": """\
Usage:
  forge build:model [--dry-run]

Description:
  Régénère les artefacts Python et SQL de toutes les entités du projet
  à partir de leurs contrats JSON canoniques.

Effets (un projet PEUT être modifié) :
  - exécute d'abord la validation des contrats (équivalent
    entity:validate) ; refuse de continuer si une entité est invalide ;
  - pour chaque entité de mvc/entities/<E>/ :
      * RÉGÉNÈRE <e>.sql (DDL canonique de la table) ;
      * RÉGÉNÈRE <e>_base.py (classe modèle régénérable) ;
      * crée <e>.py (modèle manuel) si absent — write-if-new ;
      * crée __init__.py si absent — write-if-new ;
  - RÉGÉNÈRE mvc/entities/relations.sql à partir de relations.json ;
  - imprime la liste des fichiers régénérés / créés / préservés ;
  - --dry-run : calcule tout sans écrire.

ATTENTION:
  - cette commande ÉCRASE <e>.sql et <e>_base.py à chaque exécution
    (ces fichiers sont régénérables par convention Forge) ;
  - <e>.py et __init__.py sont PRÉSERVÉS s'ils existent déjà
    (code utilisateur protégé) ;
  - vérifier le diff Git après exécution ;
  - utiliser --dry-run pour prévisualiser avant écriture.

Options:
  --dry-run     Affiche les fichiers qui seraient écrits sans rien
                modifier.
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - ne génère pas le CRUD (contrôleurs, formulaires, vues) — voir
    forge make:crud ;
  - ne crée ni la base ni les tables (voir forge db:init / db:apply) ;
  - ne génère pas de migration SQL (voir forge migration:make).""",

    "check:model": """\
Usage:
  forge check:model

Description:
  Valide la cohérence des modèles Forge et imprime un aperçu détaillé
  par entité, sans rien écrire. Identique à la validation effectuée par
  build:model mais SANS la phase de génération.

Effets (lecture seule) :
  - parcourt mvc/entities/ et applique la validation contractuelle
    (JSON Schema + sémantique) ;
  - calcule pour chaque entité la liste des champs (nom, colonne,
    sql_type, python_type, nullable, PK, AI, unique, contraintes) ;
  - imprime un tableau par entité avec ses champs et les fichiers
    cibles (<e>.sql, <e>_base.py, <e>.py, __init__.py) ;
  - n'écrit aucun fichier, ne touche pas à la base.

Différence avec build:model:
  - build:model VALIDE puis GÉNÈRE ;
  - check:model VALIDE puis AFFICHE l'aperçu sans générer.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Codes de retour:
  0  modèles valides
  1  au moins une entité invalide

Limites:
  - ne corrige rien — voir forge entity:validate pour un rapport
    purement contractuel ;
  - n'écrit jamais (utiliser forge build:model pour générer).""",

    "make:crud": """\
Usage:
  forge make:crud <Entite> [--dry-run]

Description:
  Génère le scaffolding CRUD complet pour une entité existante :
  contrôleur, modèle applicatif, formulaire, layout, vues
  (index, fiche, formulaire, suppression en masse).

Effets (un projet PEUT être modifié) :
  - applique d'abord la validation des contrats (équivalent
    entity:validate) ; refuse de continuer si invalide ;
  - lit mvc/entities/<entite>/<entite>.json (refuse le legacy
    format_version: 1 — schema_version: "1.0" requis) ;
  - écrit en mode write-if-new (aucun fichier existant n'est écrasé) :
      * mvc/controllers/<entite>_controller.py ;
      * mvc/models/<entite>_model.py ;
      * mvc/forms/__init__.py et mvc/forms/<entite>_form.py ;
      * mvc/views/layouts/app.html ;
      * mvc/views/partials/form_errors.html ;
      * mvc/views/<entite>/index.html, _table.html, _pagination.html,
        _results.html, show.html, form.html,
        bulk_delete_confirm.html ;
  - imprime le bloc de routes à insérer manuellement dans
    mvc/routes/__init__.py ;
  - --dry-run : calcule tout sans écrire.

ATTENTION:
  - cette commande peut créer plusieurs fichiers d'un coup ;
  - tous les fichiers sont écrits en write-if-new : le code utilisateur
    déjà présent est PRÉSERVÉ ;
  - vérifier le diff Git après exécution ;
  - le bloc de routes affiché doit être copié manuellement dans
    mvc/routes/__init__.py (Forge n'écrit jamais silencieusement ce fichier).

Options:
  --dry-run     Affiche les fichiers qui seraient écrits sans rien
                modifier.
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - ne génère pas de pages publiques (voir forge make:public-page,
    make:public-list, make:public-show, make:public-form) ;
  - ne génère pas de logique métier personnalisée ;
  - ne traite pas les pivots avec attributs (voir forge
    make:pivot-crud) ;
  - utiliser forge entity:validate pour diagnostiquer un contrat
    invalide.""",

    "make:pivot-crud": """\
Usage:
  forge make:pivot-crud <EntiteSource> <nom_relation> [--dry-run]

Description:
  Génère un sous-CRUD dédié pour une relation many-to-many comportant
  des attributs propres (pivot.fields[]). Permet d'éditer chaque
  association du pivot via un écran spécifique.

Effets (un projet PEUT être modifié) :
  - lit mvc/entities/relations.json et résout la relation
    many_to_many entre <EntiteSource> et son partenaire ;
  - vérifie que la relation comporte un pivot.fields[] non vide ;
  - écrit en mode write-if-new (aucun fichier existant n'est écrasé) :
      * mvc/controllers/pivot/<src>_<relation>_pivot_controller.py ;
      * mvc/templates/pivot/<src>_<relation>/index.html ;
      * mvc/templates/pivot/<src>_<relation>/form.html ;
  - --dry-run : affiche la liste des fichiers qui seraient générés
    sans rien écrire.

ATTENTION:
  - cette commande peut créer plusieurs fichiers d'un coup ;
  - tous les fichiers sont écrits en write-if-new : un fichier déjà
    présent est PRÉSERVÉ ;
  - vérifier le diff Git après exécution.

Prérequis:
  - la relation <nom_relation> doit exister dans relations.json en
    type many_to_many ;
  - elle doit posséder un bloc pivot.fields[] non vide (sinon utiliser
    le CRUD standard).

Options:
  --dry-run     Affiche les fichiers qui seraient écrits sans rien
                modifier.
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - ne génère pas le CRUD principal des deux entités liées (voir
    forge make:crud) ;
  - le runtime vit dans l'opt-in forge-mvc-entities (forge_mvc_entities),
    qui a absorbé le pivot (ADR-021/070) ; installer : pip install --pre forge-mvc-entities ;
  - ne modifie pas mvc/routes/__init__.py — le routage du sous-CRUD pivot est
    à brancher manuellement.""",

    # ── Auth — commandes restantes (CLI-HELP-FLAGS-AUTH-COMPLETION-001) ──────
    # 5 commandes qui n'ont pas l'aide argparse native des auth:user:*
    # (lesquelles restent gérées par leur propre main() et ne sont pas
    # interceptées par le dispatcher).

    "auth:init": """\
Usage:
  forge auth:init

Description:
  Initialise les fichiers SQL optionnels du socle Auth/User Forge dans
  le projet. Ne touche pas la base de données.

Effets (un projet PEUT être modifié) :
  - crée mvc/models/sql/ si absent ;
  - écrit en mode write-if-new (aucun fichier existant n'est écrasé) :
      * users.sql                       — table des comptes ;
      * auth_tokens.sql                 — jetons (reset, vérification…) ;
      * auth_mfa_factors.sql            — facteurs MFA (TOTP) ;
      * auth_mfa_recovery_codes.sql     — codes de récupération MFA ;
      * user_roles.sql                  — pont Auth/User vers RBAC ;
      * auth_audit_log.sql              — journal d'audit Auth ;
      * auth_rate_limit_attempts.sql    — anti-bruteforce ;
  - affiche la commande suivante recommandée (forge db:apply).

ATTENTION:
  - cette commande peut créer plusieurs fichiers d'un coup ;
  - les fichiers existants sont PRÉSERVÉS (write-if-new) ;
  - vérifier le diff Git après exécution.

Limites:
  - ne crée AUCUNE table : utiliser forge db:apply pour exécuter le
    SQL produit ;
  - ne configure ni la session ni le hachage de mot de passe (déjà
    fournis par core.auth) ;
  - ne crée aucun utilisateur (voir forge auth:user:create) ;
  - tous les fichiers sont opt-in : MFA, RBAC, audit, rate limit
    peuvent être omis si vous ne les utilisez pas.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.""",

    "make:auth": """\
Usage:
  forge make:auth

Description:
  Scaffolde le flux de connexion sur le socle « users » (forge auth:init) :
  contrôleur d'authentification et vue de login. Affiche les routes à ajouter.

Effets (un projet PEUT être modifié) :
  - écrit en mode write-if-new (aucun fichier existant n'est écrasé) :
      * mvc/controllers/auth_controller.py : login_form, login, logout ;
      * mvc/views/app/auth/login.html      : formulaire (namespace app/, ADR-073) ;
  - génère mvc/routes/auth_routes.py (register_auth_routes) et affiche le
    branchement à ajouter dans mvc/routes/__init__.py (Forge n'y écrit pas ; ADR-068).

Flux généré:
  - login : authenticate_user (loader users) + login_user + régénération de
    session anti-fixation + réémission du cookie ;
  - logout : logout_user + suppression du cookie + redirection /login.

Prérequis:
  - forge auth:init puis forge db:apply (table users) ;
  - un compte applicatif : forge auth:user:create.

Limites:
  - v1 : ni MFA, ni rate-limit, ni audit (voir le contrôleur de référence) ;
  - n'écrit pas dans mvc/routes/__init__.py : les routes sont affichées, à coller.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.""",

    "auth:doctor": """\
Usage:
  forge auth:doctor

Description:
  Diagnostic d'importabilité du socle Auth/User Forge : modules,
  contrats publics, brique MFA et RBAC, fichiers SQL optionnels.
  Lecture seule. Ne contacte pas la base.

Effets:
  - vérifie l'importabilité de chaque module Auth :
      core.auth.user / session / tokens / reset / audit / rate_limit,
      forge_mvc_mfa (+ recovery), forge_mvc_rbac ;
  - émet un rappel MFA (Beta, installée ou pas) : secret TOTP chiffré au
    repos, FORGE_MFA_SECRET_KEY obligatoire, voir
    packages/forge-mvc-mfa/docs/reference.md ;
  - vérifie la présence des contrats publics (AuthUser, login_user,
    AuthToken, PasswordResetRequest, AuthMfaFactor,
    AuthMfaRecoveryCode, AuthUserRole, user_has_permission,
    AuthAuditEvent, AuthRateLimitAttempt…) ;
  - vérifie les contrats RBAC optionnels (Role, Permission,
    require_permission, make_can) ;
  - liste les fichiers SQL optionnels (équivalent auth:list-sql) ;
  - imprime un tableau de statuts (ok / warn / fail) + résumé ;
  - exit 1 s'il existe au moins une erreur.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - n'ouvre aucune connexion à la base ;
  - ne crée ni utilisateur ni table ;
  - pour l'état effectif (modules + SQL présents) par fonctionnalité,
    voir forge auth:status ;
  - pour la liste seule des fichiers SQL, voir forge auth:list-sql.""",

    "auth:status": """\
Usage:
  forge auth:status

Description:
  État des briques d'authentification disponibles dans le projet :
  pour chaque fonctionnalité (users, sessions, tokens, reset password,
  MFA, user_roles, Jinja helpers, audit, rate limit), indique si le
  module est importable et si le fichier SQL correspondant est
  présent. Lecture seule. Ne contacte pas la base.

Effets:
  - pour chaque fonctionnalité Auth/User Forge :
      * vérifie que le module est importable et que le contrat public
        attendu existe ;
      * si un fichier SQL est attendu, vérifie sa présence dans
        mvc/models/sql/ ;
  - imprime un tableau de statuts (ok / warn / fail) + résumé ;
  - exit 1 s'il existe au moins une erreur.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - lecture seule, pas de connexion à la base ;
  - ne crée ni fichier ni table ;
  - pour un diagnostic plus détaillé (tous les modules et contrats,
    pas seulement les fonctionnalités), voir forge auth:doctor.""",

    "auth:list-sql": """\
Usage:
  forge auth:list-sql

Description:
  Liste les fichiers SQL optionnels du socle Auth/User Forge et leur
  présence dans le projet. Aucune écriture, aucune connexion DB.

Effets:
  - pour chaque fichier attendu sous mvc/models/sql/ :
      * users.sql, auth_tokens.sql, auth_mfa_factors.sql,
        auth_mfa_recovery_codes.sql, user_roles.sql,
        auth_audit_log.sql, auth_rate_limit_attempts.sql ;
      * vérifie si le fichier est présent ;
      * statue ok si présent, warn si absent (SQL optionnel, non
        appliqué automatiquement) ;
  - imprime un résumé + rappel qu'aucun secret n'est affiché.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - n'applique AUCUN SQL — voir forge db:apply ou forge
    migration:apply pour appliquer ;
  - ne crée aucun fichier — voir forge auth:init pour les générer ;
  - ne vérifie pas l'état réel des tables en base — voir forge
    auth:doctor / auth:status.""",

    "auth:user:list": """\
Usage:
  forge auth:user:list

Description:
  Liste les comptes utilisateurs présents dans la table users du
  projet. Lecture seule sur la base configurée.

Effets:
  - charge env/dev puis configure core.forge.db_* depuis les variables
    DB_APP_* (HOST, PORT, NAME, LOGIN, PWD, POOL_SIZE) ;
  - ouvre une connexion à la base et exécute un SELECT sur users ;
  - imprime un tableau id / email / actif / created_at ;
  - signale si aucun utilisateur n'est présent ;
  - n'écrit, ne modifie et ne purge rien.

Prérequis:
  - DB_APP_* configurés dans env/dev (ou env/prod) ;
  - table users créée (forge auth:init puis forge db:apply).

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - lecture seule — n'affiche aucun mot de passe ni hash ;
  - n'affiche pas les rôles RBAC (voir forge auth:user:roles
    --email <…>) ;
  - cette commande utilise un parseur manuel ; les autres
    auth:user:* (create, show, disable, enable, password, role:add,
    role:remove, roles) reposent sur argparse et conservent leur
    aide --help native (non couverte par ce ticket).""",

    # ── Commandes restantes (CLI-HELP-FLAGS-REMAINING-MINOR-001) ─────────────
    # Clôture du chantier --help : 9 commandes hétérogènes regroupées ici.

    "new": """\
Usage:
  forge new <NomProjet> [--profile <profil>]

Description:
  Crée un nouveau projet Forge nu dans ./<NomProjet>/ à partir du
  squelette de projet embarqué : configuration env/, environnement
  virtuel Python (avec forge-mvc), dépendances Node et certificats SSL
  de développement.

Arguments:
  <NomProjet>        Nom du projet (lettres, chiffres, _ ou -, doit
                     commencer par une lettre).

Options:
  --profile <id>     Profil de projet (voir SUPPORTED_PROJECT_PROFILES).
  -h, --help         Affiche cette aide sans exécuter la commande.

Effets (CRÉE un dossier complet) :
  - refuse si ./<NomProjet>/ existe déjà ;
  - copie le squelette de projet embarqué (aucun clone, aucun réseau) ;
  - configure env/example et env/dev (APP_NAME, DB_NAME, DB_APP_LOGIN) ;
  - python -m venv .venv puis pip install -r requirements.txt
    (installe forge-mvc) ;
  - npm install + npm run build:css si package.json présent ;
  - openssl req génère cert.pem / key.pem (HTTPS local) ;
  - écrit forge_profile.txt ;
  - initialise un dépôt Git (git init + commit initial) ;
  - en cas d'erreur, supprime tout le dossier créé (rollback).

ATTENTION:
  - cette commande crée un grand nombre de fichiers en une fois ;
  - elle EXIGE git et openssl dans le PATH ;
  - elle suppose une connexion réseau (pip, npm) ;
  - le commit Git initial peut échouer si user.name/user.email Git
    ne sont pas configurés (le projet reste créé, message d'aide).

Limites:
  - ne crée AUCUNE base de données (lancer forge db:init dans le
    projet créé) ;
  - ne configure pas le déploiement (voir forge deploy:init).""",

    "skeleton:upgrade": """\
Usage:
  forge skeleton:upgrade [--check] [--bare]

Description:
  Ajoute au projet courant les fichiers du squelette Forge qui manquent, en
  write-if-new : aucun fichier existant n'est écrasé (aucune édition perdue).
  Utile quand Forge évolue et enrichit le squelette (outillage, config qualité).

Options:
  --check       Liste les fichiers qui seraient ajoutés, sans rien écrire.
  --bare        Ignore l'apparat qualité (comme forge new --bare, ADR-063).
  -h, --help    Affiche cette aide sans exécuter la commande.

Effets (un projet PEUT être modifié) :
  - copie uniquement les fichiers du squelette absents du projet ;
  - ne modifie ni ne supprime jamais un fichier existant ;
  - les fichiers substitués à la création (env/*) préexistent et sont préservés.

Limites:
  - n'échoue pas hors d'un projet Forge : il s'arrête proprement ;
  - ne met pas à jour le contenu d'un fichier déjà présent (write-if-new strict) ;
  - ne re-télécharge pas forge-mvc (un pin git inchangé exige pip --force-reinstall).""",

    "sync:entity": """\
Usage:
  forge sync:entity <NomEntite>

Description:
  Régénère les artefacts d'une SEULE entité depuis son JSON canonique.
  Sous-ensemble de forge build:model ciblé sur une entité.

Arguments:
  <NomEntite>    Nom de l'entité (PascalCase) ; le dossier
                 mvc/entities/<entite>/ doit exister avec son
                 <entite>.json.

Effets:
  - lit mvc/entities/<entite>/<entite>.json (refuse si introuvable) ;
  - valide la définition canonique ;
  - RÉGÉNÈRE mvc/entities/<entite>/<entite>.sql ;
  - RÉGÉNÈRE mvc/entities/<entite>/<entite>_base.py ;
  - PRÉSERVE mvc/entities/<entite>/<entite>.py (fichier manuel —
    jamais écrasé) ;
  - imprime les fichiers écrits / préservés.

ATTENTION:
  - <e>.sql et <e>_base.py sont ÉCRASÉS à chaque exécution (fichiers
    régénérables par convention Forge) ;
  - <e>.py est intact ;
  - vérifier le diff Git après exécution.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - ne traite qu'UNE entité ; pour toutes, voir forge build:model ;
  - ne traite pas relations.sql (voir forge sync:relations) ;
  - ne crée pas la base ni la table — voir forge db:init / db:apply.""",

    "sync:relations": """\
Usage:
  forge sync:relations

Description:
  Régénère mvc/entities/relations.sql à partir de
  mvc/entities/relations.json. Sous-ensemble de forge build:model
  ciblé sur les relations.

Effets:
  - lit mvc/entities/relations.json ;
  - valide le contrat de relations contre les définitions d'entités ;
  - RÉGÉNÈRE mvc/entities/relations.sql ;
  - imprime le fichier régénéré.

ATTENTION:
  - relations.sql est ÉCRASÉ à chaque exécution ;
  - vérifier le diff Git après exécution.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - ne traite pas les artefacts d'entité (.sql, _base.py) — voir
    forge sync:entity ou forge build:model ;
  - ne crée pas la base ni les tables — voir forge db:apply.""",

    "js:init": """\
Usage:
  forge js:init htmx
  forge js:init alpine
  forge js:init htmx-alpine

Description:
  Installe htmx, alpine ou les deux dans le projet : copie le bundle
  minifié depuis node_modules/ vers static/vendor/<lib>/ pour usage
  direct dans les templates Jinja2.

Arguments:
  htmx           Installe htmx (htmx.org) ;
  alpine         Installe alpine.js (alpinejs) ;
  htmx-alpine    Installe les deux.

Effets:
  - lance npm install pour ajouter la lib si absente de
    node_modules/ ;
  - copie node_modules/<lib>/dist/<lib>.min.js vers
    static/vendor/<lib>/<lib>.min.js ;
  - n'écrit pas dans mvc/.

ATTENTION:
  - cette commande peut télécharger des paquets npm (réseau requis) ;
  - elle copie un fichier sous static/vendor/ (créé si nécessaire).

Prérequis:
  - npm disponible dans le PATH ;
  - package.json présent à la racine (le squelette Forge en fournit
    un).

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - ne configure aucun build Tailwind ni bundler ;
  - ne modifie pas vos templates — l'inclusion <script src="..."> reste
    à votre charge ;
  - les versions installées sont celles de package.json.""",

    "docs:pdf": """\
Usage:
  forge docs:pdf

Description:
  Génère un PDF de la documentation Forge à partir de
  docs/quarkdown/forge-documentation.qd via l'outil Quarkdown.
  Destiné au DÉPÔT Forge lui-même, pas à un projet applicatif.

Effets:
  - cherche l'exécutable quarkdown dans le PATH ;
  - cherche la racine du dépôt Forge ;
  - lance « quarkdown c docs/quarkdown/forge-documentation.qd --pdf »
    dans un sous-processus ;
  - déplace le PDF produit vers l'emplacement cible attendu ;
  - sort en erreur si quarkdown est absent, si la source .qd manque,
    si quarkdown échoue, ou si le PDF n'apparaît pas à l'emplacement
    attendu.

Prérequis:
  - quarkdown installé et accessible (voir le message d'erreur de la
    commande pour les instructions d'installation) ;
  - fichier source docs/quarkdown/forge-documentation.qd présent.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - dépend d'un outil externe (Quarkdown) — pas de fallback ;
  - destiné au dépôt Forge, pas aux projets applicatifs ;
  - ne publie pas le PDF ; il est généré localement.""",

    "i18n:check": """\
Usage:
  forge i18n:check

Description:
  Vérifie la complétude et la validité des catalogues de traductions
  du projet (translations/*.json). Lecture seule.

Effets:
  - vérifie que translations/ existe ;
  - vérifie que translations/fr.json existe ;
  - pour chaque translations/*.json :
      * lit le JSON ;
      * vérifie que c'est un objet ;
      * pour chaque clé : type chaîne, non vide, notation pointée
        (« common.save » et non « commonSave »), pas de terme métier
        interdit ;
      * pour chaque valeur : type chaîne, non vide ;
  - imprime un statut par catalogue + nombre de clés vérifiées ;
  - n'écrit rien ;
  - exit 0 si tout est OK, 1 sinon.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - lecture seule — aucune correction automatique ;
  - ne crée pas le dossier translations/ (voir forge i18n:init) ;
  - ne télécharge ni ne fusionne aucune traduction externe.""",

    "deploy:check": """\
Usage:
  forge deploy:check

Description:
  Diagnostique l'environnement de déploiement du projet : racine
  Forge, Python, .venv, env/, env/prod, variables DB, dossiers
  storage, cohérence HTTP/HTTPS local vs Nginx. Lecture seule.

Effets:
  - vérifie d'être à la racine d'un projet Forge ;
  - vérifie Python 3.12+ ;
  - vérifie .venv/ ;
  - vérifie env/ et env/prod ;
  - parse env/prod et contrôle DB_HOST, DB_NAME, DB_APP_LOGIN,
    UPLOAD_ROOT ;
  - vérifie storage/ et storage/uploads/ ;
  - vérifie la cohérence APP_SSL_ENABLED vs deploy/nginx/forge-app.conf
    (Nginx termine TLS, Forge écoute en HTTP local) ;
  - imprime un tableau de statuts + résumé ;
  - exit 1 s'il existe au moins une erreur.

Options:
  -h, --help    Affiche cette aide sans exécuter la commande.

Limites:
  - lecture seule — aucun fichier modifié ;
  - ne contacte aucun serveur distant ;
  - ne lance ni Nginx, ni systemd, ni le serveur Forge ;
  - pour générer les fichiers de déploiement, voir forge deploy:init.""",
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
