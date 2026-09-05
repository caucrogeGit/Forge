# Roadmap Forge 1.0.0-rc.8 - Amélioration des opt-ins

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette roadmap cadre le cycle rc8, dernier cycle avant la 1.0.0 stable.
Elle couvre les vingt-quatre axes d'amélioration relevés sur les opt-ins et sur les backends.

Le périmètre est fixé.
Tous les tickets listés ici sont à livrer avant le tag stable.

> **Statut** : cadrage validé, exécution en cours.
> Version de départ : 1.0.0rc7.

---

## 1. Pourquoi cette roadmap existe

Une revue des vingt-sept paquets a produit une liste d'améliorations par opt-in.
Confrontée au dépôt, cette liste s'est révélée partiellement périmée.

Seize améliorations demandées étaient déjà livrées.
Le cas le plus net est `forge-mvc-admin`, décrit comme un paquet vide alors qu'il porte 1259 lignes et dix fichiers de test.

L'erreur ne venait pas de la revue mais du dépôt.
Le README du paquet et sa roadmap de cadrage affirmaient tous deux qu'aucun code n'existait.

C'est le deuxième motif du pré-mortem rc7, la documentation qui affirme ce que le code ne fait plus.
Ce cycle commence donc par rétablir la vérité avant d'ajouter quoi que ce soit.

---

## 2. Ce qui était déjà livré

Ces seize points sont retirés du périmètre.
Ils sont consignés ici pour que la prochaine revue ne les redemande pas.

| Opt-in | Amélioration demandée | Où elle vit déjà |
|---|---|---|
| admin | CRUD générique, auth, CSRF, RBAC, pagination | `registry.py`, `resources.py`, `query.py`, `http.py` |
| entities | Suppression logique déclarée au contrat | ADR-083, `field_resolver.py`, `entity.schema.json` |
| mfa | Chiffrement du secret TOTP au repos | `secret_crypto.py`, `SEC-MFA-SECRET-ENCRYPTION-001` |
| mfa | Limitation de débit sur le challenge | `AUTH_RATE_LIMIT_MFA_CHALLENGE`, cinq essais |
| sessions-db | Purge planifiable | commande `sessions:gc` |
| jobs | Réessai avec délai | `backoff_seconds`, dix secondes à six cents |
| notifications | Tout marquer comme lu | `mark_all_read`, `unread_count` |
| notifications | Types de notification déclarés | colonne `type` |
| images | Variantes nommées | `IMAGE_VARIANT_SIZES` |
| video | Vignette automatique et métadonnées | `poster_path`, `duration_seconds`, `width`, `height` |
| video | Suivi d'état | `uploaded`, `processing`, `ready`, `failed` |
| mail | Journal des envois en base | table `mail_log`, commande `mail:logs` |
| settings | Typage déclaré | colonne `value_type` |
| audit | Rétention configurable et purge | `purge_audit_before`, commande `audit:gc` |
| stats | Agrégations SQL | `aggregate.py`, `get_stats_counts_sql` |
| qrcode | Aide contrôleur | `QrCodeResponse.from_text` |
| fixtures | Refus de charger en production sans `--force` | ADR-074, `load.py`, `purge.py` |

---

## 3. Lot 0 - Rétablir la vérité

Ce lot passe en premier.
Il est petit, et il empêche la prochaine revue de repartir d'un état faux.

| Ticket | Responsabilité unique |
|---|---|
| `ADMIN-DOC-ETAT-REEL-001` | **Livré.** Le README annonçait « à venir » des filtres livrés et des actions groupées désormais livrées |
| `META-README-COMMANDS-RATCHET-001` | **Livré.** Refuse une commande promise et absente, et une commande livrée annoncée « à venir » |

---

## 4. Lot 1 - Sécurité et pertes de données

Ces tickets corrigent des manques qui produisent une panne ou une fuite.
Ils passent avant tout ajout de confort.

