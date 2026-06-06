# Roadmap — `1.0.0-beta.13`

> **Thème** : *dernière beta fonctionnelle* — slugs, gel du contrat public,
> production-readiness. **Finalité** : `RELEASE-BETA13-001`.
>
> **Principe directeur** : finir et **figer** ce qui existe ; une seule vraie
> feature (slugs). beta.14 sera la beta de *stabilisation* (doc + field-fixes,
> **zéro feature**) — jalon séparé, hors de cette roadmap.

---

## État de l'existant (`BETA13-EXISTING-AUDIT-001`)

Beaucoup de « net-new » supposé est en réalité **déjà présent, partiel**. Cet
audit dimensionne la roadmap : 🔨 construire · 🔧 compléter/durcir · 📋 auditer/documenter.

| Domaine | Existe déjà | Manque | Verdict |
|---|---|---|---|
| **slug (type)** | type `slug` dans le contrat d'entité (`forge_cli/entities/validation.py`) + `SlugField` CRUD + `_slugify` (validateur **strict**, rejette les accents) + `slugify_migration_name` | vrai `slugify` (translittération accents), `find_by_slug`, routing public `{slug}`, gestion d'unicité ; **3 fonctions slug à consolider (§11)** | 🔧 + 🔨 |
| **forge doctor** | 11 checks (db, env, ssl, migrations, structure, modules…) | checks **prod-sécurité** (debug off, cookies sécurisés, session non-mémoire, secret présent, perms `storage/`) | 🔧 étendre |
| **/health** | documenté (`GET /health → {"status":"ok"}`) | vérifier l'implémentation réelle + option `--db` | 📋 + 🔧 |
| **migrations** | `migration:status/apply/make/diff` | **pas de dry-run/confirm/garde-env trouvés** sur `apply` | 🔨 durcir (réel) |
| **erreurs prod** | gating dev/prod **existe** (`DX-RENDER-ERROR-001`, `core/http/helpers.py`) | request-id, masquage secrets, audit 403/404/500 | 🔧 compléter |
| **forge update** | commande existante (détection pipx) | finalisation (pip/pipx/source, jamais d'écrasement projet) | 🔧 finaliser |
| **uploads** | durci récemment (`SEC-UPLOAD-IMAGE-VERIFY-001/002`) | audit final (traversal, MIME, taille configurable) | 📋 auditer |

> **Conclusion** : b13 = *auditer → consolider → durcir → geler*. Seuls
> **slug-routing** et **migration-safety** sont du vrai « construire ».

---

## Phase 0 — Mise à niveau *(immédiat, dé-risque tout)*

| Ticket | Type | Objet |
|---|---|---|
| `BETA13-EXISTING-AUDIT-001` | 📋 | Cet audit (table ci-dessus). **Fait dans ce document.** |
| `CHANGELOG-DELTA-B12-B13-001` | 📋 | Section `beta.13` documentant les 65 commits post-beta.12. |

## Phase 1 — Gel du contrat public *(cheap, arrête la valse de renommages)*

| Ticket | Type | Objet · ⛓️ |
|---|---|---|
| `CLI-PUBLIC-CONTRACT-FREEZE-001` | 📋 | Commandes publiques vs internes ; **verrouiller `opt-in:*` (enable/disable réels = route-only, final) ET `module:*` (public-stable, A2)** ; codes de sortie ; `forge help` ↔ `cli-commands.md`. |
| `STARTERS-FINAL-CONTRACT-001` | 📋 | Figer les 16 starters (noms, ordre, routes, fichiers). |
| `DOCS-LINKS-FINAL-AUDIT-001` | 📋 | `mkdocs --strict` + audit liens/ancres après la réorg docs. |

## Phase 2 — Slugs *(la seule vraie feature)* ⛓️ après Phase 0

| Ticket | Type | Objet |
|---|---|---|
| `ADR-017-SLUG-TYPE` | 🔨 | ADR : sémantique du type `slug` dans le contrat d'entité (lien ADR-013, §10). |
| `SLUG-CORE-001` | 🔧 | **Consolider** les fonctions slug en un seul `core/http/slug.py` canonique. **stdlib seul** (`unicodedata` NFKD). |
| `SLUG-VALIDATION-001` | 🔧 | `is_valid_slug` officiel, **path-safe**, message stable. |
| `SLUG-SQL-CRUD-001` | 🔧 | `VARCHAR(180) NOT NULL` + `UNIQUE` ; CRUD : slug depuis champ source, **rejet des doublons** (suffixe auto → post-1.0). |
| `SLUG-ROUTING-001` | 🔨 | `find_by_slug` + route publique `/{ressource}/{slug}`. |
| `SLUG-DOCS-001` | 📋 | Usage, génération, unicité, route publique, limites. |

## Phase 3 — Production readiness *(surtout durcir/documenter)* — ✅ **complète**

| Ticket | État | Objet |
|---|---|---|
| `PROD-DOCTOR-001` | ✅ livré | check `Sécurité prod` dans `forge doctor` (séparation DB admin/app, uploads bornés). |
| `MIGRATION-SAFETY-FINAL-001` | ✅ livré | `migration:apply --dry-run` (aperçu + SQL sans appliquer). Suivi/checksums/journal déjà présents. |
| `PRODUCTION-CHECKLIST-DOCS-001` | ✅ livré | `docs/deployment/production-checklist.md` + guide comptes MariaDB. |
| `ERRORS-PROD-FINAL-001` | ✅ déjà présent | pages d'erreur sobres 400/403/404/413/422/429/500 + handlers ; stacktrace **jamais** en HTML, détails en logs (`_log_runtime_error`). |
| `HEALTHCHECK-FINAL-001` | ✅ déjà présent | `GET /health → {"status":"ok"}` (`app.py`) + `test_health_endpoint_001`. |
| `FORGE-UPDATE-FINAL-001` | ✅ déjà présent | `forge update --check/--dry-run/--pre` + détection pipx + `test_forge_update_command_001`. |

> **Audit de clôture Phase 3** : les trois derniers tickets étaient **déjà
> implémentés et testés** dans Forge (vérifiés, pas re-développés). La Phase 3
> ajoute le check sécurité-prod du doctor, le dry-run des migrations, et la
> documentation de déploiement.

## Phase 4 — Field test *(dogfooding)* ⛓️ après 2+3 — ✅ **complète**

| Ticket | État | Objet |
|---|---|---|
| `BETA13-DOGFOOD-001` | ✅ livré | Pipeline slug validé **bout-en-bout contre une vraie MariaDB**, sous forme reproductible : `tests/test_e2e_slug_mariadb.py` (gated `FORGE_E2E_MARIADB`). |

> **Forme retenue** : plutôt qu'une app jetable, un **test e2e committé** qui
> rejoue le pipeline réel — entité `Article` (`title` + `slug` auto depuis
> `title`) → `build_entity_sql` → `apply_model_sql` sur la base → introspection
> (`Slug VARCHAR(180)` + `UNIQUE`) → runtime `slugify()`→INSERT→lecture par slug
> → **rejet du doublon** par la contrainte d'unicité. 7/7 verts sur MariaDB ;
> SKIPPED proprement sans la base. C'est le **go** : le slug fonctionne en réel.

## Phase 5 — Clôture & release ⛓️ tout vert

| Ticket | État | Objet |
|---|---|---|
| `BETA13-CLOSING-AUDIT-001` | ✅ vert | Batterie complète : `pytest` **16587 passed / 0 échec** + `ruff` + `compileall` + `mkdocs --strict` + `git diff --check` + `sync:landing --check`. |
| `BETA13-BUMP-001` | ✅ livré | Bump b12→b13 sur **23 fichiers** (7 `pyproject.toml` + `forge.py` + `app.py` + `core/__init__.py` + 6 `__init__.py` opt-in + `package.json`/`package-lock.json` + CHANGELOG daté + roadmap + landing resync), **pins Alpha `==1.0.0b13`** (media, mfa). Cohérence vérifiée (`tests/meta/` **6955 passed**, `forge --version` = `Forge 1.0.0b13`). |
| `RELEASE-BETA13-001` | ⏸️ en attente | Tag `v1.0.0-beta.13`, build, publication PyPI (`--pre`), sync landing publique. **Action irréversible/sortante — sur autorisation explicite uniquement.** |
| `BETA13-POST-PUBLISH-VERIFY-001` | ⏸️ en attente | Vérif PyPI publique + install propre. |

> **Seuil de release** : le bump est finalisé et toute la cohérence est verte.
> Le tag git et la publication PyPI (étape `RELEASE-BETA13-001`) ne sont **pas**
> réalisés — ils relèvent d'une décision explicite (publication = action
> publique et irréversible).

