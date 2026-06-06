# Starters Forge

<div style="border:1px solid #FED7AA;background:linear-gradient(135deg,#FFF7ED 0%,#FFFFFF 58%,#F8FAFC 100%);border-radius:18px;padding:1.5rem 1.6rem;margin:1rem 0 1.5rem 0;">
  <p style="margin:0 0 .35rem 0;font-size:.85rem;font-weight:700;color:#EA580C;text-transform:uppercase;letter-spacing:.08em;">Forge · Parcours applicatifs</p>
  <h2 style="margin:.1rem 0 .45rem 0;font-size:2rem;line-height:1.15;color:#0F172A;">Vue d'ensemble des starters</h2>
  <p style="margin:0;color:#334155;font-size:1.05rem;max-width:880px;">Des parcours progressifs pour apprendre Forge, reconstruire vite et adapter à un vrai projet.</p>
</div>

## Principe

Un **starter** Forge est un exemple applicatif générable avec `forge starter:build`.
Il fournit un point de départ fonctionnel pour comprendre une mécanique du
framework. Un starter n'est pas un profil — voir
[Différence entre profil et starter](#difference-entre-profil-et-starter).

Profils recommandés selon le starter : `minimal` ou `standard` pour les paliers
avec base de données, aucun profil pour les paliers sans base.

## Catalogue

La progression cœur `welcome-forge` enseigne les fondamentaux ; chaque opt-in a
sa propre progression `welcome-<module>` (débutant → avancé). La liste exhaustive
est aussi disponible via `forge starter:list`.

### Bonjour Forge — progression cœur (`welcome-forge`)

*Débutant — 11 paliers* — [Bonjour Forge](welcome-forge/debutant/welcome.md) · [Paramètres d'URL](welcome-forge/debutant/query-params.md) · [Première vue HTML](welcome-forge/debutant/first-html-view.md) · [Route dynamique](welcome-forge/debutant/dynamic-route.md) · [Inspecter une requête](welcome-forge/debutant/request-debug.md) · [Réponse JSON](welcome-forge/debutant/json-response.md) · [Le jeton CSRF](welcome-forge/debutant/csrf.md) · [Premier formulaire POST](welcome-forge/debutant/form-post.md) · [Validation serveur](welcome-forge/debutant/server-validation.md) · [Première base SQL](welcome-forge/debutant/first-sql.md) · [Écrire en base](welcome-forge/debutant/first-sql-write.md)

*Intermédiaire* — [Lister des enregistrements](welcome-forge/intermediaire/list-records.md) · [Rechercher / filtrer](welcome-forge/intermediaire/filter-list.md) · [Paginer une liste](welcome-forge/intermediaire/pagination.md) · [Héritage de gabarit](welcome-forge/intermediaire/layout-template.md) · [Modifier un enregistrement](welcome-forge/intermediaire/update-record.md) · [Supprimer un enregistrement](welcome-forge/intermediaire/delete-record.md) · [Mémoriser un état en session](welcome-forge/intermediaire/session-state.md) · [Messages flash](welcome-forge/intermediaire/flash-messages.md)

*Avancé* — [Relations entre tables](welcome-forge/avance/relations.md) · [Téléverser un fichier](welcome-forge/avance/file-upload.md) · [API JSON protégée](welcome-forge/avance/json-api.md) · [Écritures transactionnelles](welcome-forge/avance/db-transaction.md)

### IoT (opt-in `forge-mvc-iot`)

[Bonjour Forge IoT](welcome-iot/debutant/iot-welcome.md) · [Lire les événements IoT](welcome-iot/debutant/iot-events.md) · [Les événements d'un capteur](welcome-iot/debutant/iot-device.md) · [Simuler une mesure IoT](welcome-iot/intermediaire/iot-simulate.md) · [Exposer l'API IoT](welcome-iot/intermediaire/iot-api.md) · [Tableau de bord IoT](welcome-iot/intermediaire/iot-dashboard.md) · [Valider un message IoT](welcome-iot/avance/iot-contract.md) · [Le subscriber MQTT](welcome-iot/avance/iot-subscriber.md) · [Diagnostiquer le module IoT](welcome-iot/avance/iot-doctor.md)

### Vidéo (opt-in `forge-mvc-video`)

[Bonjour Forge Vidéo](welcome-video/debutant/video-welcome.md) · [Lister les vidéos](welcome-video/debutant/video-list.md) · [Le détail d'une vidéo](welcome-video/debutant/video-detail.md) · [Téléverser une vidéo](welcome-video/intermediaire/video-upload.md) · [Lire une vidéo](welcome-video/intermediaire/video-playback.md) · [Suivre l'état d'une vidéo](welcome-video/intermediaire/video-status.md) · [Sonder une vidéo](welcome-video/avance/video-probe.md) · [Transcoder une vidéo](welcome-video/avance/video-transcode.md) · [Diagnostiquer le module Vidéo](welcome-video/avance/video-doctor.md)

### Images (opt-in `forge-mvc-images`)

[Bonjour Forge Images](welcome-images/debutant/images-welcome.md) · [Téléverser une image](welcome-images/debutant/image-upload.md) · [Miniatures et variantes](welcome-images/debutant/image-variants.md) · [Rattacher une image à une entité](welcome-images/intermediaire/image-attach.md) · [Afficher la galerie](welcome-images/intermediaire/image-gallery.md) · [Texte alternatif et ordre](welcome-images/intermediaire/image-alt-order.md) · [Image de couverture](welcome-images/avance/image-cover.md) · [Supprimer proprement](welcome-images/avance/image-delete.md) · [Garde de sécurité à l'upload](welcome-images/avance/image-safety.md)

### Fichiers (opt-in `forge-mvc-files`)

[Bonjour Forge Files](welcome-files/debutant/files-welcome.md) · [Stocker un document](welcome-files/debutant/file-store.md) · [Servir un fichier](welcome-files/debutant/file-serve.md) · [Valider un upload](welcome-files/intermediaire/file-validate.md) · [Limiter les uploads](welcome-files/intermediaire/file-rate-limit.md) · [Supprimer un fichier](welcome-files/intermediaire/file-delete.md) · [Assainir un nom de fichier](welcome-files/avance/file-safe-name.md) · [Chemin anti-traversal](welcome-files/avance/file-safe-path.md) · [Écrire des octets générés](welcome-files/avance/file-bytes.md)

### Audio (opt-in `forge-mvc-audio`)

[Bonjour Forge Audio](welcome-audio/debutant/audio-welcome.md) · [Téléverser un audio](welcome-audio/debutant/audio-upload.md) · [Lire un audio](welcome-audio/debutant/audio-play.md) · [Sonder un audio](welcome-audio/avance/audio-probe.md) · [Transcoder en MP3](welcome-audio/avance/audio-transcode.md) · [Diagnostiquer le module Audio](welcome-audio/avance/audio-doctor.md)

### MFA (opt-in `forge-mvc-mfa`)

[Bonjour Forge MFA](welcome-mfa/debutant/mfa-welcome.md) · [Secret TOTP et QR](welcome-mfa/debutant/mfa-secret.md) · [Vérifier un code TOTP](welcome-mfa/debutant/mfa-verify.md) · [Enrôler un facteur TOTP](welcome-mfa/intermediaire/mfa-enroll.md) · [Challenge de connexion](welcome-mfa/intermediaire/mfa-challenge.md) · [Codes de récupération](welcome-mfa/intermediaire/mfa-recovery.md) · [Revalidation (step-up)](welcome-mfa/avance/mfa-revalidation.md) · [Anti-rejeu TOTP](welcome-mfa/avance/mfa-replay.md) · [Secret chiffré au repos](welcome-mfa/avance/mfa-crypto.md)

### RBAC (opt-in `forge-mvc-rbac`)

[Bonjour Forge RBAC](welcome-rbac/debutant/rbac-welcome.md) · [Code de permission](welcome-rbac/debutant/rbac-permission.md) · [Rôle et slug](welcome-rbac/debutant/rbac-role.md) · [Vérifier une permission](welcome-rbac/intermediaire/rbac-check.md) · [Protéger une route](welcome-rbac/intermediaire/rbac-guard.md) · [Permission dans un template](welcome-rbac/intermediaire/rbac-template.md) · [Associer un rôle à un utilisateur](welcome-rbac/avance/rbac-user-role.md) · [Résoudre les permissions](welcome-rbac/avance/rbac-resolve.md) · [Rôles de la requête](welcome-rbac/avance/rbac-request-roles.md)

### Workflow (opt-in `forge-mvc-workflow`)

[Bonjour Forge Workflow](welcome-workflow/debutant/workflow-welcome.md) · [Nom de statut](welcome-workflow/debutant/workflow-status.md) · [Retrouver un statut](welcome-workflow/debutant/workflow-find.md) · [Déclarer les transitions](welcome-workflow/intermediaire/workflow-transition.md) · [Vérifier une transition](welcome-workflow/intermediaire/workflow-check.md) · [Transitions disponibles](welcome-workflow/intermediaire/workflow-available.md) · [Badge de statut](welcome-workflow/avance/workflow-badge.md) · [Couleur, libellé, classe](welcome-workflow/avance/workflow-color.md) · [Helpers Workflow dans Jinja](welcome-workflow/avance/workflow-jinja.md)

### Stats (opt-in `forge-mvc-stats`)

[Bonjour Forge Stats](welcome-stats/debutant/stats-welcome.md) · [Nom d'événement](welcome-stats/debutant/stats-event.md) · [Le schéma SQL](welcome-stats/debutant/stats-schema.md) · [Le SQL d'insertion](welcome-stats/intermediaire/stats-track-sql.md) · [Enregistrer un événement](welcome-stats/intermediaire/stats-track.md) · [Valider un événement](welcome-stats/intermediaire/stats-validate.md) · [Le SQL de consultation](welcome-stats/avance/stats-admin-sql.md) · [Lister les événements](welcome-stats/avance/stats-list.md) · [Normaliser une ligne](welcome-stats/avance/stats-normalize.md)

### Mail (opt-in `forge-mvc-mail`)

[Bonjour Forge Mail](welcome-mail/debutant/mail-welcome.md) · [Composer un message](welcome-mail/debutant/mail-message.md) · [Choisir un transport](welcome-mail/intermediaire/mail-transport.md) · [Rendre un template](welcome-mail/intermediaire/mail-template.md) · [Configurer l'envoi](welcome-mail/avance/mail-config.md) · [Diagnostiquer le module Mail](welcome-mail/avance/mail-doctor.md)

## Progression recommandée

Le starter `Bonjour Forge` est volontairement minimal (deux routes texte,
zéro vue HTML, zéro base de données). **Ne sautez pas directement aux
notions SQL** : plusieurs paliers intermédiaires permettent d'aborder
l'accès base sereinement. La progression officielle est :

1. **Bonjour Forge** — afficher une réponse texte avec `Response.text(...)`.
   *(livré — starter `welcome`)*
2. **Paramètres d'URL** — lire une valeur simple avec `request.param(...)`.
   *(livré — starter `query-params`, ticket `STARTER-QUERY-PARAMS-001`)*
3. **Première vue HTML** — rendre une page avec `BaseController.render(...)`.
   *(livré — starter `first-html-view`, ticket `STARTER-FIRST-HTML-VIEW-001`)*
4. **Route dynamique** — lire un paramètre de route comme `/articles/{id}`.
   *(livré — starter `dynamic-route`, ticket `STARTER-DYNAMIC-ROUTE-001`)*
5. **Inspecter une requête** — explorer `request.data` avec `Response.debug(...)` en développement.
   *(livré — starter `request-debug`, ticket `STARTER-REQUEST-DEBUG-001`)*
6. **Réponse JSON** — retourner des données structurées avec `Response.json(...)`.
   *(livré — starter `json-response`, ticket `STARTER-JSON-RESPONSE-001`)*
7. **Le jeton CSRF** — comprendre la protection CSRF des formulaires.
   *(livré — starter `csrf`, ticket `STARTER-CSRF-001`)*
8. **Premier formulaire POST** — envoyer des données depuis un formulaire HTML.
   *(livré — starter `form-post`, ticket `STARTER-FORM-POST-001`)*
9. **Validation serveur** — refuser ou accepter les données reçues.
   *(livré — starter `server-validation`, ticket `STARTER-SERVER-VALIDATION-001`)*
10. **Première base SQL** — lire une donnée : MariaDB, migrations et SQL visible.
   *(livré — starter `first-sql`, ticket `STARTER-FIRST-SQL-001`)*
11. **Écrire en base** — insérer une ligne depuis un formulaire avec `db.insert(...)`.
   *(livré — starter `first-sql-write`, ticket `STARTER-FIRST-SQL-WRITE-001`)*

Une fois ces **11 paliers** acquis, vous avez terminé le starter de
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

```bash
forge starter:list                 # catalogue complet depuis la CLI
forge starter:build <identifiant>  # ex. : forge starter:build welcome
```

Un starter se génère par son **identifiant public** (`welcome`, `query-params`,
`iot-welcome`…), pas par un numéro. Chaque page de starter liste les commandes
exactes, le modèle de données et les étapes de reconstruction.