| Ticket | Responsabilité unique |
|---|---|
| ~~`FIXTURES-APP-ENV-GUARD-001`~~ | **Retiré, faux besoin.** La garde existait déjà (ADR-074). Remplacé par `ENV-APP-ENV-NORMALISATION-001`, qui corrige la vraie faille, la casse qui la désarmait |
| `ENV-APP-ENV-NORMALISATION-001` | **Livré.** Lecture unique et normalisée de `APP_ENV` dans `core.app.env` |
| `MFA-KEY-ROTATION-001` | **Livré.** `FORGE_MFA_SECRET_KEY_PREVIOUS`, `rotate_totp_secret`, `uses_current_key` |
| `SESSIONS-DELETE-FOR-USER-001` | **Livré.** `delete_for_user` au contrat et aux trois stores, plus `AddColumn` pour faire évoluer un schéma d'opt-in |
| `MFA-SESSION-INVALIDATION-001` | **Livré.** `except_session_id` épargne la session courante, geste documenté et exercé |
| `IOT-RETENTION-GC-001` | **Livré.** `iot:gc --days N`, nommé comme les trois autres purges et non `iot:purge` |
| `DEPLOY-CHECK-SECRETS-001` | **Livré.** Repérage par nom de variable, valeur jamais affichée, liste partagée dans `core.security.secrets` |
| `FILES-METADATA-TABLE-001` | **Livré.** Table `forge_files` et registre explicite, ADR-094 amendant l'ADR-020 |

---

## 5. Lot 2 - Socles dont d'autres tickets dépendent

| Ticket | Responsabilité unique |
|---|---|
| `I18N-LOCALE-DETECTION-001` | **Livré.** `detect_locale`, liste blanche obligatoire, négociation par facteurs de qualité |
| `JOBS-PRIORITY-001` | **Livré.** `priority DESC, id`, niveaux nommés, `AddColumn` étendu aux index composites |
| `JOBS-STATUS-CLI-001` | **Livré.** Compteurs par file, colonne « prêtes » distincte de « en attente », lecture seule |
| `ADMIN-LIST-FILTERS-001` | **Livré.** Déclaration obligatoire, noms vérifiés en liste blanche, `ORDER BY` portable |
| `ENTITIES-UNIQUE-COMPOSITE-001` | **Livré.** Les index déclarés atteignent le SQL, contrainte nommée, doublon refusé sur serveurs réels |
| `RBAC-INSTANCE-PERMISSIONS-001` | **Livré.** `has_instance_permission`, ordre global puis propriétaire, composition et non quatrième niveau |
| `WORKFLOW-HOOKS-001` | **Livré.** `apply_transition`, veto par exception, `commit` fourni par l'application |
| `DB-DOCTOR-001` | **Livré.** Enrichit `forge doctor` plutôt que d'ouvrir `db:doctor` (principe 11) : version, encodage, base, compte |

---

## 6. Lot 3 - Compositions entre opt-ins

Ces tickets branchent des opt-ins les uns sur les autres.
Chacun dépend d'un ticket du lot 2.

| Ticket | Dépend de | Responsabilité unique |
|---|---|---|
| `MAIL-QUEUE-VIA-JOBS-001` | jobs | **Livré.** `MAIL_JOB_TASK`, sérialisation JSON, gestionnaire ; aucune dépendance croisée |
| `IMPEXP-ASYNC-JOBS-001` | jobs | **Livré.** Importeurs nommés, racine de chemins obligatoire, lignes invalides non fatales |
| `RBAC-DENIAL-AUDIT-001` | audit | **Livré.** Les 3 gardes annoncent, observateurs isolés, aucune dépendance croisée |
| `AUDIT-CSV-EXPORT-001` | import-export | **Livré.** Export non borné, curseur par identifiant, aucune dépendance croisée |
| `NOTIF-MAIL-BRIDGE-001` | mail, jobs | **Livré.** `on_notification_created`, relais isolés, pont à trois paquets sans dépendance |
| `ADMIN-SETTINGS-UI-001` | admin | **Livré.** Conversion de saisie explicite, forme renvoyable, aucune dépendance au back-office |
| `ADMIN-SESSIONS-VIEW-001` | admin | **Livré.** `list_for_user` sur les 3 stores, résumé sans jeton, préfixe non révocable |
| `WORKFLOW-ENTITY-STATUS-001` | entities | **Livré.** Le contrat devient la source, champ nommé jamais deviné, aucune dépendance |

