# Contrat public 1.0 (gel)

> **Gel de la surface publique** avant `1.0.0`. Tickets :
> `CLI-PUBLIC-CONTRACT-FREEZE-001`, `STARTERS-FINAL-CONTRACT-001`,
> `DOCS-LINKS-FINAL-AUDIT-001` (Phase 1 de la
> [roadmap beta.13](../roadmap/beta13-roadmap.md)).

Ce document **fige** ce qui constitue l'API publique de Forge pour la série
1.x. Après `1.0.0`, toute rupture de cette surface (renommage, suppression)
passe par une **release majeure** (charte, règle C). Avant 1.0, le gel sert à
**arrêter la valse de renommages** et à donner un contrat stable aux premiers
utilisateurs.

Un garde-fou — `tests/meta/test_public_contract_1_0_001.py` — verrouille
mécaniquement les listes ci-dessous : toute dérive casse la suite.

---

## 1. Famille de commandes `opt-in:*` (gelée)

La famille canonique de gestion des opt-ins officiels, **exactement 5 verbes** :

| Commande | Axe | Effet |
|---|---|---|
| `forge opt-in:install <name>` | présence (+) | affiche la commande `pip`/`pipx` (n'exécute rien) |
| `forge opt-in:remove <name>` | présence (−) | affiche la désinstallation |
| `forge opt-in:enable <name>` | activation (+) | câblage réel (kind `route`) / conseil (library, crosscutting) |
| `forge opt-in:disable <name>` | activation (−) | inverse de `enable` |
| `forge opt-in:list` | lecture | état des 7 opt-ins officiels |

**Décisions finales 1.0** :

- `enable`/`disable` font un **câblage réel uniquement pour le kind `route`**
  (iot) ; pour `library` (workflow, stats, media) et `crosscutting` (mfa,
  rbac), ils sont **informatifs** (ADR-016 D8 + A1). C'est le contrat 1.0, pas
  une étape intermédiaire.
- Les anciennes commandes `optin:enable` / `optin:list` (sans tiret) sont
  **définitivement retirées**.

## 2. Famille `module:*` (gelée, distincte)

Le système de **module local** (workflow d'auteur), **exactement 4 commandes** :

`forge module:list`, `forge module:install`, `forge module:files`,
`forge module:routes`.

**Décision finale 1.0** : `module:*` reste **distinct** de `opt-in:*`
(ADR-016 A2) — il sert à *fabriquer* un module local, pas à *consommer* un
opt-in officiel. Il n'est pas fusionné. Un nom inconnu passé à `opt-in:*`
oriente vers `forge module:install`.

## 3. Reste de la surface CLI

L'ensemble des commandes dispatchées est figé par
`tests/meta/test_cli_help_flags_closing_audit_001.py`
(`ALL_DISPATCHED_COMMANDS`). Chaque commande publique a une aide riche
(`forge <cmd> --help`) et une entrée dans
[`cli-commands.md`](cli-commands.md). Les codes de sortie suivent la
convention : `0` succès, `2` usage/argument, `1` erreur d'exécution.

## 4. Starters 1.0 (gelés — 99)

La liste pédagogique est **figée** : 99 starters, numérotés de 1 à 99,
nommés selon [la convention](../philosophy/starter-author-guide.md)
(`welcome-optin-<module>`, `users-core-auth`, `first-*`…). La progression
`welcome-forge` est organisée par niveau ; le **niveau avancé** (`relations`, …)
prolonge le niveau intermédiaire (`list-records`, `filter-list`, …), lui-même
au-dessus du niveau débutant. Trois autres progressions par niveau couvrent les
modules opt-in : `welcome-iot` (`iot-welcome`, …) pour `forge-mvc-iot`,
`welcome-video` (`video-welcome`, …) pour `forge-mvc-video`, `welcome-images`
(`images-welcome`, …) pour `forge-mvc-images`, `welcome-files`
(`files-welcome`, …) pour `forge-mvc-files`, `welcome-audio`
(`audio-welcome`, …) pour `forge-mvc-audio` (2 niveaux, sans état), `welcome-mfa` (`mfa-welcome`, …) pour `forge-mvc-mfa` (mécaniques TOTP, flux
enrôlement/challenge/récupération, durcissement), `welcome-rbac`
(`rbac-welcome`, …) pour `forge-mvc-rbac` (contrat déclaratif, vérification,
guards, résolution par utilisateur), et `welcome-workflow` (`workflow-welcome`, …)
pour `forge-mvc-workflow` (statuts, transitions, badges — sans état).

```
audio-doctor, audio-play, audio-probe, audio-transcode, audio-upload, audio-welcome,
csrf, db-transaction, delete-record, dynamic-route, file-upload, filter-list, first-crud, first-crud-generated,
file-bytes, file-delete, file-rate-limit, file-safe-name, file-safe-path, file-serve, file-store, file-validate, files-welcome,
first-html-view, first-sql, first-sql-write, flash-messages, form-post,
image-alt-order, image-attach, image-cover, image-delete, image-gallery, image-safety, image-upload, image-variants, images-welcome,
iot-api, iot-contract, iot-dashboard, iot-device, iot-doctor, iot-events,
iot-simulate, iot-subscriber, iot-welcome,
json-api, json-response,
layout-template,
mfa-challenge, mfa-crypto, mfa-enroll, mfa-recovery, mfa-replay, mfa-revalidation, mfa-secret, mfa-verify, mfa-welcome,
send-email,
list-records, pagination, query-params,
rbac-check, rbac-guard, rbac-permission, rbac-request-roles, rbac-resolve, rbac-role, rbac-template, rbac-user-role, rbac-welcome,
relations, request-debug, server-validation, session-state, update-record,
users-core-auth, video-detail, video-doctor, video-list, video-playback, video-probe, video-status, video-transcode, video-upload, video-welcome, welcome, welcome-optin-iot, welcome-optin-mfa,
welcome-optin-video,
workflow-available, workflow-badge, workflow-check, workflow-color, workflow-find, workflow-jinja, workflow-status, workflow-transition, workflow-welcome
```

Les anciennes applications métier lourdes ont été **archivées hors du système
starter**. Aucun ajout, retrait ni renommage de starter avant 1.0 sans mise à
jour de ce contrat.

## 5. Liens documentaires

L'intégrité des liens internes de la documentation est **garantie en
continu** par `mkdocs build --strict`, exécuté dans la suite de tests
(`tests/meta/test_install_docs_structure_001.py` et autres). Un lien cassé
fait échouer la suite. Aucun audit manuel séparé n'est requis : c'est déjà
enforced.
