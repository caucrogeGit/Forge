# Roadmap, Tests terrain Forge

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

> Roadmap indépendante de la roadmap de construction Forge.
>
> Objectif : tester Forge comme un utilisateur réel l’apprendrait, depuis l’installation jusqu’à l’autonomie.

## Convention

- Préfixe : `FT`
- Un ticket terrain teste une action principale observable.
- Un ticket terrain ne corrige pas Forge.
- Chaque ticket détaillé doit respecter le [modèle de ticket FT](../testing/field-test-ticket-template.md).
- Chaque retour doit respecter le [modèle de retour testeur](../testing/field-test-feedback-template.md).

---

# FT-00, Cadre de la campagne terrain

Objectif : préparer la méthode, les modèles et les règles.

## Tickets

- `FT-00-TEST-CHARTER-001`, Définir la charte de test terrain.
- `FT-00-FEEDBACK-TEMPLATE-001`, Créer le modèle de retour d’expérience.
- `FT-00-SEVERITY-SCALE-001`, Définir les niveaux de gravité S0 à S5.
- `FT-00-GUIDANCE-LEVELS-001`, Définir les niveaux de guidage G0 à G3.
- `FT-00-HELP-LEVELS-001`, Définir les niveaux d’aide A0 à A5.
- `FT-00-TICKET-FORMAT-001`, Verrouiller la structure d’un ticket FT.
- `FT-00-TRIAGE-RULES-001`, Définir la transformation des retours en tickets correctifs.
- `FT-00-DOC-ERROR-PROTOCOL-001`, Définir la procédure si la documentation officielle est erronée pendant un ticket.
- `FT-00-ENV-MATRIX-001`, Définir les environnements de test.
- `FT-00-DEBUG-TOOLS-INTRO-001`, Découvrir les outils de diagnostic Forge.

---

# FT-01, Installation de Forge

Objectif : vérifier les parcours d’installation.

## Tickets

- `FT-01-INSTALL-PIPX-001`, Installer Forge avec `pipx`.
- `FT-01-INSTALL-VENV-001`, Installer Forge dans un environnement virtuel.
- `FT-01-INSTALL-GITHUB-001`, Installer Forge depuis GitHub.
- `FT-01-INSTALL-DEV-EDITABLE-001`, Installer Forge en mode développement.
- `FT-01-INSTALL-WINDOWS-WSL-001`, Installer Forge sous Windows avec WSL.
- `FT-01-INSTALL-DEBIAN-VM-001`, Installer Forge sur VM Debian propre.
- `FT-01-INSTALL-VERSION-CHECK-001`, Vérifier la version installée.
- `FT-01-INSTALL-UNINSTALL-001`, Désinstaller Forge proprement.
- `FT-01-PHASE-REVIEW-001`, Revue de phase installation.

---

# FT-02, Configuration de l’environnement

Objectif : vérifier `.env`, dev/prod, secrets et erreurs de configuration.

## Tickets

- `FT-02-ENV-FILES-LOCATE-001`, Identifier les fichiers d’environnement.
- `FT-02-ENV-EXAMPLE-COPY-001`, Créer une configuration locale depuis l’exemple.
- `FT-02-ENV-REQUIRED-VARS-001`, Identifier les variables obligatoires.
- `FT-02-ENV-OPTIONAL-VARS-001`, Identifier les variables optionnelles.
- `FT-02-ENV-DEV-MODE-001`, Configurer le mode développement.
- `FT-02-ENV-PROD-MODE-READ-001`, Lire la configuration production sans l’activer.
- `FT-02-ENV-MISSING-VAR-001`, Tester une variable manquante.
- `FT-02-ENV-BAD-VALUE-001`, Tester une valeur incorrecte.
- `FT-02-SECRETS-GITIGNORE-001`, Vérifier que les secrets ne partent pas dans Git.
- `FT-02-PHASE-REVIEW-001`, Revue de phase environnement.

---

# FT-03, MariaDB système

Objectif : préparer MariaDB sans utiliser root comme compte applicatif.

## Tickets

- `FT-03-MARIADB-INSTALL-CHECK-001`, Vérifier que MariaDB est installé.
- `FT-03-MARIADB-SERVICE-001`, Vérifier le service MariaDB.
- `FT-03-MARIADB-ROOT-ACCESS-001`, Vérifier l’accès administrateur local.
- `FT-03-MARIADB-DATABASE-CREATE-001`, Créer une base dédiée au projet.
- `FT-03-MARIADB-USER-CREATE-001`, Créer un utilisateur non-root.
- `FT-03-MARIADB-USER-GRANTS-001`, Donner les droits au bon schéma.
- `FT-03-MARIADB-USER-LOGIN-001`, Tester la connexion de l’utilisateur dédié.
- `FT-03-MARIADB-BAD-PASSWORD-001`, Tester une erreur de mot de passe.
- `FT-03-MARIADB-DATABASE-MISSING-001`, Tester une base absente.
- `FT-03-PHASE-REVIEW-001`, Revue de phase MariaDB.

---

# FT-04, Connexion Forge à MariaDB

Objectif : relier Forge à la base et tester les erreurs.

## Tickets