---

## 7. Lot 4 - Complétude par opt-in

### 7.1 admin

| Ticket | Responsabilité unique |
|---|---|
| `ADMIN-BULK-ACTIONS-001` | **Livré.** Suppression et transitions groupées, câblées de la case à cocher au workflow. La première livraison n'avait posé que la fonction de requête, inatteignable depuis le back-office |

### 7.2 entities

| Ticket | Responsabilité unique |
|---|---|
| `ENTITIES-COMPUTED-FIELDS-001` | **Livré.** Projetés par leur expression, absents des écritures ; quatre combinaisons refusées |
| `ENTITIES-BUSINESS-VALIDATION-001` | **Livré.** Fonction enregistrée, pas de mini-langue ; toutes les règles évaluées |
| `ENTITIES-SLUG-ROUTES-001` | **Livré.** La recherche existait, la route non ; déclarée en dernier |
| `ENTITIES-MIGRATION-DIFF-READABLE-001` | **Livré.** Résumé, `--sql` sans écrire, `--check` pour la CI |

### 7.3 rbac

| Ticket | Responsabilité unique |
|---|---|
| `RBAC-CONTRACT-EXPORT-001` | **Livré.** Markdown et CSV ; rend le contrat, jamais l'état de la base |

### 7.4 workflow

| Ticket | Responsabilité unique |
|---|---|
| `WORKFLOW-HISTORY-001` | **Livré.** Table dédiée ; enregistrement explicite, dans la transaction de l'appelant |
| `WORKFLOW-CONDITIONS-001` | **Livré.** Une condition dit pourquoi elle refuse ; une panne refuse |

### 7.5 mfa

| Ticket | Responsabilité unique |
|---|---|
| `MFA-REQUIRED-BY-ROLE-001` | **Livré.** Trois emplacements de rôles lus ; ne lève jamais, n'active rien |

### 7.6 sessions-db

| Ticket | Responsabilité unique |
|---|---|
| `SESSIONS-TTL-PER-KIND-001` | **Livré.** Trois natures fermées ; valeur illisible refusée |
| `SESSIONS-ACTIVE-METRIC-001` | **Livré.** Filtre en SQL ; une session expirée n'est pas active |
| `SESSIONS-GC-TIMER-DOC-001` | **Livré.** Deux unités, `Persistent`, dispersion, et le piège du `.service` |

### 7.7 jobs

| Ticket | Responsabilité unique |
|---|---|
| `JOBS-IDEMPOTENCY-KEY-001` | **Livré.** Index unique dialectal : SQL Server n'accepte qu'un seul NULL |
| `JOBS-HEARTBEAT-001` | **Livré.** `heartbeat(claim_token)`, gardé par le jeton |
| `DOC-JOBS-COMPOSITION-001` | **Livré.** Tableau des motifs, et ce qui doit faire échouer une tâche |

### 7.8 mail

| Ticket | Responsabilité unique |
|---|---|
| `MAIL-ATTACHMENTS-001` | **Livré.** Message immuable, nom de fichier assaini, type jamais deviné faux |
| `MAIL-TEST-GUIDED-001` | **Livré.** `--dry-run`, diagnostic avant l'envoi |
| `MAIL-LAYOUTS-001` | **Livré.** Faux besoin : l'héritage Jinja marchait déjà ; capacité figée par des tests et documentée |

### 7.9 notifications

| Ticket | Responsabilité unique |
|---|---|
| `NOTIF-TARGET-URL-001` | **Livré.** Colonne dédiée validée à l'écriture, schémas exécutables refusés |
| `NOTIF-PAGINATION-001` | **Livré.** Curseur `before_id`, jamais d'`OFFSET` |
| `NOTIF-HTTP-ROUTES-001` | **Livré** hors cycle, voir section 11. Quatre routes JSON, destinataire résolu par l'application et jamais lu dans la requête |

### 7.10 files

