# Audit CONSOLIDATION-CLI-001 — Cohérence CLI Forge

## Objectif

Auditer la cohérence globale de la CLI Forge après CONSOLIDATION-001. Vérifier que les commandes sont cohérentes, lisibles, documentées et correctement organisées. Ne rien corriger.

---

## Synthèse

**Verdict : la CLI Forge est cohérente et exploitable.**

59 commandes disponibles, toutes organisées selon une convention de nommage uniforme (`namespace:action`). Le dispatcher central dans `forge.py` délègue proprement vers les sous-modules `forge_cli.*`. Les commandes récentes (`auth:user:role:*`, `module:*`, `forge new --profile`) respectent intégralement les conventions établies.

Quatre incohérences mineures sont identifiées (style des messages d'aide, alias non documenté, nommage `build:model` / `check:model`). Aucune n'est bloquante.

---

## Commandes auditées

**59 commandes répertoriées :**

| Famille | Commandes | Fichier délégué |
|---------|-----------|-----------------|
| Projet | `new`, `doctor`, `help`, `--version` | `forge.py` (inline) |
| Entités | `make:entity`, `make:crud`, `make:relation`, `sync:entity`, `sync:relations`, `sync:landing` | `forge_cli/entities/` |
| Modèles | `build:model`, `check:model` | `forge_cli/entities/model.py` |
| Pages publiques | `make:public-page`, `make:public-list`, `make:public-show`, `make:public-form`, `make:public-contact` | `forge_cli/public_*.py` |
| Front | `js:init` (htmx / alpine / htmx-alpine) | `forge_cli/front.py` |
| i18n | `i18n:init`, `i18n:check` | `forge_cli/i18n.py` |
| Auth | `auth:init`, `auth:doctor`, `auth:status`, `auth:list-sql` | `forge_cli/auth.py` |
| Auth/User | `auth:user:create`, `auth:user:list`, `auth:user:show`, `auth:user:disable`, `auth:user:enable`, `auth:user:password` | `forge_cli/auth.py` |
| Auth/RBAC | `auth:user:role:add`, `auth:user:role:remove`, `auth:user:roles` | `forge_cli/auth.py` |
| Mail | `mail:init`, `mail:test`, `mail:render`, `mail:doctor`, `mail:logs` | `forge_cli/mail.py` |
| Modules | `module:list`, `module:install`, `module:files`, `module:routes` | `forge_cli/modules.py` |
| Starters | `starter:list`, `starter:build` | `forge_cli/starters/__init__.py` |
| Déploiement | `deploy:init`, `deploy:check` | `forge_cli/deploy.py` |
| Database | `db:init`, `db:apply` | `forge_cli/entities/db_init.py`, `db_apply.py` |
| Migrations | `migration:status`, `migration:apply`, `migration:make`, `migration:diff` | `forge_cli/entities/migrations.py` |
| Uploads / médias | `upload:init`, `media:init` | `forge_cli/uploads.py` |
| Routes | `routes:list` | `forge.py` (inline) |
| Docs | `docs:pdf` | `forge_cli/docs/` |

---

## Cohérence du nommage

**Convention principale : `namespace:action` ou `namespace:sub:action`.**

Respectée par toutes les familles de commandes :

| Style | Exemples | Cohérence |
|-------|----------|-----------|
| Plat | `new`, `doctor`, `help` | ✅ Réservé aux commandes fondamentales |
| `namespace:action` | `make:entity`, `auth:init`, `module:list` | ✅ Standard |
| `namespace:sub:action` | `auth:user:create`, `auth:user:role:add` | ✅ Cohérent avec la hiérarchie |

**Commandes récentes vérifiées :**

- `auth:user:role:add`, `auth:user:role:remove`, `auth:user:roles` — ✅ respectent la convention de profondeur 3.
- `module:list`, `module:install`, `module:files`, `module:routes` — ✅ style `namespace:action` standard.
- `forge new --profile` — ✅ option standard, validée et documentée.

**Incohérences de nommage identifiées :**

| Incohérence | Description | Sévérité |
|-------------|-------------|----------|
| `build:model` / `check:model` | Style différent de `make:entity` / `sync:entity` — verbe "build" vs "make" pour des opérations de génération | ⚠️ FAIBLE |
| `upload:init` / `media:init` | Deux noms pour la même logique (alias) — non documenté dans l'aide | ⚠️ FAIBLE |

---

## Cohérence des aides

**Style global :** l'aide de premier niveau (`forge help`) est complète et couvre toutes les familles de commandes. Elle est produite depuis la docstring de `forge.py` (lignes 2–76).

**Style des aides par commande :**

| Module | Style d'aide | Cohérence |
|--------|--------------|-----------|
| `forge.py` | `sys.exit("Usage : ...")` | ✅ Cohérent |
| `auth.py` | `argparse` pour `auth:user:*`, `raise SystemExit("Usage : ...")` pour le reste | ✅ Acceptable |
| `mail.py` | `sys.exit("Usage : ...")` | ✅ Cohérent |
| `modules.py` | `print(...)` + `raise SystemExit(1)` (sans message dans SystemExit) | ⚠️ Incohérent |
| `front.py` | `print("Usage : ...")` | ⚠️ Incohérent — pas de `sys.exit` |
| `starters/__init__.py` | `print(...)` + `raise SystemExit(1)` | ⚠️ Incohérent |

**Incohérence principale :** trois styles coexistent pour afficher un message d'usage et quitter :
1. `sys.exit("Usage : ...")` — quitte avec message (style compact, cohérent).
2. `raise SystemExit("Usage : ...")` — équivalent mais syntaxe différente.
3. `print("Usage : ...")` suivi de `raise SystemExit(1)` — le code de sortie est explicite mais le message n'est pas dans l'exception.

Ces incohérences ne sont pas fonctionnellement bloquantes. À harmoniser dans un ticket dédié.

**Support `--help` :**

- `auth:user:*` : `argparse` avec aide automatique désactivée (`add_help=True` sur certains parsers). Aide structurée.
- `module:*` : `argparse` avec `add_help=False` — pas de `--help` disponible.
- Autres commandes : pas de `--help` individuel — uniquement `forge help` global.

---

## Cohérence des erreurs

**Commande inconnue (`forge xyz`) :**

```text
Commande inconnue : 'xyz'. Voir : forge help
```

Message clair, avec renvoi vers l'aide. ✅

**Profil invalide (`forge new MonProjet --profile inexistant`) :**

```text
Profil inconnu : inexistant. Profils disponibles : minimal, standard, dynamic, multilingual.
```

Message clair avec liste des valeurs valides. ✅

**Argument manquant variable selon la commande :**

| Commande | Comportement sur argument manquant | État |
|----------|------------------------------------|------|
| `auth:user:create` | `argparse` — message d'erreur structuré | ✅ |
| `auth:user:role:add` | `argparse` — message d'erreur structuré | ✅ |
| `module:install` | Message inline + `SystemExit(1)` | ✅ Acceptable |
| `make:public-form` | Comportement non garanti | ⚠️ À vérifier |
| `make:public-contact` | Comportement non garanti | ⚠️ À vérifier |
| `mail:test` | Validation de `--to` requis | ✅ |
| `migration:make` | Validation du nom | ✅ |

---

## Dispatch dans forge.py

**Fichier :** `forge.py` — 619 lignes.

**Structure du dispatcher :**

- Lignes 461–607 : fonction `main()` avec dispatch par `if command ==` ou `if command in (...)`.
- Commandes simples : dispatch direct vers une fonction `cmd_*()` dans `forge.py`.
- Familles de commandes : dispatch vers `*_main(args)` dans les sous-modules.

**Familles déléguées (pattern `if command in (...)`) :**

| Famille | Lignes | Délégation |
|---------|--------|------------|
| auth | 542–558 | `auth_main(args)` |
| i18n | 538 | `i18n_main(args)` |
| mail | 560 | `mail_main(args)` |
| deploy | 564 | `deploy_main(args)` |
| starter | 568 | `starters_main(args)` |
| module | 572 | `modules_main(args)` |
| model/sync | 581 | `model_main(args)` |
| migration | 593 | `migrations_main(args)` |

**Conclusion :** `forge.py` est lisible et proprement délégateur. Aucune logique métier lourde. La longueur (619 lignes) est acceptable compte tenu du nombre de commandes couvertes.

---

## Commandes Auth

**13 commandes `auth:*`, toutes dans `forge_cli/auth.py` (1134 lignes).**

Structure interne : dispatcher à 14 conditions `if command ==` dans `auth_main(argv)`.

**Vérifications :**

| Commande | Présente | Validée | Aide |
|----------|----------|---------|------|
| `auth:init` | ✅ | ✅ | Inline |
| `auth:doctor` | ✅ | ✅ | Inline |
| `auth:status` | ✅ | ✅ | Inline |
| `auth:list-sql` | ✅ | ✅ | Inline |
| `auth:user:create` | ✅ | ✅ argparse | Structurée |
| `auth:user:list` | ✅ | ✅ | Structurée |
| `auth:user:show` | ✅ | ✅ | Structurée |
| `auth:user:disable` | ✅ | ✅ | Structurée |
| `auth:user:enable` | ✅ | ✅ | Structurée |
| `auth:user:password` | ✅ | ✅ | Structurée |
| `auth:user:role:add` | ✅ | ✅ argparse | Structurée |
| `auth:user:role:remove` | ✅ | ✅ argparse | Structurée |
| `auth:user:roles` | ✅ | ✅ | Structurée |

**Note :** `auth.py` est le module le plus volumineux de la CLI (1134 lignes). Cela est justifié par les 13 commandes + la logique de chaque opération utilisateur.

---

## Commandes Starters

**2 commandes `starter:*`, dans `forge_cli/starters/__init__.py`.**

| Commande | Présente | Validée | Aide |
|----------|----------|---------|------|
| `starter:list` | ✅ | ✅ | Inline |
| `starter:build` | ✅ | ✅ | Inline |

**Note :** `starter:build` accepte un numéro ou un alias (`1`, `contacts`, `carnet`, etc.). Validation correcte avec message d'erreur sur starter inconnu.

---

## Commandes Modules

**4 commandes `module:*`, dans `forge_cli/modules.py` (214 lignes).**

| Commande | Présente | Validée | Aide |
|----------|----------|---------|------|
| `module:list` | ✅ | ✅ | Inline (`print` + `SystemExit`) |
| `module:install` | ✅ | ✅ | Inline |
| `module:files` | ✅ | ✅ | Inline |
| `module:routes` | ✅ | ✅ | Inline |

**Incohérence relevée :** `add_help=False` sur tous les parsers modules — pas de `--help` disponible. Contournement : `forge help` global. Acceptable pour l'instant.

---

## Commandes Profils

**Support `--profile` dans `forge new` :**

```bash
forge new MonProjet --profile standard
forge new MonProjet --profile minimal
forge new MonProjet --profile dynamic
forge new MonProjet --profile multilingual
```

- Profils valides : `minimal`, `standard`, `dynamic`, `multilingual`.
- Défaut : `standard`.
- Validation : message d'erreur clair sur profil invalide avec liste des valeurs acceptées.
- Enregistrement : `forge_profile.txt` dans le projet généré.
- ✅ Entièrement fonctionnel et cohérent.

---

## Commandes Migrations / DB

**6 commandes `migration:*` et `db:*`, dans `forge_cli/entities/migrations.py`.**

| Commande | Présente | Aide |
|----------|----------|------|
| `db:init` | ✅ | Inline |
| `db:apply` | ✅ | Inline |
| `migration:status` | ✅ | Inline |
| `migration:apply` | ✅ | Inline |
| `migration:make` | ✅ | Inline |
| `migration:diff` | ✅ | Inline |

Cohérence satisfaisante. `db:*` et `migration:*` sont deux namespaces distincts pour des opérations de niveau différent (initialisation vs versionnement).

---

## Commandes Front / i18n

**3 commandes `js:init` (variantes positionnelles), 2 commandes `i18n:*`.**

| Commande | Présente | Aide |
|----------|----------|------|
| `js:init htmx` | ✅ | Print inline |
| `js:init alpine` | ✅ | Print inline |
| `js:init htmx-alpine` | ✅ | Print inline |
| `i18n:init` | ✅ | Inline |
| `i18n:check` | ✅ | Inline |

**Note :** `js:init` utilise un argument positionnel (pas un flag `--library`). Acceptable : il y a exactement 3 variantes. Pas de `--help` individuel.

---

## Commandes Déploiement

**2 commandes `deploy:*`, dans `forge_cli/deploy.py`.**

| Commande | Présente | Aide |
|----------|----------|------|
| `deploy:init` | ✅ | Inline |
| `deploy:check` | ✅ | Inline |

Ces commandes sont stables (génèrent un fichier de configuration déploiement). Documentées dans le guide de déploiement.

---

## Points cohérents

1. **Convention de nommage uniforme** : 59 commandes, toutes en style `namespace:action` ou plat pour les commandes fondamentales.
2. **Dispatch centralisé propre** : `forge.py` délègue sans logique métier. Lisible en 619 lignes.
3. **Commandes récentes conformes** : `auth:user:role:*`, `module:*`, `forge new --profile` — toutes conformes aux conventions.
4. **Validation `--profile`** : complète, message d'erreur clair, liste des profils affichée.
5. **auth:user:*** : argparse avec validation structurée — meilleure qualité d'aide que la moyenne.
6. **Commande inconnue** : message informatif avec renvoi vers `forge help`.
7. **Starter inconnu** : message avec liste des starters disponibles.

---

## Incohérences détectées

| N° | Zone | Description | Sévérité | Ticket recommandé |
|----|------|-------------|----------|-------------------|
| 1 | Aide | Trois styles coexistent : `sys.exit(msg)`, `raise SystemExit(msg)`, `print(msg)` + `raise SystemExit(1)` | ⚠️ FAIBLE | CONSOLIDATION-DOC-001 ou ticket dédié |
| 2 | Aide | `module:*` : `add_help=False` — pas de `--help` individuel disponible | ⚠️ FAIBLE | Ticket dédié post-consolidation |
| 3 | Nommage | `build:model` / `check:model` — style différent de `make:entity` / `sync:entity` | ⚠️ FAIBLE | Ticket dédié post-consolidation |
| 4 | Nommage | `upload:init` / `media:init` — alias non documenté dans l'aide globale | ⚠️ FAIBLE | CONSOLIDATION-DOC-001 |
| 5 | Erreurs | `make:public-form`, `make:public-contact` — validation d'arguments non garantie | ⚠️ FAIBLE | CONSOLIDATION-NON-OVERWRITE-001 ou ticket dédié |

**Aucune incohérence bloquante.**

---

## Recommandations

Ces recommandations sont destinées aux tickets suivants. Ne pas corriger dans CONSOLIDATION-CLI-001.

### CONSOLIDATION-DOC-001

- Documenter l'alias `upload:init` / `media:init` dans l'aide globale.
- Vérifier que `docs/reference.md` couvre les 13 commandes `auth:*`.
- Vérifier que `docs/guide.md` mentionne `forge new --profile`.

### Post-consolidation : harmonisation des messages d'aide

- Choisir un style unique : recommandé `sys.exit("Usage : ...")`.
- Remplacer les occurrences `print(msg)` + `raise SystemExit(1)` dans `modules.py` et `starters/__init__.py`.

### Post-consolidation : nommage `build:model` / `check:model`

- Ces commandes sont peu visibles dans la documentation. Évaluer si un alias `make:model` ou `sync:model` serait plus cohérent. Ne pas renommer sans évaluation d'impact.

### Post-consolidation : `--help` sur `module:*`

- Activer `add_help=True` dans les parsers `modules.py` ou ajouter une aide explicite sur `-h`.

---

*Audit réalisé le 2026-05-08. Forge post-1.5.0. 4801 tests passés, 1 skipped.*