- `FT-04-FORGE-DB-CONFIG-001`, Renseigner la configuration DB côté Forge.
- `FT-04-FORGE-DB-CONNECTION-001`, Tester la connexion Forge à MariaDB.
- `FT-04-FORGE-DB-INIT-001`, Initialiser la base du projet.
- `FT-04-FORGE-DB-INIT-IDEMPOTENT-001`, Relancer l’initialisation.
- `FT-04-FORGE-DB-BAD-HOST-001`, Tester un mauvais host.
- `FT-04-FORGE-DB-BAD-LOGIN-001`, Tester un mauvais login.
- `FT-04-FORGE-DB-BAD-PASSWORD-001`, Tester un mauvais mot de passe.
- `FT-04-FORGE-DB-DOC-CHECK-001`, Vérifier la documentation base.
- `FT-04-PHASE-REVIEW-001`, Revue de phase connexion DB.

---

# FT-05, Premier projet Forge

Objectif : créer, lancer et observer un projet minimal.

## Tickets

- `FT-05-FIRST-PROJECT-CREATE-001`, Créer un projet minimal.
- `FT-05-FIRST-PROJECT-FILES-001`, Vérifier les fichiers générés.
- `FT-05-FIRST-PROJECT-RUN-001`, Lancer le projet.
- `FT-05-FIRST-PROJECT-HOMEPAGE-001`, Afficher la page d’accueil.
- `FT-05-FIRST-PROJECT-STOP-RESTART-001`, Arrêter et relancer le projet.
- `FT-05-FIRST-PROJECT-DOC-FOLLOW-001`, Suivre uniquement la documentation.
- `FT-05-FIRST-PROJECT-GIT-STATUS-001`, Observer l’état Git du projet.
- `FT-05-PHASE-REVIEW-001`, Revue de phase premier projet.

---

# FT-06, Architecture du projet

Objectif : distinguer framework, application, fichiers générés et fichiers manuels.

## Tickets

- `FT-06-ARCH-CORE-MVC-001`, Distinguer `core/` et `mvc/`.
- `FT-06-ARCH-ROUTES-001`, Identifier `mvc/routes.py`.
- `FT-06-ARCH-CONTROLLERS-001`, Identifier `mvc/controllers/`.
- `FT-06-ARCH-VIEWS-001`, Identifier `mvc/views/`.
- `FT-06-ARCH-MODELS-001`, Identifier `mvc/models/`.
- `FT-06-ARCH-ENTITIES-001`, Identifier `mvc/entities/`.
- `FT-06-ARCH-STATIC-STORAGE-001`, Distinguer `static/` et `storage/`.
- `FT-06-ARCH-DO-NOT-TOUCH-CORE-001`, Vérifier que le core n’est pas modifié.
- `FT-06-PHASE-REVIEW-001`, Revue de phase architecture.

---

# FT-07, Routes applicatives

Objectif : tester le routage minimal.

## Tickets

- `FT-07-ROUTE-FILE-OPEN-001`, Ouvrir et lire le fichier des routes.
- `FT-07-ROUTE-ADD-GET-001`, Ajouter une route GET simple.
- `FT-07-ROUTE-NAME-001`, Nommer une route.
- `FT-07-ROUTE-IMPORT-CONTROLLER-001`, Importer le contrôleur utilisé.
- `FT-07-ROUTE-UNKNOWN-URL-001`, Tester une URL non déclarée.
- `FT-07-ROUTE-DUPLICATE-001`, Tester une route dupliquée.
- `FT-07-ROUTE-METHOD-NOT-ALLOWED-001`, Tester une mauvaise méthode HTTP.
- `FT-07-PHASE-REVIEW-001`, Revue de phase routes.

---

# FT-08, Contrôleurs

Objectif : relier une route à une méthode de contrôleur.

## Tickets

- `FT-08-CONTROLLER-LOCATE-001`, Identifier le dossier des contrôleurs.
- `FT-08-CONTROLLER-CREATE-001`, Créer un contrôleur minimal.
- `FT-08-CONTROLLER-METHOD-001`, Créer une méthode appelée par la route.
- `FT-08-CONTROLLER-RETURN-TEXT-001`, Retourner une réponse texte simple.
- `FT-08-CONTROLLER-RETURN-HTML-001`, Retourner une réponse HTML simple.
- `FT-08-CONTROLLER-MISSING-METHOD-001`, Tester une méthode absente.
- `FT-08-CONTROLLER-BAD-IMPORT-001`, Tester un mauvais import.
- `FT-08-PHASE-REVIEW-001`, Revue de phase contrôleurs.

---

# FT-09, Premier template

Objectif : passer d’une réponse texte à une vue HTML.

## Tickets

- `FT-09-TEMPLATE-LOCATE-001`, Identifier le dossier des templates.
- `FT-09-TEMPLATE-CREATE-001`, Créer un template simple.
- `FT-09-TEMPLATE-RENDER-001`, Rendre un template depuis un contrôleur.
- `FT-09-TEMPLATE-VARIABLE-001`, Passer une variable au template.
- `FT-09-TEMPLATE-MISSING-001`, Tester un template absent.
- `FT-09-TEMPLATE-JINJA-ERROR-001`, Tester une erreur Jinja simple.
- `FT-09-PHASE-REVIEW-001`, Revue de phase premier template.

---

# FT-10, Templates Jinja

Objectif : tester les mécanismes Jinja utilisés par Forge.

## Tickets