---

## Chemin critique

```
Phase 0 ─┬─▶ Phase 1 (gel) ─────────────────┐
         └─▶ Phase 2 (slugs) ──┐            ├─▶ Phase 5 (clôture → release)
            Phase 3 (prod) ─────┴─▶ Phase 4 ─┘
                                  (dogfood)
```

Phases 1 et 3 **parallélisables** avec la 2. Phase 0 débloque tout.
Phase 4 (dogfood) = **vrai go/no-go** avant clôture.

## Définition de « beta.13 prête »

1. 16 starters + contrat CLI (`opt-in:*`/`module:*`) **gelés et documentés**.
2. Slugs complets (type + slugify canonique + validation + SQL/CRUD + routing public + doc) et **une app réelle construite avec**.
3. Production : doctor/migrations/erreurs/health/update **durcis + checklist déploiement**.
4. `BETA13-CLOSING-AUDIT-001` **vert**, versions bumpées b13, CHANGELOG complet.

> **Note — opt-in `forge-mvc-video` livré en parallèle.** Hors de la
> définition initiale ci-dessus, l'opt-in `forge-mvc-video` v1 (upload,
> transcodage MP4 H.264/AAC, lecture HTTP Range, commandes `video:*`) a été
> développé et mergé sur `main` pendant ce cycle, puis publié avec les autres
> distributions en `1.0.0-beta.13`. Audit de clôture : `audit-video-closing.md`.