| Ticket | Responsabilité unique |
|---|---|
| `FILES-QUOTA-001` | **Livré.** Par couple propriétaire, valeur d'env illisible refusée, fenêtre de concurrence documentée |
| `FILES-SCAN-HOOK-001` | **Livré.** Consultée avant écriture, une panne refuse le dépôt au lieu de le laisser passer |
| `FILES-ORPHAN-PURGE-001` | **Livré.** Deux sortes d'orphelins, registre vide et fichier récent interrompent |
| `DOC-FILES-XACCEL-001` | **Livré.** Motif documenté, `internal;` posé comme la moitié qui protège |

### 7.11 images

| Ticket | Responsabilité unique |
|---|---|
| `IMAGES-PRESETS-DECLARATIFS-001` | **Livré.** `IMAGE_VARIANTS`, lus à chaque appel, nom réservé et doublon refusés |
| `IMAGES-FOCAL-CROP-001` | **Livré.** Fenêtre recalée dans l'image, aucun pixel inventé |
| `IMAGES-ORPHAN-VARIANTS-001` | **Livré.** Deux catégories, sans base ; `images:orphans` affiche puis supprime |
| `IMAGES-ENTITY-FIELD-001` | **Livré.** `variants` accepte une liste ; nom non déclaré refusé à la génération |
| `IMAGES-LIMITS-CONFIG-001` | **Livré.** Largeur, hauteur et poids ; valeur illisible refusée |

### 7.12 video

| Ticket | Responsabilité unique |
|---|---|
| `VIDEO-STATUS-UI-001` | **Livré.** Vue d'état, route JSON ; la sortie ffmpeg ne sort jamais |
| `VIDEO-QUOTA-001` | **Livré.** Les limites par fichier existaient ; les plafonds **cumulés** manquaient |
| `VIDEO-SUBTITLES-001` | **Livré.** Table dédiée, WebVTT seul, signature vérifiée à l'entrée |

### 7.13 audio

| Ticket | Responsabilité unique |
|---|---|
| `AUDIO-ID3-001` | **Livré.** ffprobe les rendait déjà ; nettoyées, elles viennent du fichier envoyé |
| `AUDIO-TRIM-001` | **Livré.** `audio:trim` ; ni la source ni une sortie existante ne sont écrasées |
| `AUDIO-DOCTOR-HARMONISE-001` | **Livré. Faux besoin** : déjà alignés. Garde-fou posé, et la vraie divergence corrigée (config) |

### 7.14 iot

| Ticket | Responsabilité unique |
|---|---|
| `IOT-DEVICE-AUTH-001` | **Livré.** Le jeton unique ouvrait TOUS les sites ; portées, empreintes, révocation |
| `IOT-AGGREGATES-001` | **Livré.** En SQL, fenêtre vide distincte d'une moyenne nulle |
| `IOT-RBAC-READ-001` | **Livré.** Prise, pas dépendance ; une vérification en panne refuse |

### 7.15 import-export

| Ticket | Responsabilité unique |
|---|---|
| `IMPEXP-COLUMN-MAPPING-001` | **Livré.** `source` déclaré ; colonne absente = 1 erreur, plus 10 000 |
| `IMPEXP-ERROR-REPORT-001` | **Livré.** CSV échappé, ligne tableur et valeur refusée |
| `IMPEXP-FILTERED-EXPORT-001` | **Livré. Faux besoin** : les filtres passaient déjà. La **troncature silencieuse** corrigée |
| `IMPEXP-JSONL-001` | **Livré.** Types préservés, clé absente à `null`, lecture stricte par défaut |

### 7.16 fixtures

| Ticket | Responsabilité unique |
|---|---|
| `FIXTURES-SCENARIOS-001` | **Livré.** Sous-dossiers ; un nom inconnu lève au lieu de charger zéro |
| `FIXTURES-SNAPSHOT-001` | **Livré.** Affiche d'abord, refuse en prod, plafond bas, en-tête qui prévient |
| `FIXTURES-FK-ORDER-ROBUST-001` | **Livré.** Toutes les tables d'un fichier ; le repli est dit, plus silencieux |

### 7.17 settings