- `FT-10-JINJA-EXTENDS-001`, Utiliser `{% extends %}`.
- `FT-10-JINJA-BLOCKS-001`, Utiliser les blocs Jinja.
- `FT-10-JINJA-INCLUDE-001`, Inclure un fragment de template.
- `FT-10-JINJA-LOOP-001`, Afficher une liste avec une boucle.
- `FT-10-JINJA-CONDITION-001`, Afficher selon une condition.
- `FT-10-JINJA-FILTER-001`, Utiliser un filtre Jinja simple.
- `FT-10-JINJA-MACRO-001`, Tester une macro si utilisée par Forge.
- `FT-10-JINJA-ESCAPING-001`, Vérifier l’échappement HTML.
- `FT-10-JINJA-ERRORS-001`, Observer les erreurs Jinja.
- `FT-10-PHASE-REVIEW-001`, Revue de phase Jinja.

---

# FT-11, Layout public

Objectif : construire une structure de page publique propre.

## Tickets

- `FT-11-LAYOUT-PUBLIC-LOCATE-001`, Identifier le layout public.
- `FT-11-LAYOUT-PUBLIC-EDIT-001`, Modifier le layout public.
- `FT-11-LAYOUT-NAVIGATION-001`, Ajouter une navigation.
- `FT-11-LAYOUT-FOOTER-001`, Ajouter un footer.
- `FT-11-LAYOUT-SCRIPTS-BLOCK-001`, Tester le bloc scripts si disponible.
- `FT-11-PUBLIC-PAGE-COMPLETE-001`, Créer une page publique complète.
- `FT-11-PUBLIC-404-001`, Tester une page inexistante.
- `FT-11-PHASE-REVIEW-001`, Revue de phase layout public.

---

# FT-12, Tailwind

Objectif : vérifier l’usage visuel simple sans usine front opaque.

## Tickets

- `FT-12-TAILWIND-SETUP-CHECK-001`, Vérifier comment Tailwind est disponible.
- `FT-12-TAILWIND-CLASS-BASIC-001`, Modifier l’apparence avec des classes.
- `FT-12-TAILWIND-BUTTONS-001`, Créer boutons et liens stylés.
- `FT-12-TAILWIND-CARD-001`, Créer une carte de contenu.
- `FT-12-TAILWIND-FORM-STYLE-001`, Styliser un formulaire.
- `FT-12-TAILWIND-RESPONSIVE-001`, Tester une mise en page responsive.
- `FT-12-TAILWIND-CUSTOM-CSS-001`, Ajouter un CSS complémentaire si nécessaire.
- `FT-12-TAILWIND-DOC-CHECK-001`, Vérifier la documentation front.
- `FT-12-PHASE-REVIEW-001`, Revue de phase Tailwind.

---

# FT-13, Formulaire public simple

Objectif : traiter une saisie utilisateur sans CRUD.

## Tickets

- `FT-13-FORM-GET-001`, Afficher un formulaire en GET.
- `FT-13-FORM-POST-001`, Recevoir une soumission POST.
- `FT-13-FORM-REQUIRED-FIELD-001`, Tester un champ obligatoire.
- `FT-13-FORM-ERROR-DISPLAY-001`, Afficher les erreurs utilisateur.
- `FT-13-FORM-SUCCESS-001`, Afficher un message de succès.
- `FT-13-FORM-INVALID-DATA-001`, Tester des données invalides.
- `FT-13-FORM-REDIRECT-AFTER-POST-001`, Tester un retour après POST si prévu.
- `FT-13-PHASE-REVIEW-001`, Revue de phase formulaires.

---

# FT-14, CSRF et formulaires sensibles

Objectif : vérifier la protection CSRF.

## Tickets

- `FT-14-CSRF-TOKEN-PRESENT-001`, Vérifier la présence du token CSRF.
- `FT-14-CSRF-VALID-SUBMIT-001`, Soumettre un formulaire valide.
- `FT-14-CSRF-MISSING-001`, Soumettre sans token.
- `FT-14-CSRF-INVALID-001`, Soumettre avec token invalide.
- `FT-14-CSRF-GET-SENSITIVE-001`, Vérifier qu’une action sensible n’est pas en GET.
- `FT-14-CSRF-ERROR-MESSAGE-001`, Évaluer le message d’erreur CSRF.
- `FT-14-PHASE-REVIEW-001`, Revue de phase CSRF.

---

# FT-15, HTMX progressif

Objectif : tester les interactions HTML partielles.

## Tickets

- `FT-15-HTMX-SETUP-CHECK-001`, Vérifier la disponibilité de HTMX.
- `FT-15-HTMX-PARTIAL-GET-001`, Charger un fragment HTML en GET.
- `FT-15-HTMX-TARGET-SWAP-001`, Tester `hx-target` et `hx-swap`.
- `FT-15-HTMX-FORM-POST-001`, Soumettre un formulaire avec HTMX.
- `FT-15-HTMX-VALIDATION-ERRORS-001`, Afficher des erreurs sans rechargement complet.
- `FT-15-HTMX-FALLBACK-001`, Vérifier le comportement sans HTMX si prévu.
- `FT-15-HTMX-DOC-CHECK-001`, Vérifier la documentation HTMX.
- `FT-15-PHASE-REVIEW-001`, Revue de phase HTMX.

---

# FT-16, Alpine.js optionnel

Objectif : vérifier qu’Alpine peut aider sans devenir obligatoire.

## Tickets

