# Starters Forge

<div style="border:1px solid #FED7AA;background:linear-gradient(135deg,#FFF7ED 0%,#FFFFFF 58%,#F8FAFC 100%);border-radius:18px;padding:1.5rem 1.6rem;margin:1rem 0 1.5rem 0;">
  <p style="margin:0 0 .35rem 0;font-size:.85rem;font-weight:700;color:#EA580C;text-transform:uppercase;letter-spacing:.08em;">Forge · Parcours applicatifs</p>
  <h2 style="margin:.1rem 0 .45rem 0;font-size:2rem;line-height:1.15;color:#0F172A;">Vue d'ensemble des starters</h2>
  <p style="margin:0;color:#334155;font-size:1.05rem;max-width:880px;">Des parcours progressifs pour apprendre Forge, reconstruire vite et adapter à un vrai projet.</p>
</div>

## Principe

Un **starter** Forge est un parcours d'apprentissage que l'on réalise à la main en suivant la documentation.
Chaque palier montre le contrôleur, la vue et la route à créer pour comprendre une mécanique du framework.
Un starter n'est pas un profil, voir
[Différence entre profil et starter](#difference-entre-profil-et-starter).

Profils recommandés selon le starter : `minimal` ou `standard` pour les paliers
avec base de données, aucun profil pour les paliers sans base.

## Catalogue

La progression cœur `welcome-forge` enseigne les fondamentaux ; chaque opt-in a
sa propre progression `welcome-<module>` (débutant puis avancé).

### Bonjour Forge : progression cœur (`welcome-forge`)

*Débutant, 11 paliers (tutoriel continu)* : [Bonjour Forge](welcome-forge/debutant/welcome.md) · [Paramètres d'URL](welcome-forge/debutant/query-params.md) · [Première vue HTML](welcome-forge/debutant/first-html-view.md) · [Route dynamique](welcome-forge/debutant/dynamic-route.md) · [Inspecter une requête](welcome-forge/debutant/request-debug.md) · [Réponse JSON](welcome-forge/debutant/json-response.md) · [Le jeton CSRF](welcome-forge/debutant/csrf.md) · [Premier formulaire POST](welcome-forge/debutant/form-post.md) · [Validation serveur](welcome-forge/debutant/server-validation.md) · [Première base SQL](welcome-forge/debutant/first-sql.md) · [Écrire en base](welcome-forge/debutant/first-sql-write.md)

*Intermédiaire, 8 paliers (tutoriel continu)* : [Lister des enregistrements](welcome-forge/intermediaire/list-records.md) · [Héritage de gabarit](welcome-forge/intermediaire/layout-template.md) · [Rechercher / filtrer](welcome-forge/intermediaire/filter-list.md) · [Paginer une liste](welcome-forge/intermediaire/pagination.md) · [Modifier un enregistrement](welcome-forge/intermediaire/update-record.md) · [Supprimer un enregistrement](welcome-forge/intermediaire/delete-record.md) · [Messages flash](welcome-forge/intermediaire/flash-messages.md) · [Mémoriser un état en session](welcome-forge/intermediaire/session-state.md)

*Avancé, 4 paliers (tutoriel continu)* : [Relations entre tables](welcome-forge/avance/relations.md) · [Écritures transactionnelles](welcome-forge/avance/db-transaction.md) · [Téléverser un fichier](welcome-forge/avance/file-upload.md) · [API JSON protégée](welcome-forge/avance/json-api.md)

### IoT (opt-in `forge-mvc-iot`)

[Bonjour Forge IoT](welcome-iot/debutant/iot-welcome.md) · [Lire les événements IoT](welcome-iot/debutant/iot-events.md) · [Les événements d'un capteur](welcome-iot/debutant/iot-device.md) · [Simuler une mesure IoT](welcome-iot/intermediaire/iot-simulate.md) · [Exposer l'API IoT](welcome-iot/intermediaire/iot-api.md) · [Tableau de bord IoT](welcome-iot/intermediaire/iot-dashboard.md) · [Valider un message IoT](welcome-iot/avance/iot-contract.md) · [Le subscriber MQTT](welcome-iot/avance/iot-subscriber.md) · [Diagnostiquer le module IoT](welcome-iot/avance/iot-doctor.md)

### Vidéo (opt-in `forge-mvc-video`)

[Bonjour Forge Vidéo](welcome-video/debutant/video-welcome.md) · [Lister les vidéos](welcome-video/debutant/video-list.md) · [Le détail d'une vidéo](welcome-video/debutant/video-detail.md) · [Téléverser une vidéo](welcome-video/intermediaire/video-upload.md) · [Lire une vidéo](welcome-video/intermediaire/video-playback.md) · [Suivre l'état d'une vidéo](welcome-video/intermediaire/video-status.md) · [Sonder une vidéo](welcome-video/avance/video-probe.md) · [Transcoder une vidéo](welcome-video/avance/video-transcode.md) · [Diagnostiquer le module Vidéo](welcome-video/avance/video-doctor.md)

### Images (opt-in `forge-mvc-images`)

[Bonjour Forge Images](../images/welcome/debutant/images-welcome.md) · [Téléverser une image](../images/welcome/debutant/image-upload.md) · [Miniatures et variantes](../images/welcome/debutant/image-variants.md) · [Rattacher une image à une entité](../images/welcome/intermediaire/image-attach.md) · [Afficher la galerie](../images/welcome/intermediaire/image-gallery.md) · [Texte alternatif et ordre](../images/welcome/intermediaire/image-alt-order.md) · [Image de couverture](../images/welcome/avance/image-cover.md) · [Supprimer proprement](../images/welcome/avance/image-delete.md) · [Garde de sécurité à l'upload](../images/welcome/avance/image-safety.md)

### Fichiers (opt-in `forge-mvc-files`)

[Bonjour Forge Files](../files/welcome/debutant/files-welcome.md) · [Stocker un document](../files/welcome/debutant/file-store.md) · [Servir un fichier](../files/welcome/debutant/file-serve.md) · [Valider un upload](../files/welcome/intermediaire/file-validate.md) · [Limiter les uploads](../files/welcome/intermediaire/file-rate-limit.md) · [Supprimer un fichier](../files/welcome/intermediaire/file-delete.md) · [Assainir un nom de fichier](../files/welcome/avance/file-safe-name.md) · [Chemin anti-traversal](../files/welcome/avance/file-safe-path.md) · [Écrire des octets générés](../files/welcome/avance/file-bytes.md)

### Audio (opt-in `forge-mvc-audio`)

[Bonjour Forge Audio](../audio/welcome/debutant/audio-welcome.md) · [Téléverser un audio](../audio/welcome/debutant/audio-upload.md) · [Lire un audio](../audio/welcome/debutant/audio-play.md) · [Sonder un audio](../audio/welcome/avance/audio-probe.md) · [Transcoder en MP3](../audio/welcome/avance/audio-transcode.md) · [Diagnostiquer le module Audio](../audio/welcome/avance/audio-doctor.md)

### MFA (opt-in `forge-mvc-mfa`)

[Bonjour Forge MFA](../mfa/welcome/debutant/mfa-welcome.md) · [Secret TOTP et QR](../mfa/welcome/debutant/mfa-secret.md) · [Vérifier un code TOTP](../mfa/welcome/debutant/mfa-verify.md) · [Enrôler un facteur TOTP](../mfa/welcome/intermediaire/mfa-enroll.md) · [Challenge de connexion](../mfa/welcome/intermediaire/mfa-challenge.md) · [Codes de récupération](../mfa/welcome/intermediaire/mfa-recovery.md) · [Revalidation (step-up)](../mfa/welcome/avance/mfa-revalidation.md) · [Anti-rejeu TOTP](../mfa/welcome/avance/mfa-replay.md) · [Secret chiffré au repos](../mfa/welcome/avance/mfa-crypto.md)

### RBAC (opt-in `forge-mvc-rbac`)

[Bonjour Forge RBAC](welcome-rbac/debutant/rbac-welcome.md) · [Code de permission](welcome-rbac/debutant/rbac-permission.md) · [Rôle et slug](welcome-rbac/debutant/rbac-role.md) · [Vérifier une permission](welcome-rbac/intermediaire/rbac-check.md) · [Protéger une route](welcome-rbac/intermediaire/rbac-guard.md) · [Permission dans un template](welcome-rbac/intermediaire/rbac-template.md) · [Associer un rôle à un utilisateur](welcome-rbac/avance/rbac-user-role.md) · [Résoudre les permissions](welcome-rbac/avance/rbac-resolve.md) · [Rôles de la requête](welcome-rbac/avance/rbac-request-roles.md)

### Workflow (opt-in `forge-mvc-workflow`)

[Bonjour Forge Workflow](../workflow/welcome/debutant/workflow-welcome.md) · [Nom de statut](../workflow/welcome/debutant/workflow-status.md) · [Retrouver un statut](../workflow/welcome/debutant/workflow-find.md) · [Déclarer les transitions](../workflow/welcome/intermediaire/workflow-transition.md) · [Vérifier une transition](../workflow/welcome/intermediaire/workflow-check.md) · [Transitions disponibles](../workflow/welcome/intermediaire/workflow-available.md) · [Badge de statut](../workflow/welcome/avance/workflow-badge.md) · [Couleur, libellé, classe](../workflow/welcome/avance/workflow-color.md) · [Helpers Workflow dans Jinja](../workflow/welcome/avance/workflow-jinja.md)

### Stats (opt-in `forge-mvc-stats`)

[Bonjour Forge Stats](../stats/welcome/debutant/stats-welcome.md) · [Nom d'événement](../stats/welcome/debutant/stats-event.md) · [Le schéma SQL](../stats/welcome/debutant/stats-schema.md) · [Le SQL d'insertion](../stats/welcome/intermediaire/stats-track-sql.md) · [Enregistrer un événement](../stats/welcome/intermediaire/stats-track.md) · [Valider un événement](../stats/welcome/intermediaire/stats-validate.md) · [Le SQL de consultation](../stats/welcome/avance/stats-admin-sql.md) · [Lister les événements](../stats/welcome/avance/stats-list.md) · [Normaliser une ligne](../stats/welcome/avance/stats-normalize.md)

### Mail (opt-in `forge-mvc-mail`)

[Bonjour Forge Mail](../mail/welcome/debutant/mail-welcome.md) · [Composer un message](../mail/welcome/debutant/mail-message.md) · [Choisir un transport](../mail/welcome/intermediaire/mail-transport.md) · [Rendre un template](../mail/welcome/intermediaire/mail-template.md) · [Configurer l'envoi](../mail/welcome/avance/mail-config.md) · [Diagnostiquer le module Mail](../mail/welcome/avance/mail-doctor.md)

## Progression recommandée

Le niveau débutant `Bonjour Forge` est un **tutoriel continu** : vous
construisez à la main un seul projet qui grandit palier après palier (un
contrôleur qui s'enrichit, un `mvc/routes.py` qui s'accumule). **Ne sautez pas
directement aux notions SQL** : les paliers HTTP préparent l'accès base
sereinement. Les 11 paliers du niveau débutant :

1. **Bonjour Forge** : afficher une réponse texte avec `Response.text(...)`.
2. **Paramètres d'URL** : lire une valeur simple avec `request.query(...)`.
3. **Première vue HTML** : rendre une page avec `BaseController.render(...)`.
4. **Route dynamique** : lire un paramètre de route comme `/articles/{id}`.
5. **Inspecter une requête** : explorer `request.data` avec `Response.debug(...)` en développement.
6. **Réponse JSON** : retourner des données structurées avec `Response.json(...)`.
7. **Le jeton CSRF** : comprendre la protection CSRF des formulaires.
8. **Premier formulaire POST** : envoyer des données depuis un formulaire HTML.
9. **Validation serveur** : refuser ou accepter les données reçues.
10. **Première base SQL** : lire une donnée : MariaDB, migrations et SQL visible.
11. **Écrire en base** : insérer une ligne depuis un formulaire avec `db.insert(...)`.

Après le préambule d'installation, suivez les paliers dans l'ordre depuis
[Bonjour Forge](welcome-forge/debutant/welcome.md).

Une fois ces **11 paliers** acquis, vous avez terminé le niveau débutant de
découverte *Bonjour Forge*. Vous pouvez ensuite explorer les progressions
opt-in dédiées (IoT, vidéo, images, fichiers, audio, MFA, RBAC, workflow,
stats), chacune autonome et présentée par niveau dans le catalogue ci-dessus.

Le tableau de synthèse plus haut reste utile comme catalogue exhaustif
des starters disponibles aujourd'hui, mais l'ordre d'apprentissage
recommandé est celui des 11 paliers ci-dessus, suivi des progressions
opt-in de votre choix.

## Différence entre profil et starter

Un **profil** définit la base technique d'un projet créé avec `forge new`
(`forge new MonProjet --profile standard`). Un **starter** fournit un exemple
applicatif générable *après* la création du projet. Ils sont indépendants : un
profil ne remplace pas un starter, un starter ne modifie pas le profil, et un
starter peut illustrer un ou plusieurs profils.

Pour choisir un profil : [Profils de projet](../features/profiles.md).

## Utiliser un starter

Un starter se suit **à la main**, palier par palier.
Pour une progression opt-in, commencez par sa page d'installation (installer le module, disposer d'un projet Forge), puis enchaînez les paliers.
Chaque palier indique le contrôleur, la vue et la route à créer dans le projet.

!!! note "Les starters ne se génèrent pas"
    Forge ne génère pas les starters et n'écrit jamais dans votre `mvc/routes.py`.
    Vous créez vous-même chaque fichier et ajoutez chaque route, en suivant la documentation du palier (voir [ADR-035](../adr/035-starters-manual-not-generated.md)).
