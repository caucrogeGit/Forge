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
| `ADMIN-DOC-ETAT-REEL-001` | Réaligner le README et la roadmap de `forge-mvc-admin` sur le code livré |
| `META-README-COMMANDS-RATCHET-001` | Garde-fou comparant, par opt-in, les commandes annoncées au README et le contenu de `COMMANDS` |

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
| `ADMIN-BULK-ACTIONS-001` | Actions en masse, adossées aux transitions quand workflow est présent |

### 7.2 entities

| Ticket | Responsabilité unique |
|---|---|
| `ENTITIES-COMPUTED-FIELDS-001` | Champs dérivés en lecture seule, documentés au contrat |
| `ENTITIES-BUSINESS-VALIDATION-001` | Validation métier déclarable au delà des types |
| `ENTITIES-SLUG-ROUTES-001` | Recherche par slug et routes publiques correspondantes |
| `ENTITIES-MIGRATION-DIFF-READABLE-001` | Sortie de `migration:diff` lisible, et essai à blanc |

### 7.3 rbac

| Ticket | Responsabilité unique |
|---|---|
| `RBAC-CONTRACT-EXPORT-001` | Export du contrat, documentation des rôles d'une application |

### 7.4 workflow

| Ticket | Responsabilité unique |
|---|---|
| `WORKFLOW-HISTORY-001` | Historique des transitions, auteur et date |
| `WORKFLOW-CONDITIONS-001` | Conditions de transition par fonction enregistrée |

### 7.5 mfa

| Ticket | Responsabilité unique |
|---|---|
| `MFA-REQUIRED-BY-ROLE-001` | Politique rendant le facteur obligatoire pour un rôle |

### 7.6 sessions-db

| Ticket | Responsabilité unique |
|---|---|
| `SESSIONS-TTL-PER-KIND-001` | Durée de vie distincte selon la nature de la session |
| `SESSIONS-ACTIVE-METRIC-001` | Compteur de sessions actives |
| `SESSIONS-GC-TIMER-DOC-001` | Minuterie systemd documentée pour `sessions:gc` |

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
| `STATS-IP-ANONYMISATION-001` | Anonymisation optionnelle de l'adresse |
| `STATS-EVENT-KIND-001` | Distinction entre vue de page et action métier |
| `DOC-STATS-AGGREGATES-001` | Documentation des agrégations par jour et par page |

### 7.20 qrcode

| Ticket | Responsabilité unique |
|---|---|
| `QRCODE-CLI-001` | Commande `qrcode:make` |
| `QRCODE-ERROR-LEVEL-001` | Niveau de correction d'erreur exposé à l'appelant |

### 7.21 i18n

| Ticket | Responsabilité unique |
|---|---|
| `I18N-EXTRACT-CLI-001` | Commande `i18n:extract` sur les gabarits |
| `I18N-MISSING-KEYS-DEV-001` | Signalement des clés manquantes hors production |
| `I18N-PLURALS-001` | Règle de pluriel minimale |

### 7.22 deploy

| Ticket | Responsabilité unique |
|---|---|
| `DEPLOY-NGINX-MEDIA-HEADERS-001` | Gabarit couvrant les médias, l'envoi délégué et les en-têtes de sécurité |
| `DEPLOY-TIMERS-DOC-001` | Minuteries de sauvegarde et de reprise des tâches |

### 7.23 backends

| Ticket | Responsabilité unique |
|---|---|
| `DB-ERROR-MESSAGES-HOMOGENES-001` | Messages d'erreur homogènes entre les quatre dialectes |
| `DOC-DIALECT-ECARTS-001` | Écarts de dialecte documentés, limite, booléens et insertion conditionnelle |

### 7.24 testing

| Ticket | Responsabilité unique |
|---|---|
| `TESTING-CLIENT-001` | Client de test léger, requête vers réponse, sans navigateur |
| `TESTING-LOGIN-AS-001` | Aide d'authentification de test par rôle |
| `TESTING-FIXTURES-ALIGN-001` | Fixtures pytest alignées sur `forge-mvc-fixtures` |
| `TESTING-ASSERTIONS-001` | Assertions de session et de jeton anti-rejeu |

---

## 8. Lot 5 - Tickets en tension avec la charte

Ces cinq tickets sont demandés, et chacun entre en tension avec un principe.
La tension est nommée ici pour être tranchée en connaissance de cause, non pour bloquer la livraison.

| Ticket | Tension |
|---|---|
| `MFA-WEBAUTHN-001` | Principe 8, le facteur TOTP suffit au socle et la charge de maintenance est durable |
| `RBAC-ROLE-HIERARCHY-001` | Limite assumée par l'ADR-014, la rouvrir élargit le contrat public |
| `AUDIO-STATEFUL-OPTION-001` | Principe 11, une seconde façon de gérer un média avec état existe déjà dans video |
| `DEPLOY-CADDY-001` | Principe 11, deux serveurs frontaux officiels au lieu d'un |
| `NOTIF-POLLING-HELPER-001` | Principe 1, le rafraîchissement d'interface relève de l'application |

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