- `FT-16-ALPINE-SETUP-CHECK-001`, Vérifier la disponibilité d’Alpine.
- `FT-16-ALPINE-TOGGLE-001`, Créer un affichage masqué/visible.
- `FT-16-ALPINE-DROPDOWN-001`, Tester un menu déroulant.
- `FT-16-ALPINE-MODAL-001`, Tester une modale simple.
- `FT-16-ALPINE-FORM-STATE-001`, Tester un état local de formulaire.
- `FT-16-ALPINE-NO-DEPENDENCY-001`, Vérifier qu’Alpine reste optionnel.
- `FT-16-PHASE-REVIEW-001`, Revue de phase Alpine.

---

# FT-17, Mail en développement

Objectif : tester le mail sans envoi réel involontaire.

## Tickets

- `FT-17-MAIL-CONFIG-FAKE-001`, Configurer le transport fake.
- `FT-17-MAIL-CONFIG-LOG-001`, Configurer le transport log.
- `FT-17-MAIL-CONTACT-FORM-001`, Relier un formulaire de contact au mail.
- `FT-17-MAIL-TEMPLATE-001`, Utiliser un template de mail.
- `FT-17-MAIL-CONFIG-ERROR-001`, Tester une mauvaise configuration mail.
- `FT-17-MAIL-NO-REAL-SEND-DEV-001`, Vérifier l’absence d’envoi réel en dev.
- `FT-17-PHASE-REVIEW-001`, Revue de phase mail.

---

# FT-18, Découverte de la CLI

Objectif : comprendre la CLI avant génération.

## Tickets

- `FT-18-CLI-HELP-GLOBAL-001`, Lire l’aide globale.
- `FT-18-CLI-HELP-COMMAND-001`, Lire l’aide d’une commande.
- `FT-18-CLI-UNKNOWN-COMMAND-001`, Lancer une commande inconnue.
- `FT-18-CLI-MISSING-ARGUMENT-001`, Omettre un argument obligatoire.
- `FT-18-CLI-VERSION-001`, Vérifier la version via CLI.
- `FT-18-CLI-LIST-FAMILIES-001`, Identifier les familles de commandes.
- `FT-18-PHASE-REVIEW-001`, Revue de phase CLI.

---

# FT-19, Diagnostics CLI

Objectif : vérifier que Forge aide à trouver les problèmes.

## Tickets

- `FT-19-DOCTOR-CLEAN-PROJECT-001`, Lancer doctor sur projet sain.
- `FT-19-DOCTOR-MISSING-FILE-001`, Supprimer un fichier attendu.
- `FT-19-DOCTOR-BAD-CONFIG-001`, Casser une configuration.
- `FT-19-DOCTOR-BAD-ENTITY-001`, Casser une entité JSON.
- `FT-19-DOCTOR-BAD-ROUTE-001`, Casser une route.
- `FT-19-PROJECT-CHECK-STRICT-001`, Lancer le contrôle strict si disponible.
- `FT-19-PHASE-REVIEW-001`, Revue de phase diagnostics.

---

# FT-20, Routes via CLI

Objectif : vérifier que la CLI aide à comprendre le routage.

## Tickets

- `FT-20-ROUTES-LIST-001`, Lister les routes.
- `FT-20-ROUTES-LIST-NAMED-001`, Vérifier les routes nommées.
- `FT-20-ROUTES-LIST-METHODS-001`, Vérifier les méthodes HTTP.
- `FT-20-ROUTES-LIST-BROKEN-001`, Lister avec route cassée.
- `FT-20-ROUTES-DOC-CHECK-001`, Comparer CLI et documentation routes.
- `FT-20-PHASE-REVIEW-001`, Revue de phase routes CLI.

---

# FT-21, Entités JSON

Objectif : introduire le modèle de données Forge.

## Tickets

- `FT-21-ENTITY-FOLDER-001`, Identifier le dossier des entités.
- `FT-21-ENTITY-CREATE-MINIMAL-001`, Créer une entité minimale.
- `FT-21-ENTITY-STRING-FIELD-001`, Ajouter un champ texte.
- `FT-21-ENTITY-NUMBER-FIELD-001`, Ajouter un champ numérique.
- `FT-21-ENTITY-DATE-FIELD-001`, Ajouter un champ date.
- `FT-21-ENTITY-BOOLEAN-FIELD-001`, Ajouter un champ booléen.
- `FT-21-ENTITY-INVALID-JSON-001`, Casser le JSON.
- `FT-21-ENTITY-UNKNOWN-TYPE-001`, Utiliser un type inconnu.
- `FT-21-PHASE-REVIEW-001`, Revue de phase entités.

---

# FT-22, Modèles générés et fichiers manuels

Objectif : vérifier la séparation généré/manuel.

## Tickets

- `FT-22-BUILD-MODEL-001`, Générer un modèle depuis l’entité.
- `FT-22-MODEL-BASE-FILE-001`, Identifier le fichier `_base.py`.
- `FT-22-MODEL-MANUAL-FILE-001`, Identifier le fichier manuel.
- `FT-22-MODEL-MANUAL-CUSTOM-001`, Ajouter une méthode manuelle.
- `FT-22-MODEL-REGENERATE-001`, Régénérer après modification d’entité.
- `FT-22-MODEL-DO-NOT-EDIT-BASE-001`, Vérifier le risque de modifier `_base.py`.
- `FT-22-PHASE-REVIEW-001`, Revue de phase modèles.

---

# FT-23, SQL visible

Objectif : vérifier que Forge ne cache pas la base.

## Tickets

