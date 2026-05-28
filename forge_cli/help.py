"""Texte d'aide de la CLI Forge, affiché par forge help / forge --help."""

from __future__ import annotations

_HELP_TEMPLATE = """\
Forge {version} — Framework MVC Python

  forge <commande> [arguments]

Projet
  new <NomProjet>    Crée un nouveau projet Forge.
  run                Lance Forge (dev) ou affiche la stratégie WSGI (prod).
  update             Met à jour Forge dans l'environnement courant (.venv / pipx).
  doctor             Diagnostic large et tolérant (lecture seule).
  project:check      Contrôle strict des conventions (CI-ready).
  project:audit      Rapport d'audit détaillé non destructif.
  routes:list        Affiche les routes déclarées.

Entités
  make:entity        Génère une entité JSON et son modèle Python.
  make:crud          Génère un CRUD complet (liste, fiche, formulaires).
  make:pivot-crud    Génère un sous-CRUD dédié pour un pivot avec attributs.
  make:relation      Déclare une relation entre entités.
  entity:validate    Valide les entités et relations contre les schémas JSON.
  sync:entity        Régénère les fichiers modèles.
  sync:relations     Régénère relations.sql.
  sync:landing       Synchronise la landing page vers docs/.
  build:model        Régénère tous les modèles Python.
  check:model        Vérifie la cohérence des modèles.

Pages publiques
  make:public-page      Page statique publique.
  make:public-list      Liste publique paginée.
  make:public-show      Fiche publique détaillée.
  make:public-form      Formulaire public.
  make:public-contact   Page de contact publique.

Base de données
  db:init             Crée la base de données depuis les entités.
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

Starters et modules
  starter:list        Liste les starter apps disponibles.
  starter:build       Génère un starter app dans le projet.
  module:list         Liste les modules disponibles.
  module:install      Installe un module dans le projet.
  module:files        Copie les fichiers d'un module.
  module:routes       Injecte les routes d'un module.

Auth / Sécurité
  auth:init                 Initialise les tables d'authentification.
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

Documentation
  docs:pdf            Génère un PDF depuis la documentation.

Internationalisation
  i18n:init           Initialise les fichiers de traduction.
  i18n:check          Vérifie la complétude des traductions.

Médias et JavaScript
  upload:init         Configure les uploads de fichiers.
  media:init          Configure les médias.
  js:init             Installe htmx, alpine ou les deux.

Déploiement
  deploy:init         Initialise la configuration de déploiement.
  deploy:check        Vérifie la configuration de déploiement.

Version et aide
  --version           Affiche la version de Forge.
  help, --help, -h    Affiche cette aide.

Exemples :
  forge new GestionVentes
  forge make:entity Contact && forge make:crud Contact
  forge doctor && forge project:check

Documentation : https://github.com/caucrogeGit/Forge
"""


def build_help(version: str) -> str:
    return _HELP_TEMPLATE.format(version=version)
