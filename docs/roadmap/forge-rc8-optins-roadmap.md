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
| `JOBS-PRIORITY-001` | Colonne de priorité et ordre de prise en compte |
| `JOBS-STATUS-CLI-001` | Commande `jobs:status`, files en attente, en cours et en échec |
| `ADMIN-LIST-FILTERS-001` | Filtres, recherche et tri sur les listes du back-office |
| `ENTITIES-UNIQUE-COMPOSITE-001` | Contrainte d'unicité sur plusieurs colonnes, déclarée au contrat |
| `RBAC-INSTANCE-PERMISSIONS-001` | Permission portant sur une instance, cas du propriétaire |
| `WORKFLOW-HOOKS-001` | Points d'accroche explicites avant et après transition |
| `DB-DOCTOR-001` | Commande `db:doctor`, version, droits, jeu de caractères |

---

## 6. Lot 3 - Compositions entre opt-ins

Ces tickets branchent des opt-ins les uns sur les autres.
Chacun dépend d'un ticket du lot 2.

| Ticket | Dépend de | Responsabilité unique |
|---|---|---|
| `MAIL-QUEUE-VIA-JOBS-001` | jobs | Envoi différé par la file, motif officiel documenté |
| `IMPEXP-ASYNC-JOBS-001` | jobs | Import de gros fichiers par la file |
| `RBAC-DENIAL-AUDIT-001` | audit | Consigner les refus d'accès |
| `AUDIT-CSV-EXPORT-001` | import-export | Export du journal en CSV |
| `NOTIF-MAIL-BRIDGE-001` | mail, jobs | Relais documenté de la notification vers l'email |
| `ADMIN-SETTINGS-UI-001` | admin | Écran d'administration des paramètres |
| `ADMIN-SESSIONS-VIEW-001` | admin | Écran des sessions actives |
| `WORKFLOW-ENTITY-STATUS-001` | entities | Reconnaissance du champ de statut des contrats |

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
| `JOBS-IDEMPOTENCY-KEY-001` | Clé d'idempotence, contrainte et aide de mise en file |
| `JOBS-HEARTBEAT-001` | Prolongation du bail pour les tâches longues |
| `DOC-JOBS-COMPOSITION-001` | Documentation des branchements vers mail, video et notifications |

### 7.8 mail

| Ticket | Responsabilité unique |
|---|---|
| `MAIL-ATTACHMENTS-001` | Pièces jointes simples |
| `MAIL-TEST-GUIDED-001` | `mail:test` guidé, essai à blanc et destinataire de test |
| `MAIL-LAYOUTS-001` | Gabarits d'email réutilisables |

### 7.9 notifications

| Ticket | Responsabilité unique |
|---|---|
| `NOTIF-TARGET-URL-001` | Lien cible porté par la notification |
| `NOTIF-PAGINATION-001` | Pagination de la liste |

### 7.10 files

| Ticket | Responsabilité unique |
|---|---|
| `FILES-QUOTA-001` | Quota par utilisateur et par ressource |
| `FILES-SCAN-HOOK-001` | Interface d'analyse antivirus, mise en oeuvre hors du paquet |
| `FILES-ORPHAN-PURGE-001` | Purge des fichiers sans référence |
| `DOC-FILES-XACCEL-001` | Envoi délégué au serveur frontal, documenté comme motif de production |

### 7.11 images

| Ticket | Responsabilité unique |
|---|---|
| `IMAGES-PRESETS-DECLARATIFS-001` | Variantes déclarées par configuration et non en dur |
| `IMAGES-FOCAL-CROP-001` | Recadrage autour d'un point d'intérêt |
| `IMAGES-ORPHAN-VARIANTS-001` | Nettoyage des variantes sans original |
| `IMAGES-ENTITY-FIELD-001` | Intégration au champ image des contrats d'entité |
| `IMAGES-LIMITS-CONFIG-001` | Limites de dimensions et de poids explicites en configuration |

### 7.12 video

| Ticket | Responsabilité unique |
|---|---|
| `VIDEO-STATUS-UI-001` | Restitution de l'état de traitement dans l'interface |
| `VIDEO-QUOTA-001` | Quota de durée et de taille |
| `VIDEO-SUBTITLES-001` | Fichier de sous-titres associé |

### 7.13 audio

| Ticket | Responsabilité unique |
|---|---|
| `AUDIO-ID3-001` | Exposition des métadonnées du fichier |
| `AUDIO-TRIM-001` | Découpe par début et fin en ligne de commande |
| `AUDIO-DOCTOR-HARMONISE-001` | Messages de `audio:doctor` alignés sur `video:doctor` |

### 7.14 iot

| Ticket | Responsabilité unique |
|---|---|
| `IOT-DEVICE-AUTH-001` | Authentification par équipement ou par site |
| `IOT-AGGREGATES-001` | Moyenne, minimum et maximum sur une fenêtre |
| `IOT-RBAC-READ-001` | Contrôle d'accès optionnel sur l'API de lecture |

### 7.15 import-export

| Ticket | Responsabilité unique |
|---|---|
| `IMPEXP-COLUMN-MAPPING-001` | Correspondance de colonnes déclarée au contrat |
| `IMPEXP-ERROR-REPORT-001` | Rapport d'erreurs téléchargeable |
| `IMPEXP-FILTERED-EXPORT-001` | Export respectant les filtres de la liste |
| `IMPEXP-JSONL-001` | Second format, une ligne par enregistrement |

### 7.16 fixtures

| Ticket | Responsabilité unique |
|---|---|
| `FIXTURES-SCENARIOS-001` | Jeux nommés, démonstration, test et minimal |
| `FIXTURES-SNAPSHOT-001` | Export de l'état courant vers des fabriques |
| `FIXTURES-FK-ORDER-ROBUST-001` | Ordre des clés étrangères durci |

### 7.17 settings

| Ticket | Responsabilité unique |
|---|---|
| `SETTINGS-PER-USER-001` | Paramètres par utilisateur, derrière un drapeau |
| `SETTINGS-CACHE-001` | Cache mémoire à invalidation explicite |
| `DOC-SETTINGS-NO-SECRETS-001` | Refus documenté d'y placer des secrets |

### 7.18 audit

| Ticket | Responsabilité unique |
|---|---|
| `AUDIT-FILTERS-001` | Filtres par acteur, par type et par période |
| `AUDIT-ACTION-HELPER-001` | Aide unique de consignation d'une action |

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