- `FT-23-SQL-GENERATE-001`, Générer le SQL d’une entité.
- `FT-23-SQL-FIELD-TYPES-001`, Vérifier les types SQL produits.
- `FT-23-SQL-PRIMARY-KEY-001`, Vérifier la clé primaire.
- `FT-23-SQL-NOT-NULL-001`, Vérifier les contraintes simples.
- `FT-23-SQL-RELATION-PREP-001`, Observer la préparation SQL d’une relation simple.
- `FT-23-SQL-REVIEW-BY-TESTER-001`, Lire le SQL avant application.
- `FT-23-PHASE-REVIEW-001`, Revue de phase SQL.

---

# FT-24, Migrations

Objectif : tester l’évolution de la base.

## Tickets

- `FT-24-MIGRATION-MAKE-FIRST-001`, Créer une première migration.
- `FT-24-MIGRATION-FILE-READ-001`, Lire le fichier de migration.
- `FT-24-MIGRATION-APPLY-001`, Appliquer une migration.
- `FT-24-MIGRATION-STATUS-001`, Lire l’état des migrations.
- `FT-24-MIGRATION-REAPPLY-001`, Relancer une migration appliquée.
- `FT-24-MIGRATION-ADD-FIELD-001`, Ajouter un champ et migrer.
- `FT-24-MIGRATION-BROKEN-SQL-001`, Tester une migration cassée.
- `FT-24-PHASE-REVIEW-001`, Revue de phase migrations.

---

# FT-25, CRUD : génération

Objectif : générer un CRUD simple.

## Tickets

- `FT-25-CRUD-PREPARE-ENTITY-001`, Préparer une entité CRUD simple.
- `FT-25-CRUD-GENERATE-001`, Générer le CRUD.
- `FT-25-CRUD-FILES-CREATED-001`, Vérifier les fichiers créés.
- `FT-25-CRUD-ROUTES-CHECK-001`, Vérifier les routes CRUD.
- `FT-25-CRUD-TEMPLATES-CHECK-001`, Vérifier les templates CRUD.
- `FT-25-CRUD-DO-NOT-TOUCH-CORE-001`, Vérifier qu’aucun core n’est modifié.
- `FT-25-PHASE-REVIEW-001`, Revue de phase génération CRUD.

---

# FT-26, CRUD : utilisation

Objectif : tester les opérations CRUD de base.

## Tickets

- `FT-26-CRUD-INDEX-001`, Afficher la liste.
- `FT-26-CRUD-CREATE-FORM-001`, Afficher le formulaire de création.
- `FT-26-CRUD-CREATE-SUBMIT-001`, Créer un enregistrement.
- `FT-26-CRUD-EDIT-FORM-001`, Afficher le formulaire d’édition.
- `FT-26-CRUD-EDIT-SUBMIT-001`, Modifier un enregistrement.
- `FT-26-CRUD-DELETE-001`, Supprimer un enregistrement.
- `FT-26-CRUD-DETAIL-001`, Afficher le détail si disponible.
- `FT-26-PHASE-REVIEW-001`, Revue de phase usage CRUD.

---

# FT-27, CRUD : validation et erreurs

Objectif : tester les mauvais usages du CRUD.

## Tickets

- `FT-27-CRUD-REQUIRED-FIELD-001`, Soumettre un champ obligatoire vide.
- `FT-27-CRUD-BAD-TYPE-001`, Soumettre un mauvais type.
- `FT-27-CRUD-UNKNOWN-ID-001`, Accéder à un ID inexistant.
- `FT-27-CRUD-DELETE-UNKNOWN-ID-001`, Supprimer un ID inexistant.
- `FT-27-CRUD-CSRF-001`, Tester CSRF sur actions sensibles.
- `FT-27-CRUD-ERROR-MESSAGES-001`, Évaluer les messages utilisateur.
- `FT-27-PHASE-REVIEW-001`, Revue de phase erreurs CRUD.

---

# FT-28, CRUD enrichi : recherche, tri, pagination

Objectif : tester l’usage quotidien d’un back-office.

## Tickets

- `FT-28-CRUD-SEED-DATA-001`, Créer un jeu de données de test.
- `FT-28-CRUD-SEARCH-001`, Tester la recherche texte.
- `FT-28-CRUD-SEARCH-EMPTY-001`, Tester une recherche sans résultat.
- `FT-28-CRUD-SORT-VALID-001`, Tester un tri autorisé.
- `FT-28-CRUD-SORT-INVALID-001`, Tester un tri invalide.
- `FT-28-CRUD-PAGINATION-001`, Tester la pagination.
- `FT-28-CRUD-QUERY-PARAMS-001`, Vérifier la conservation des paramètres.
- `FT-28-PHASE-REVIEW-001`, Revue de phase recherche/tri/pagination.

---

# FT-29, CRUD enrichi : filtres et export

Objectif : tester filtres et export CSV.

## Tickets

- `FT-29-CRUD-FILTER-SIMPLE-001`, Tester un filtre simple.
- `FT-29-CRUD-FILTER-INVALID-001`, Tester un filtre invalide.
- `FT-29-CRUD-FILTER-EMPTY-001`, Tester filtre sans résultat.
- `FT-29-CRUD-EXPORT-CSV-001`, Exporter les données.
- `FT-29-CRUD-EXPORT-SPECIAL-CHARS-001`, Exporter des caractères spéciaux.
- `FT-29-CRUD-EXPORT-FORMULA-INJECTION-001`, Tester injection CSV potentielle.
- `FT-29-CRUD-EXPORT-WITH-FILTERS-001`, Exporter avec filtres actifs.
- `FT-29-PHASE-REVIEW-001`, Revue de phase filtres/export.

