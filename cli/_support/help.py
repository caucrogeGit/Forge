# pyright: strict
"""Texte d'aide de la CLI Forge, affiché par forge help / forge --help."""

from __future__ import annotations

_HELP_TEMPLATE = """\
Forge {version} — Framework MVC Python

  forge <commande> [arguments]

Projet
  new <NomProjet>    Crée un nouveau projet Forge.
  skeleton:upgrade   Ajoute au projet les fichiers du squelette manquants (write-if-new).
  run                Lance Forge (dev) ou affiche la stratégie WSGI (prod).
  update             Met à jour Forge dans l'environnement courant (.venv / pipx).
  doctor             Diagnostic large et tolérant (lecture seule).
  project:check      Contrôle strict des conventions (CI-ready).
  project:audit      Rapport d'audit détaillé non destructif.
  routes:list        Affiche les routes déclarées.
  agents:init        Génère/rafraîchit la guidance agent IA (CLAUDE.md, AGENTS.md, ADR-001).

Entités
  make:entity        Génère une entité JSON et son modèle Python.
  make:crud          Génère un CRUD complet (liste, fiche, formulaires).
  make:pivot-crud    Génère un sous-CRUD dédié pour un pivot avec attributs.
  make:relation      Déclare une relation entre entités.
  entity:validate    Valide les entités et relations contre les schémas JSON.
  entity:doc         Documente entités et relations (Markdown + diagramme Mermaid).
  sync:entity        Régénère les fichiers modèles.
  sync:relations     Régénère relations.sql.
  build:model        Régénère tous les modèles Python.
  check:model        Vérifie la cohérence des modèles.

Pages publiques
  make:public-page      Page statique publique.
  make:public-list      Liste publique paginée.
  make:public-show      Fiche publique détaillée.
  make:public-form      Formulaire public.
  make:public-contact   Page de contact publique.

Base de données
  db:config           Amorce les variables d'environnement du backend.
  db:init             Affiche le SQL de provisioning de la base (--run pour exécuter).
  db:apply            Applique le schéma SQL.
  migration:status    Statut des migrations.
  migration:apply     Applique les migrations en attente.
  migration:make      Crée une nouvelle migration SQL.
  migration:diff      Génère un diff SQL entre entité et base.

Schémas JSON
  schema:list        Liste les schémas JSON Forge disponibles localement.
  schema:doctor      Diagnostique les schémas JSON Forge (présence, validité, $ref).

Sécurité
  rbac:validate      Valide mvc/security/rbac.json avec le schéma RBAC Forge.
  rbac:audit         Audit de cohérence fonctionnelle de mvc/security/rbac.json.

Modules
  module:list         Liste les modules disponibles.
  module:install      Installe un module dans le projet.
  module:files        Copie les fichiers d'un module.
  module:routes       Injecte les routes d'un module.
  module:remove       Désinstalle un module (fichiers inchangés).

Auth / Sécurité
  auth:init                 Initialise les tables d'authentification.
  make:auth                 Scaffolde le flux de connexion (contrôleur, vue, routes).
  auth:doctor               Diagnostic du système d'authentification.
  auth:status               État des briques d'authentification installées.
  auth:list-sql             Affiche les fichiers SQL d'authentification.
  auth:user:create          Crée un compte utilisateur.
  auth:user:list            Liste les comptes utilisateurs.
  auth:user:show            Affiche les détails d'un compte utilisateur.
  auth:user:disable         Désactive un compte utilisateur.
  auth:user:enable          Réactive un compte utilisateur.
  auth:user:password        Modifie le mot de passe d'un compte.
  auth:user:role:add        Assigne un rôle à un utilisateur.
  auth:user:role:remove     Retire un rôle d'un utilisateur.
  auth:user:roles           Affiche les rôles d'un utilisateur.

Mail
  mail:init           Initialise la configuration mail.
  mail:test           Envoie un mail de test.
  mail:render         Rend un template de mail (preview).
  mail:doctor         Diagnostic de la configuration mail.
  mail:logs           Affiche les derniers logs mail.

IoT (module opt-in forge-mvc-iot)
  iot:doctor          Diagnostic statique du module IoT (package, config, migration, API HTTP).
  iot:init            Copie la migration IoT du package vers mvc/migrations/ (idempotent, sans appliquer).
  iot:simulate        Publie des mesures MQTT factices conformes au contrat (sans capteur).
  iot:listen          Écoute le broker MQTT et insère les mesures reçues dans iot_events.
  iot:gc              Purge les mesures iot_events antérieures à une rétention (--days N, --run).

Vidéo (module opt-in forge-mvc-video)
  video:doctor        Diagnostic statique du module vidéo (package, config, ffmpeg/ffprobe).
  video:init          Copie la migration vidéo du package vers mvc/migrations/ (idempotent, sans appliquer).
  video:upload        Upload une vidéo source : <fichier> [--title "..."] (statut uploaded).
  video:process       Traite une vidéo (probe + poster + transcodage MP4) : <id> ou --pending.
  video:cleanup       Purge les vidéos failed / fichiers orphelins (dry-run par défaut, --apply).

Audio (module opt-in forge-mvc-audio)
  audio:doctor        Diagnostic statique du module audio (package, config, ffmpeg/ffprobe).
  audio:trim          Découpe un fichier audio entre deux instants (ne touche pas la source).

Admin (module opt-in forge-mvc-admin)
  admin:init          Prépare la structure mvc/admin/ du back-office (write-if-new, sans écrasement).
  admin:doctor        Vérifie la cohérence des ressources admin avec les contrats d'entité (lecture seule).

Opt-ins (branchement projet)
  opt-in:install      Affiche la commande d'installation du package d'un opt-in officiel.
  opt-in:remove       Affiche la commande de désinstallation du package d'un opt-in officiel.
  opt-in:enable       Branche un opt-in dans le projet (optins/) ; dry-run par défaut, --apply pour écrire.
  opt-in:disable      Débranche un opt-in du projet (retire optins/) ; dry-run par défaut, --apply pour écrire.
  opt-in:list         Affiche les opt-ins officiels et leur état projet (lecture seule).
  opt-in:installed    Affiche les opt-ins réellement installés (pip, lecture seule).

Documentation
  docs:pdf            Génère un PDF depuis la documentation.

Internationalisation
  i18n:init           Initialise les fichiers de traduction.
  i18n:check          Vérifie la complétude des traductions.

Médias et JavaScript
  upload:init         Configure les uploads de fichiers.
  media:init          Configure les médias.
  files:init          Écrit la migration du registre de fichiers (forge-mvc-files, ADR-094).
  files:orphans       Rapproche le dossier d'upload et le registre (affiche ; --delete supprime).
  images:init         Copie la migration Images du package vers mvc/migrations/ (idempotent, sans appliquer).
  images:orphans      Liste les variantes sans original ou d'un préréglage retiré (--delete supprime).
  js:init             Installe htmx, alpine ou les deux.

Déploiement
  deploy:init         Initialise la configuration de déploiement.
  deploy:check        Vérifie la configuration de déploiement.

Opt-ins applicatifs
  settings:init       Prépare la table des paramètres applicatifs (forge-mvc-settings).
  stats:init          Prépare la table des événements statistiques (forge-mvc-stats).
  stats:gc            Purge les événements statistiques par âge (affiche ; --run exécute).
  audit:init          Prépare le journal d'audit applicatif (forge-mvc-audit).
  audit:gc            Purge le journal d'audit par âge (affiche ; --run exécute).
  jobs:init           Prépare la file de tâches de fond (forge-mvc-jobs).
  jobs:reclaim        Reprend les tâches orphelines d'un worker planté.
  jobs:status         Affiche l'état des files de tâches (lecture seule).
  mfa:init            Prépare le registre anti-rejeu TOTP partagé (forge-mvc-mfa, optionnel).
  notifications:init  Prépare les notifications in-app (forge-mvc-notifications).
  rbac:init           Génère les migrations RBAC (roles, permissions, role_permissions) vers mvc/migrations/.
  sessions:init       Génère la migration Sessions vers mvc/migrations/ (idempotent, sans appliquer).
  sessions:gc         Purge les sessions expirées (à brancher sur cron/systemd).

Fixtures (démo/test)
  fixtures:load          Charge les fixtures mvc/fixtures/*.sql (affiche ; --run exécute).
  fixtures:purge         Vide les tables ciblées par les fixtures (affiche ; --run exécute).
  fixtures:generate      Génère un .sql depuis une factory (Faker, forge-mvc-fixtures).
  fixtures:make-factory  Échafaude une factory depuis le contrat d'entité (scaffold riche).

Version et aide
  --version           Affiche la version de Forge.
  help, --help, -h    Affiche cette aide.

Exemples :
  forge new GestionVentes
  forge make:entity Contact && forge make:crud Contact
  forge doctor && forge project:check

Documentation : https://forgemvc.com/docs/forge/
Dépôt         : https://github.com/caucrogeGit/Forge
"""


def build_help(version: str) -> str:
    return _HELP_TEMPLATE.format(version=version)