| Ticket | Responsabilité unique |
|---|---|
| `SETTINGS-PER-USER-001` | **Livré.** Préfixe `user.` réservé, collision refusée, pas de repli sur le global |
| `SETTINGS-CACHE-001` | **Livré.** Éteint par défaut, invalidation explicite, absence mise en cache |
| `DOC-SETTINGS-NO-SECRETS-001` | **Livré.** Limite tracée, et pourquoi chiffrer la table ne résoudrait rien |

### 7.18 audit

| Ticket | Responsabilité unique |
|---|---|
| `AUDIT-FILTERS-001` | **Livré.** Les 4 filtres d'égalité existaient ; période ajoutée, date de fin incluant la journée |
| `AUDIT-ACTION-HELPER-001` | **Livré.** `record_request_audit`, acteur pris en session, jamais bloquant |

### 7.19 stats

| Ticket | Responsabilité unique |
|---|---|
| `STATS-IP-ANONYMISATION-001` | **Livré.** Aucune adresse n'était stockée ; `metadata` était la porte, elle est fermée |
| `STATS-EVENT-KIND-001` | **Livré.** Vocabulaire fermé, colonne `kind`, migration additive |
| `DOC-STATS-AGGREGATES-001` | **Livré.** L'agrégation par jour n'existait pas ; `Dialect.date_expression` la porte |

### 7.20 qrcode

| Ticket | Responsabilité unique |
|---|---|
| `QRCODE-CLI-001` | **Livré.** Affiche puis écrit ; n'écrase jamais, refuse une extension contradictoire |
| `QRCODE-ERROR-LEVEL-001` | **Livré.** Il existait sur le générateur, la réponse HTTP ne le transmettait pas |

### 7.21 i18n

| Ticket | Responsabilité unique |
|---|---|
| `I18N-EXTRACT-CLI-001` | **Livré.** Le cas que `i18n:check` ne peut pas voir ; clé calculée comptée à part |
| `I18N-MISSING-KEYS-DEV-001` | **Livré.** Journal et registre hors prod, une fois par clé, sans jamais lever |
| `I18N-PLURALS-001` | **Livré.** Deux formes ; les langues qui en demandent plus **lèvent** au lieu de mentir |

### 7.22 deploy

| Ticket | Responsabilité unique |
|---|---|
| `DEPLOY-NGINX-MEDIA-HEADERS-001` | **Livré.** HSTS que le cœur délègue au proxy, `nosniff` sur `/static/`, `internal;` |
| `DEPLOY-TIMERS-DOC-001` | **Livré.** Deux unités complètes et quatre pièges nommés |

### 7.23 backends

| Ticket | Responsabilité unique |
|---|---|
| `DB-ERROR-MESSAGES-HOMOGENES-001` | **Livré.** La clé étrangère n'était pas qualifiée ; vérifié sur les quatre serveurs |
| `DOC-DIALECT-ECARTS-001` | **Livré.** Bornes, booléens, insertion conditionnelle, erreurs, et ce qui reste hors contrat |

### 7.24 testing

| Ticket | Responsabilité unique |
|---|---|
| `TESTING-CLIENT-001` | **Livré.** Passe par le vrai callable WSGI, pas par un jumeau |
| `TESTING-LOGIN-AS-001` | **Livré.** Vrai magasin de sessions ; `logout` détruit vraiment |
| `TESTING-FIXTURES-ALIGN-001` | **Livré.** Réutilise le code du paquet, pas une seconde implémentation |
| `TESTING-ASSERTIONS-001` | **Livré.** Messages qui nomment la cause ; la rotation exige l'ancienne morte |

---

## 8. Lot 5 - Tickets en tension avec la charte

Ces cinq tickets sont demandés, et chacun entre en tension avec un principe.
La tension est nommée ici pour être tranchée en connaissance de cause, non pour bloquer la livraison.