---

# FT-30, Relations simples

Objectif : tester les relations entre deux entités.

## Tickets

- `FT-30-RELATION-PREPARE-ENTITIES-001`, Préparer deux entités liées.
- `FT-30-RELATION-MANY-TO-ONE-001`, Déclarer une relation many-to-one.
- `FT-30-RELATION-MIGRATION-001`, Migrer une relation.
- `FT-30-RELATION-FORM-001`, Saisir une relation dans un formulaire.
- `FT-30-RELATION-LIST-LABEL-001`, Afficher le libellé lié en liste.
- `FT-30-RELATION-EDIT-001`, Modifier une relation.
- `FT-30-RELATION-DELETE-LINKED-001`, Supprimer une donnée liée.
- `FT-30-PHASE-REVIEW-001`, Revue de phase relations simples.

---

# FT-31, Relations avancées

Objectif : tester les relations complexes si supportées.

## Tickets

- `FT-31-RELATION-MANY-TO-MANY-001`, Déclarer une relation many-to-many.
- `FT-31-RELATION-PIVOT-SQL-001`, Vérifier le SQL pivot.
- `FT-31-RELATION-MANY-FORM-001`, Saisir plusieurs relations.
- `FT-31-RELATION-MANY-LIST-001`, Afficher plusieurs relations.
- `FT-31-RELATION-MANY-UPDATE-001`, Modifier les relations.
- `FT-31-RELATION-MANY-DELETE-001`, Tester suppression et intégrité.
- `FT-31-PHASE-REVIEW-001`, Revue de phase relations avancées.

---

# FT-32, Médias et uploads

Objectif : tester les fichiers utilisateurs.

## Tickets

- `FT-32-UPLOAD-CONFIG-001`, Vérifier la configuration upload.
- `FT-32-UPLOAD-FORM-001`, Ajouter un champ fichier.
- `FT-32-UPLOAD-SIMPLE-FILE-001`, Envoyer un fichier simple.
- `FT-32-UPLOAD-IMAGE-001`, Envoyer une image.
- `FT-32-UPLOAD-STORAGE-PATH-001`, Vérifier le chemin stocké.
- `FT-32-UPLOAD-DISPLAY-001`, Afficher le média.
- `FT-32-UPLOAD-DELETE-001`, Supprimer le média.
- `FT-32-PHASE-REVIEW-001`, Revue de phase médias.

---

# FT-33, Sécurité uploads

Objectif : tester les garde-fous des fichiers.

## Tickets

- `FT-33-UPLOAD-PATH-TRAVERSAL-001`, Tester `../`.
- `FT-33-UPLOAD-WINDOWS-ABSOLUTE-001`, Tester chemin Windows absolu.
- `FT-33-UPLOAD-URL-EXTERNAL-001`, Tester une URL externe comme chemin.
- `FT-33-UPLOAD-BAD-EXTENSION-001`, Tester une extension interdite.
- `FT-33-UPLOAD-DOUBLE-EXTENSION-001`, Tester une double extension.
- `FT-33-UPLOAD-LARGE-FILE-001`, Tester un fichier trop gros.
- `FT-33-UPLOAD-UNICODE-NAME-001`, Tester un nom étrange.
- `FT-33-PHASE-REVIEW-001`, Revue de phase sécurité uploads.

---

# FT-34, Authentification

Objectif : tester le flux utilisateur connecté.

## Tickets

- `FT-34-AUTH-PREPARE-001`, Préparer l’authentification.
- `FT-34-AUTH-USER-CREATE-001`, Créer un utilisateur.
- `FT-34-AUTH-LOGIN-FORM-001`, Afficher le formulaire login.
- `FT-34-AUTH-LOGIN-SUCCESS-001`, Connexion réussie.
- `FT-34-AUTH-LOGIN-BAD-PASSWORD-001`, Mot de passe incorrect.
- `FT-34-AUTH-LOGIN-UNKNOWN-USER-001`, Utilisateur inconnu.
- `FT-34-AUTH-LOGOUT-001`, Déconnexion.
- `FT-34-AUTH-SESSION-AFTER-LOGOUT-001`, Accès après logout.
- `FT-34-PHASE-REVIEW-001`, Revue de phase auth.

---

# FT-35, Pages protégées

Objectif : vérifier l’accès privé.

## Tickets

- `FT-35-PROTECTED-PAGE-CREATE-001`, Créer une page privée.
- `FT-35-PROTECTED-ANONYMOUS-001`, Accès anonyme refusé.
- `FT-35-PROTECTED-LOGIN-REDIRECT-001`, Redirection vers login.
- `FT-35-PROTECTED-CONNECTED-001`, Accès connecté autorisé.
- `FT-35-PROTECTED-DIRECT-URL-001`, Accès direct par URL.
- `FT-35-PROTECTED-TEMPLATE-LINKS-001`, Liens visibles selon connexion.
- `FT-35-PHASE-REVIEW-001`, Revue de phase pages protégées.

---

# FT-36, RBAC

Objectif : tester rôles, permissions et autorisation serveur.

## Tickets