## Hors périmètre b13 (→ post-1.0)

Suffixe slug auto, `slug_history`/redirections 301, sitemap, recherche avancée,
pagination avancée, admin, multi-SGBD, Docker officiel, monitoring, ORM, SPA,
marketplace.

---

## Annexe — Carte d'implémentation `SLUG-SQL-CRUD-001`

> Investigation faite ; design figé ; **implémentation reportée** (effort
> dédié). À reprendre idéalement **avec MariaDB** pour valider le CRUD généré,
> ou via la Phase 4 (dogfood). Cette carte évite de refaire l'investigation.

### Décisions figées

- Le slug est **généré depuis un champ source** (ex. `titre`), pas saisi.
- Slug **stable à l'édition** (généré une fois à la création ; changer le titre
  ne change pas l'URL → pas de redirection 301, reportée post-1.0).
- Doublon d'unicité → **erreur claire** (« ce slug existe déjà »), **pas** de
  suffixe auto `-2/-3` (ADR-017 D4).

### Constat clé du pipeline

Forge a un pipeline d'entité **multi-couches** : JSON utilisateur (`type`) →
**normaliseur** → forme canonique (`sql_type` / `form.field`) → générateurs.
`slug` existe au niveau *form normalisé* (`SUPPORTED_FORM_FIELD_VALUES`) mais
**pas** comme `type` utilisateur (l'enum `type` de `field.schema.json` ne le
contient pas). Le SQL est déjà géré (`build_entity_sql` produit `UNIQUE KEY`
depuis `unique: true`).

### Changements par couche

| Couche | Fichier(s) | Changement |
|---|---|---|
| Schéma (×2 à synchroniser) | `schemas/field.schema.json` **et** `forge_cli/schemas/field.schema.json` | ajouter `slug` à l'enum `type` ; ajouter la propriété `source` (string) |
| Normaliseur | `forge_cli/entities/canonical_model_normalizer.py` | `type:slug` → `sql_type:VARCHAR(180)`, `form.field:slug` ; propager `source` |
| Validation | `forge_cli/entities/validation.py` | `source` dans `ALLOWED_FIELD_KEYS` ; règle sémantique : `source` réfère un champ texte existant de l'entité |
| Form | `forge_cli/entities/crud/form_builder.py` | exclure du formulaire un champ slug porteur de `source` (auto-généré) |
| Contrôleur | `forge_cli/entities/crud/controller_builder.py` | à la création : `data = dict(form.cleaned_data); data["<slug>"] = slugify(data["<source>"])` (via `core.http.slug`) avant `add_…(data)` ; envelopper l'INSERT pour capter l'erreur d'unicité → message clair |
| Modèle | `forge_cli/entities/crud/model_builder.py` | **exclure** le champ slug auto de l'`UPDATE` (stable à l'édition) ; le garder dans l'`INSERT` |

### Garde-fous / validation

- Tests **structurels** façon `test_make_crud` : le contrôleur généré contient
  `slugify(`, le slug est absent du formulaire, l'INSERT a la colonne slug,
  l'`UPDATE` ne l'a pas.
- `compileall` du CRUD généré (échantillon) pour attraper toute erreur de
  syntaxe.
- **Validation runtime (DB)** : déférée au dogfood Phase 4 (les e2e MariaDB
  sont gated par la disponibilité d'une base).

### Avancement & inconnues résolues (investigation)

- ✅ **Commit A livré** (`af09e7a`) : `type: slug` → `VARCHAR(180)` + `SlugField`
  (saisie manuelle validée). Le type slug est **utilisable dès maintenant**.
- **Commit B** (auto-génération depuis `source`) — ~6 fichiers : schémas ×2
  (`source`), normaliseur (propage `source`), `validation.py` (`source` dans
  `ALLOWED_FIELD_KEYS` + règle « réfère un champ texte existant »),
  `crud/utils.py` (helper `_is_generated(f)` = a un `source` ; **`_non_pk_fields`
  est partagé** form/model → l'exclusion doit être ciblée), `form_builder`
  (exclure le champ généré), `controller_builder`
  (`_data["slug"] = slugify(_data[source])` avant `add_…`), `model_builder`
  (exclure le slug généré de l'`UPDATE`).
- **Doublon** : la contrainte `UNIQUE` **garantit déjà** zéro slug dupliqué.
  Le *message d'erreur clair* (catch `DoublonError`) est une **lacune générale
  du générateur** (le CRUD généré ne wrappe l'INSERT pour **aucun** champ
  unique aujourd'hui) → sous-chantier séparé `CRUD-DUP-HANDLING-001`, pas
  slug-spécifique.