| Ticket | Tension | Décision |
|---|---|---|
| `MFA-WEBAUTHN-001` | Principe 8, le facteur TOTP suffit au socle et la charge de maintenance est durable | **Retiré du périmètre** |
| `RBAC-ROLE-HIERARCHY-001` | Limite assumée par l'ADR-014, la rouvrir élargit le contrat public | **Livré**, ADR-095 |
| `AUDIO-STATEFUL-OPTION-001` | Principe 11, une seconde façon de gérer un média avec état existe déjà dans video | **Retiré du périmètre** |
| `DEPLOY-CADDY-001` | Principe 11, deux serveurs frontaux officiels au lieu d'un | **Retiré du périmètre** |
| `NOTIF-POLLING-HELPER-001` | Principe 1, le rafraîchissement d'interface relève de l'application | **Retiré du périmètre** |

### Décisions écrites, 2026-09-03

Roger a tranché les cinq en connaissance de cause, comme ce lot le prévoyait.
Un ticket est livré, quatre sont retirés du périmètre.
Le critère de clôture du cycle admet le retrait par décision écrite, et ces paragraphes en tiennent lieu.

**`RBAC-ROLE-HIERARCHY-001`, livré.**
La tension était réelle mais bornée : la fonction est petite, la demande est constante, et l'ADR-014 citait déjà l'héritage de permissions comme relevant d'un contrat RBAC.
La limite levée était une limite d'implémentation, non une frontière de conception.
L'élargissement du contrat public est cadré par l'[ADR-095](../adr/095-rbac-role-hierarchy.md).

**`MFA-WEBAUTHN-001`, retiré.**
WebAuthn est une spécification large et mouvante, qui demande une bibliothèque à suivre, une gestion d'attestation, et des contournements par navigateur.
Le principe 8 vise exactement cette charge : un noyau minimal ne porte pas ce que sa maintenance ne peut pas garantir sur la durée.
Le facteur TOTP couvre le socle, et une application qui a besoin de WebAuthn l'implémente avec une bibliothèque dédiée, sans que Forge prétende le faire à sa place.

**`AUDIO-STATEFUL-OPTION-001`, retiré.**
Une seconde façon de gérer un média avec état existe déjà dans `forge-mvc-video`, et le principe 11 en veut une seule.
Si le besoin revient, la bonne réponse n'est pas de dupliquer la machinerie dans `audio` mais de l'**extraire** en socle partagé.
C'est un ticket d'architecture, à instruire quand deux besoins indépendants l'auront demandé, pas une option à ajouter aujourd'hui.

**`DEPLOY-CADDY-001`, retiré.**
Un second gabarit officiel doit être maintenu, testé et tenu à jour au même rythme que le premier, et le principe 11 refuse deux façons officielles de faire la même chose.
La documentation peut nommer Caddy comme alternative viable sans que Forge en engendre la configuration : dire qu'une chose est possible ne coûte rien, la maintenir coûte à chaque version.

**`NOTIF-POLLING-HELPER-001`, retiré.**
Le rafraîchissement d'un écran relève de l'application, principe 1.
Forge livre déjà HTMX, avec lequel un rafraîchissement périodique tient en un attribut.
Ajouter un assistant ne retirerait aucune décision à l'application, il en masquerait une.

Ce motif portait une **affirmation fausse**, corrigée ici.
Il disait que « la route JSON que l'aide aurait appelée existe déjà côté notifications », et le paquet n'exposait alors aucune route.
Le retrait tient, la marche manquante n'était pas l'assistant mais la route, livrée par `NOTIF-HTTP-ROUTES-001` (section 11).

---

## 9. Compte et ordonnancement

| Lot | Tickets |
|---|---|
| Lot 0, vérité | 2 |
| Lot 1, sécurité et pertes | 6 |
| Lot 2, socles | 8 |
| Lot 3, compositions | 8 |
| Lot 4, complétude | 56 |
| Lot 5, tension | 5 |
| **Total** | **85** |

L'ordre des lots est une contrainte, pas une préférence.
Un ticket du lot 3 ne peut pas être livré avant le ticket du lot 2 dont il dépend.

À l'intérieur d'un lot, l'ordre est libre.

---

## 10. Critères de clôture du cycle

Le cycle rc8 est clos quand les six conditions suivantes sont vraies.