- `FT-36-RBAC-ROLE-CREATE-001`, Créer un rôle.
- `FT-36-RBAC-PERMISSION-CREATE-001`, Créer une permission.
- `FT-36-RBAC-ASSIGN-USER-001`, Assigner un rôle à un utilisateur.
- `FT-36-RBAC-PROTECT-ROUTE-001`, Protéger une route.
- `FT-36-RBAC-PROTECT-CRUD-001`, Protéger un CRUD.
- `FT-36-RBAC-FORBIDDEN-001`, Accès sans permission.
- `FT-36-RBAC-BYPASS-POST-001`, POST manuel sans permission.
- `FT-36-PHASE-REVIEW-001`, Revue de phase RBAC.

---

# FT-37, Diagnostics d’erreurs applicatives

Objectif : vérifier que les erreurs sont compréhensibles.

## Tickets

- `FT-37-ERROR-404-001`, Tester une page absente.
- `FT-37-ERROR-CONTROLLER-001`, Casser un contrôleur.
- `FT-37-ERROR-TEMPLATE-001`, Casser un template.
- `FT-37-ERROR-SQL-001`, Provoquer une erreur SQL.
- `FT-37-ERROR-ENTITY-001`, Casser une entité.
- `FT-37-ERROR-LOG-FILE-001`, Retrouver l’erreur dans les logs.
- `FT-37-ERROR-NO-SECRETS-001`, Vérifier l’absence de secrets dans l’erreur.
- `FT-37-PHASE-REVIEW-001`, Revue de phase diagnostics erreurs.

---

# FT-38, Mode production local

Objectif : préparer le passage hors développement.

## Tickets

- `FT-38-PROD-CONFIG-001`, Configurer un mode production local.
- `FT-38-PROD-DEBUG-OFF-001`, Désactiver le debug.
- `FT-38-PROD-SECRET-KEY-001`, Vérifier la clé secrète.
- `FT-38-PROD-STATIC-001`, Tester les fichiers statiques.
- `FT-38-PROD-MEDIA-001`, Tester les médias.
- `FT-38-PROD-HEADERS-001`, Vérifier les headers de sécurité.
- `FT-38-PHASE-REVIEW-001`, Revue de phase production locale.

---

# FT-39, Déploiement serveur

Objectif : vérifier qu’une application Forge peut être déployée.

## Tickets

- `FT-39-DEPLOY-DEBIAN-PREP-001`, Préparer une VM Debian.
- `FT-39-DEPLOY-APP-INSTALL-001`, Installer l’application Forge.
- `FT-39-DEPLOY-VENV-001`, Créer l’environnement Python serveur.
- `FT-39-DEPLOY-ENV-001`, Configurer l’environnement serveur.
- `FT-39-DEPLOY-MARIADB-001`, Connecter MariaDB serveur.
- `FT-39-DEPLOY-RUN-001`, Lancer l’application.
- `FT-39-DEPLOY-LOGS-001`, Lire les logs serveur.
- `FT-39-DEPLOY-RESTART-001`, Redémarrer l’application.
- `FT-39-PHASE-REVIEW-001`, Revue de phase déploiement.

---

# FT-40, Mise à jour et maintenance

Objectif : tester l’évolution d’un projet Forge.

## Tickets

- `FT-40-MAINTAIN-ADD-PAGE-001`, Ajouter une page après coup.
- `FT-40-MAINTAIN-ADD-FIELD-001`, Ajouter un champ à une entité.
- `FT-40-MAINTAIN-REGENERATE-001`, Régénérer sans perdre le code manuel.
- `FT-40-MAINTAIN-UPDATE-FORGE-001`, Mettre à jour Forge.
- `FT-40-MAINTAIN-ROLLBACK-001`, Tester un retour arrière simple.
- `FT-40-MAINTAIN-DOC-GAPS-001`, Identifier les manques de documentation maintenance.
- `FT-40-PHASE-REVIEW-001`, Revue de phase maintenance.

---

# FT-41, Mini-projet guidé complet

Objectif : assembler les briques dans une application cohérente.

## Tickets

- `FT-41-MINIAPP-SCOPE-001`, Définir le mini-projet.
- `FT-41-MINIAPP-INSTALL-001`, Préparer l’environnement.
- `FT-41-MINIAPP-PUBLIC-001`, Créer la partie publique.
- `FT-41-MINIAPP-FORM-001`, Ajouter un formulaire public.
- `FT-41-MINIAPP-ENTITIES-001`, Créer les entités.
- `FT-41-MINIAPP-MIGRATIONS-001`, Appliquer les migrations.
- `FT-41-MINIAPP-CRUD-001`, Générer le back-office.
- `FT-41-MINIAPP-RELATIONS-001`, Ajouter des relations.
- `FT-41-MINIAPP-MEDIA-001`, Ajouter des médias.
- `FT-41-MINIAPP-AUTH-001`, Ajouter une zone protégée.
- `FT-41-MINIAPP-REVIEW-001`, Faire le bilan guidé.

---

# FT-42, Projet autonome

Objectif : vérifier que le testeur peut utiliser Forge sans procédure détaillée.

## Tickets

- `FT-42-AUTONOMOUS-BRIEF-001`, Donner un objectif applicatif simple.
- `FT-42-AUTONOMOUS-CREATE-001`, Créer le projet.
- `FT-42-AUTONOMOUS-CONFIG-001`, Configurer l’environnement.
- `FT-42-AUTONOMOUS-DATA-001`, Créer le modèle de données.
- `FT-42-AUTONOMOUS-PAGES-001`, Créer les pages nécessaires.
- `FT-42-AUTONOMOUS-CRUD-001`, Générer et adapter le CRUD.
- `FT-42-AUTONOMOUS-DEBUG-001`, Résoudre une erreur rencontrée.
- `FT-42-AUTONOMOUS-FINAL-REPORT-001`, Produire le retour final.

