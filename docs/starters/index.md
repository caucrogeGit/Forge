# Starters Forge

<div style="border:1px solid #FED7AA;background:linear-gradient(135deg,#FFF7ED 0%,#FFFFFF 58%,#F8FAFC 100%);border-radius:18px;padding:1.5rem 1.6rem;margin:1rem 0 1.5rem 0;">
  <p style="margin:0 0 .35rem 0;font-size:.85rem;font-weight:700;color:#EA580C;text-transform:uppercase;letter-spacing:.08em;">Forge · Parcours applicatifs</p>
  <h2 style="margin:.1rem 0 .45rem 0;font-size:2rem;line-height:1.15;color:#0F172A;">Apprendre Forge, palier par palier</h2>
  <p style="margin:0;color:#334155;font-size:1.05rem;max-width:880px;">Le parcours cœur pour les fondamentaux, puis un parcours par fonctionnalité pour chaque opt-in.</p>
</div>

## Qu'est-ce qu'un starter ?

Un **starter** est un parcours d'apprentissage que l'on réalise **à la main** en suivant la documentation.
Chaque palier montre le contrôleur, la vue et la route à créer pour comprendre une mécanique.
Un starter n'est pas un profil : voir [Profil ou starter ?](#difference-entre-profil-et-starter).

!!! tip "Par où commencer"
    Commencez par le parcours cœur ci-dessous, dans l'ordre, depuis [Bonjour Forge](welcome-forge/debutant/welcome.md).
    Abordez les fonctionnalités (opt-ins) une fois les fondamentaux acquis.

## Progression recommandée

Le parcours cœur `welcome-forge` est un **tutoriel continu** : un seul projet qui grandit palier après palier.
Les **11 paliers** des fondamentaux, dans l'ordre :

1. **Bonjour Forge** : afficher une réponse texte avec `Response.text(...)`. [Suivre](welcome-forge/debutant/welcome.md)
2. **Paramètres d'URL** : lire une valeur avec `request.query(...)`. [Suivre](welcome-forge/debutant/query-params.md)
3. **Première vue HTML** : rendre une page avec `BaseController.render(...)`. [Suivre](welcome-forge/debutant/first-html-view.md)
4. **Route dynamique** : lire un paramètre comme `/articles/{id}`. [Suivre](welcome-forge/debutant/dynamic-route.md)
5. **Inspecter une requête** : explorer `request.data` avec `Response.debug(...)`. [Suivre](welcome-forge/debutant/request-debug.md)
6. **Réponse JSON** : retourner des données avec `Response.json(...)`. [Suivre](welcome-forge/debutant/json-response.md)
7. **Le jeton CSRF** : la protection CSRF des formulaires. [Suivre](welcome-forge/debutant/csrf.md)
8. **Premier formulaire POST** : envoyer des données depuis un formulaire. [Suivre](welcome-forge/debutant/form-post.md)
9. **Validation serveur** : refuser ou accepter les données reçues. [Suivre](welcome-forge/debutant/server-validation.md)
10. **Première base SQL** : lire une donnée (MariaDB, migrations, SQL visible). [Suivre](welcome-forge/debutant/first-sql.md)
11. **Écrire en base** : insérer une ligne avec `db.insert(...)`. [Suivre](welcome-forge/debutant/first-sql-write.md)

Le parcours cœur se poursuit ensuite avec [les listes et la pagination](welcome-forge/intermediaire/list-records.md), puis [les relations et l'API JSON protégée](welcome-forge/avance/relations.md).

## Parcours par fonctionnalité

Chaque opt-in a son propre parcours d'apprentissage. Suivez-le quand vous ajoutez la fonctionnalité à votre projet.

### Sécurité et accès

- [MFA](../mfa/welcome/installation.md) : ajouter l'authentification multi-facteurs (TOTP, codes de récupération).
- [RBAC](../rbac/welcome/installation.md) : rôles et permissions déclaratives.
- [Audit](../audit/welcome/installation.md) : journaliser les actions sensibles.

### Données et persistance

- [Settings](../settings/welcome/installation.md) : paramètres applicatifs persistés.
- [Jobs](../jobs/welcome/installation.md) : tâches de fond adossées à la base SQL.
- [Notifications](../notifications/welcome/installation.md) : notifications in-app.
- [Import/Export CSV](../import-export/welcome/installation.md) : importer et exporter des données.
- [Statistiques](../stats/welcome/installation.md) : compter et agréger des événements.
- [Pivot](../pivot/welcome/installation.md) : tables pivot enrichies `many_to_many`.

### Médias et fichiers

- [Fichiers](../files/welcome/installation.md) : upload et service de fichiers sécurisés.
- [Images](../images/welcome/installation.md) : traitement et galeries d'images.
- [Audio](../audio/welcome/installation.md) : upload, transcodage et lecture audio.
- [Vidéo](../video/welcome/installation.md) : upload, transcodage et lecture vidéo.

### Contenu et communication

- [Mail](../mail/welcome/installation.md) : envoyer des courriels.
- [i18n](../i18n/welcome/installation.md) : internationaliser l'application.
- [QR Code](../qrcode/welcome/installation.md) : générer des QR Codes servables.

### Applicatif et exploitation

- [Workflow](../workflow/welcome/installation.md) : statuts et transitions.
- [Admin](../admin/welcome/installation.md) : back-office applicatif.
- [IoT](../iot/welcome/installation.md) : recevoir et exposer des données IoT.
- [Déploiement](../deploy/welcome/installation.md) : préparer la mise en production.

### Outils et infrastructure

- [Infrastructure de test](../testing/welcome/installation.md) : tester Forge et ses opt-ins.
- [Helpers](welcome-helpers/installation.md) : raccourcis et utilitaires applicatifs.
- [Markdown](welcome-markdown/installation.md) : rendre du contenu Markdown.

Catalogue des paquets et de leur API : [Packages opt-in](../optins/index.md).

## Profil ou starter ? { #difference-entre-profil-et-starter }

Un **profil** définit la base technique d'un projet créé avec `forge new` (`forge new MonProjet --profile standard`).
Un **starter** fournit un exemple applicatif que l'on construit *après* la création du projet.

Ils sont indépendants : un profil ne remplace pas un starter, un starter ne modifie pas le profil, et un starter peut illustrer un ou plusieurs profils.
Pour choisir un profil : [Profils de projet](../features/profiles.md).

## Comment suivre un starter

Un starter se suit **à la main**, palier par palier : chaque palier indique le contrôleur, la vue et la route à créer.

!!! note "Les starters ne se génèrent pas"
    Forge ne génère pas les starters et n'écrit jamais dans votre `mvc/routes.py`.
    Vous créez vous-même chaque fichier et ajoutez chaque route, en suivant la documentation du palier (voir [ADR-035](../adr/035-starters-manual-not-generated.md)).