- Les quatre-vingt-cinq tickets sont livrés ou explicitement retirés du périmètre par décision écrite.
- La suite complète passe, marqueurs `docs` compris.
- `mkdocs build --strict` passe.
- Chaque paquet touché voit sa documentation embarquée mise à jour dans le même commit que le code.
- Aucun README d'opt-in ne décrit un état antérieur à son code, garde-fou `META-README-COMMANDS-RATCHET-001` vert.
- Le `CHANGELOG.md` porte une entrée par ticket livré.

---

## 11. Après la clôture

Le cycle est clos, et cette section recueille ce que sa revue a fait apparaître ensuite.

Elle n'en rouvre pas le périmètre.
Chaque entrée nomme ce qui l'a révélée, parce qu'un ticket sans cause visible se relit mal.

| Ticket | Paquet | Révélé par | État |
|---|---|---|---|
| `ADMIN-BULK-ACTIONS-001`, câblage | admin | Revue de la proposition admin | **Livré.** La première livraison n'avait posé que la fonction de requête, inatteignable depuis le back-office |
| `ADMIN-DOC-ETAT-REEL-001` | admin | Même revue | **Livré.** Le README annonçait « à venir » des capacités déjà présentes |
| `NOTIF-HTTP-ROUTES-001` | notifications | Besoin d'asynchrone d'une application réelle | **Livré.** Quatre routes JSON, marquage borné au destinataire |
| `JOBS-WORKER-GRACEFUL-STOP-001` | jobs | Écriture de l'unité systemd du worker | **Livré.** `stop` était sans effet sur une file chargée |
| `DEPLOY-JOBS-WORKER-UNIT-001` | deploy | Mesure des besoins d'asynchrone | **Livré.** Le worker n'existait nulle part sur le chemin de production |
| `DEPLOY-CHECK-JOBS-WORKER-001` | deploy | Même mesure | **Livré.** Le pré-vol ne regardait pas si quelqu'un traitait la file |
| `DEPLOY-NGINX-RATE-LIMIT-001` | deploy | Même mesure | **Livré.** La parade prescrite n'était pas dans la configuration engendrée |
| `MFA-RATE-LIMIT-SHARED-STORE-001` | mfa | Même mesure | **Retiré du périmètre**, voir ci dessous |
| `DB-POOL-THREADS-DOC-001` | cœur | Même mesure | **Livré.** Ce que devient la base quand une requête ouvre des threads |
| `META-DOC-ABSOLUTE-LINKS-001` | méta | Un lien cassé accepté par le build strict | **Livré.** Les liens absolus échappaient à `mkdocs --strict` |
| `META-README-RATCHET-WIDEN-001` | méta | Dix paquets sur vingt-sept sautés | **Livré.** Le cliquet ne lisait ni les blocs de code ni les citations nues, et sa règle était fausse |
| `SKELETON-TAILWIND-CSS-STALE-001` | squelette | Enquête sur le coût de `forge new` | **Livré.** Le CSS versionné manquait quinze classes de ses propres gabarits |
| `FORGE-NEW-NO-NODE-DEFAULT-001` | CLI | Même enquête | **Livré.** `forge new` passe de 144 s à 5,3 s ; `--with-node` pour l'ancien comportement |
| `ENTITIES-COMPUTED-CANONICAL-001` | entities | Revue du référentiel entities | **Livré.** Les champs calculés n'étaient déclarables que dans le format interne ; le normaliseur perdait l'expression en silence |
| `RBAC-DENIAL-AUDIT-COMPLETE-001` | rbac | Revue du référentiel rbac | **Livré.** L'audit des refus couvrait 3 gardes sur 5, et manquait la canonique |
| `WORKFLOW-CONDITIONS-APPLIED-001` | workflow | Revue du référentiel workflow | **Livré.** `apply_transition` ne consultait pas le registre de conditions |
| `OPTINS-MATURITY-FOLLOWS-CORE-001` | tous | Consigne : plus aucun opt-in en bêta | **Livré.** Dix fichiers s'attribuaient un stade propre, dont des affirmations fausses sur le MFA |
| `PKG-PYRIGHT-FIXTURES-001` | fixtures | Relecture du `pyproject.toml` racine | **Livré.** Le paquet n'était vérifié par aucun typage, alors que ses dix fichiers portent `# pyright: strict` |
| `SESSIONS-TTL-AUTHENTICATED-APPLIED-001` | sessions-db | Revue du référentiel sessions-db | **Livré.** `SESSION_TTL_AUTHENTICATED` était sans effet : `ttl_for()` n'était lue que par `create()` |
| `ADMIN-SESSIONS-VIEW-001` | admin | Même revue | **Livré.** La métrique existait, l'écran non ; couplage souple, aucun identifiant exposé |
| `JOBS-HEARTBEAT-REACHABLE-001` | jobs | Revue du référentiel jobs | **Livré.** Le gestionnaire ne recevait pas son jeton ; l'exemple documenté cassait la tâche |
| `MAIL-QUEUE-ATTACHMENTS-REFUSED-001` | mail | Revue du référentiel mail | **Livré.** Pièces jointes et file ne composaient pas ; la pièce disparaissait en silence |
| `IMAGES-REGISTRY-RECORD-001` | images, files | Revue du référentiel files | **Livré.** `files:orphans --delete` supprimait les images et leurs vignettes |
| `NOTIF-STORE-AS-VALIDATED-001` | notifications | Revue du référentiel notifications | **Livré.** Destinataire validé élagué et stocké brut : notification écrite, jamais relue |
| `DOC-FILES-RETENTION-SCOPE-001` | files | Revue du référentiel files, deuxième passe | **Livré.** L'absence de purge par ancienneté était silencieuse ; elle est motivée et le chemin applicatif donné |
| `FILES-DELETE-FORGETS-001` | files, images | Revue du référentiel images | **Livré.** Trois chemins de suppression laissaient la ligne au registre ; le quota comptait des fichiers supprimés |