---

# FT-43, Consolidation des retours terrain

Objectif : transformer les retours en décisions exploitables.

## Tickets

- `FT-43-FEEDBACK-COLLECT-001`, Centraliser tous les retours.
- `FT-43-FEEDBACK-NORMALIZE-001`, Normaliser les retours.
- `FT-43-FEEDBACK-SEVERITY-001`, Classer par gravité.
- `FT-43-FEEDBACK-DUPLICATES-001`, Fusionner les doublons.
- `FT-43-FEEDBACK-BLOCKERS-001`, Identifier les bloquants.
- `FT-43-FEEDBACK-DOC-ISSUES-001`, Identifier les problèmes documentaires.
- `FT-43-FEEDBACK-OFFICIAL-DOC-ERRORS-001`, Isoler les erreurs de documentation officielle bloquantes ou trompeuses.
- `FT-43-FEEDBACK-CORRECTIVE-TICKETS-001`, Créer les tickets correctifs.
- `FT-43-PHASE-REVIEW-001`, Revue de phase consolidation.

---

# FT-44, Conversion des tickets validés en tutoriels

Objectif : transformer les tickets FT validés en pages tutoriels utilisables dans la documentation Forge.

## Tickets

- `FT-44-TUTORIAL-SELECTION-001`, Identifier les tickets FT validés pouvant devenir tutoriels.
- `FT-44-TUTORIAL-CONVERSION-RULES-001`, Définir la transformation ticket FT vers page tutoriel.
- `FT-44-TUTORIAL-DOC-ERROR-CHECK-001`, Vérifier qu’aucune erreur documentaire connue ne passe dans les tutoriels.
- `FT-44-TUTORIAL-INSTALLATION-001`, Créer les tutoriels issus des tickets d’installation validés.
- `FT-44-TUTORIAL-CONFIG-DB-001`, Créer les tutoriels environnement et MariaDB.
- `FT-44-TUTORIAL-FIRST-PAGES-001`, Créer les tutoriels route, contrôleur et template.
- `FT-44-TUTORIAL-FRONT-001`, Créer les tutoriels Jinja, Tailwind, HTMX et Alpine.
- `FT-44-TUTORIAL-DATA-CRUD-001`, Créer les tutoriels entités, SQL, migrations et CRUD.
- `FT-44-TUTORIAL-AUTH-SECURITY-001`, Créer les tutoriels auth, RBAC et sécurité.
- `FT-44-TUTORIAL-DEPLOY-MAINTAIN-001`, Créer les tutoriels déploiement et maintenance.
- `FT-44-TUTORIAL-MKDOCS-NAV-001`, Ajouter le menu Tutoriels dans MkDocs.
- `FT-44-TUTORIAL-STRICT-BUILD-001`, Valider la documentation avec `mkdocs build --strict`.
- `FT-44-PHASE-REVIEW-001`, Revue de phase conversion documentation.

---

# FT-45, Décision bêta ou stable

Objectif : décider objectivement si Forge peut sortir de bêta.

## Tickets

- `FT-45-STABLE-CRITERIA-001`, Définir les critères de stabilité.
- `FT-45-INSTALL-READINESS-001`, Vérifier la maturité installation.
- `FT-45-DOC-READINESS-001`, Vérifier la maturité documentation.
- `FT-45-USAGE-READINESS-001`, Vérifier la maturité usage réel.
- `FT-45-BLOCKERS-REVIEW-001`, Vérifier les bloquants restants.
- `FT-45-BETA-EXTEND-DECISION-001`, Décider si la bêta continue.
- `FT-45-STABLE-GO-NOGO-001`, Décider stable ou non.

---

# Résumé synthétique

```text
FT-00  Cadre de campagne
FT-01  Installation
FT-02  Configuration environnement
FT-03  MariaDB système
FT-04  Connexion Forge à MariaDB
FT-05  Premier projet
FT-06  Architecture projet
FT-07  Routes
FT-08  Contrôleurs
FT-09  Premier template
FT-10  Templates Jinja
FT-11  Layout public
FT-12  Tailwind
FT-13  Formulaires publics
FT-14  CSRF
FT-15  HTMX
FT-16  Alpine.js
FT-17  Mail développement
FT-18  CLI
FT-19  Diagnostics CLI
FT-20  Routes via CLI
FT-21  Entités JSON
FT-22  Modèles générés/manuels
FT-23  SQL visible
FT-24  Migrations
FT-25  CRUD génération
FT-26  CRUD utilisation
FT-27  CRUD validation/erreurs
FT-28  CRUD recherche/tri/pagination
FT-29  CRUD filtres/export
FT-30  Relations simples
FT-31  Relations avancées
FT-32  Médias/uploads
FT-33  Sécurité uploads
FT-34  Authentification
FT-35  Pages protégées
FT-36  RBAC
FT-37  Diagnostics erreurs applicatives
FT-38  Production locale
FT-39  Déploiement serveur
FT-40  Maintenance
FT-41  Mini-projet guidé
FT-42  Projet autonome
FT-43  Consolidation retours
FT-44  Conversion tickets validés en tutoriels
FT-45  Décision bêta/stable
```