**`NOTIF-HTTP-ROUTES-001`.**
Le paquet savait écrire une notification et la relire depuis Python, et n'exposait aucune route.
`forge-mvc-video` livre `register_video_routes`, `forge-mvc-iot` livre `register_iot_routes`, celui ci ne livrait rien.

Chaque application devait donc écrire son contrôleur, sa sérialisation et son compteur de non-lus avant d'afficher quoi que ce soit.
Mesuré sur une application réelle, elle appelait `notify()` depuis des mois sans avoir jamais affiché une seule notification, ayant buté sur cette marche.

Le point qui décide de tout le reste est le destinataire.
Il est résolu par l'application, jamais lu dans la requête, et l'absence du résolveur empêche l'enregistrement des routes.

Le marquage est borné au même destinataire, ce qui a demandé d'ajouter `recipient` à `mark_read` avant d'exposer quoi que ce soit.
Sans cette borne, l'identifiant seul suffisait à faire disparaître l'alerte de quelqu'un d'autre.

**`MFA-RATE-LIMIT-SHARED-STORE-001`, retiré.**
Je l'avais proposé, puis mesuré, et la mesure a renversé la recommandation.

Le compteur de tentatives vit en mémoire de processus, et vaut donc `5 × N` travailleurs.
La conclusion semblait couler de source : livrer un magasin partagé adossé à la base, sur le modèle de `DbTotpReplayStore`.

Trois faits s'y opposent.

Le premier est que la parade tient ailleurs, et mieux.
Une fois `limit_req` posé au proxy, cinq POST par minute et par IP, le nombre de travailleurs ne change plus rien à ce qu'un attaquant peut tenter à travers lui.
Le multiplicateur devient inatteignable, et il l'est pour la connexion comme pour le challenge.

Le deuxième est que la couture existe déjà.
`check_auth_rate_limit` accepte une liste de tentatives chargée d'où l'application veut : celle qui exige un compteur applicatif partagé peut l'écrire sans que Forge grossisse.

Le troisième est le principe 8.
Un protocole, une table, une migration et un magasin de plus dans un chemin de sécurité coûtent à chaque version, pour un besoin qui est une hypothèse de ma part et non un retour de terrain.
C'est la règle des deux occurrences indépendantes, celle qui a écarté quatre tickets du lot 5.

La moitié utile du ticket restait la révélation, règle B, et elle est livrée : la documentation du MFA ne s'appuie plus sur un contrôle affaibli de la même façon que celui qu'elle relativise.
