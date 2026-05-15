# Audit CONSOLIDATION-FRONT-001 — Tailwind / HTMX / Alpine / templates

**Date :** 2026-05-09
**Périmètre :** socle front-end Forge — Tailwind, JS optionnel, templates Jinja, CRUD HTMX, i18n
**Ticket :** CONSOLIDATION-FRONT-001

---

## Objectif

Vérifier que le socle front Forge reste léger, explicite, documenté et aligné avec la philosophie : **HTML serveur d'abord, Tailwind comme CSS officiel, HTMX et Alpine optionnels**.

Ce ticket n'ajoute aucun framework front nouveau.

---

## Synthèse

| Zone front | État | Commentaire |
|---|---|---|
| Tailwind | OK | v4.2.2, `build:css` déclaré, source + compilé présents |
| `package.json` | OK | Dépendances cohérentes, pas de bundler lourd |
| `static/src/input.css` | OK | `@import "tailwindcss"`, classes custom Forge |
| `static/tailwind.css` | OK | Présent (~24 Ko compilé) |
| JS Forge | OK | `static/js/app.js` minimal, sans HTMX/Alpine |
| HTMX | OK | Optionnel, `forge js:init htmx`, vendor non commité |
| Alpine | OK | Optionnel, `forge js:init alpine`, vendor non commité |
| HTMX + Alpine | OK | `forge js:init htmx-alpine` combine les deux |
| Templates publics | OK | Layouts publics propres, Tailwind chargé |
| Templates admin | OK | Layout admin propre, `{% block scripts %}` disponible |
| Composants Jinja | OK | 6 composants + 4 partials cohérents |
| CRUD HTMX | OK | `hx-get`, `hx-post`, `hx-target` — pas de `hx-delete` |
| i18n templates | OK | `trans()` globalement disponible via Jinja2 |
| Documentation | OK | `docs/front.md` complet (~960 lignes) |
| Forge Design séparé | OK | Aucun couplage, aucune promesse d'éditeur graphique |

---

## Méthode d'audit

- Lecture de `forge_cli/front.py` (156 lignes)
- Lecture de `package.json` (dépendances et scripts)
- Lecture de `static/src/input.css` (86 lignes)
- Vérification de `static/tailwind.css`
- Lecture des 3 layouts principaux (`base.html`, `admin.html`, `public.html`)
- Grep des références HTMX/Alpine dans `make_crud.py`
- Lecture de `integrations/jinja2/renderer.py`
- Revue des tests existants (`test_front_css_contract.py`, `test_front_js_init.py`, `test_front_layout_contract.py`, 7+37+8 = 52 tests)
- Lecture des sections pertinentes de `docs/front.md`
- Ajout de tests ciblés dans `tests/test_consolidation_front_001.py`

---

## Fichiers audités

| Fichier | Lignes | Responsabilité |
|---|---|---|
| `forge_cli/front.py` | 156 | `forge js:init htmx/alpine/htmx-alpine` |
| `package.json` | ~35 | Tailwind, scripts build:css, dépendances optionnelles |
| `static/src/input.css` | 86 | Source Tailwind v4 + classes custom |
| `static/tailwind.css` | ~800 | CSS compilé (non modifié manuellement) |
| `static/js/app.js` | ~3 | Point d'entrée JS minimal |
| `mvc/views/layouts/base.html` | 35 | Layout de base |
| `mvc/views/layouts/admin.html` | 35 | Layout admin |
| `mvc/views/layouts/public.html` | 25 | Layout public |
| `forge_cli/entities/make_crud.py` | 2242 | CRUD avec HTMX optionnel |
| `integrations/jinja2/renderer.py` | ~40 | Exposition `trans()` dans Jinja2 |
| `docs/front.md` | ~960 | Documentation complète du socle front |

---

## Tailwind CSS

**Version :** `^4.2.2` (Tailwind v4, API `@import "tailwindcss"`)

**Workflow de build :**
```bash
npm install
npm run build:css
# → static/tailwind.css
```

Script déclaré dans `package.json` :
```json
"build:css": "tailwindcss -i ./static/src/input.css -o ./static/tailwind.css --minify"
```

**`static/src/input.css`** contient :
- `@import "tailwindcss"` (ligne 1)
- Classes custom Forge dans `@layer utilities` : couleurs de la palette orange Forge (`#E8651A`), classes landing page, classes de syntaxe

Pas de fichier `tailwind.config.js` — configuration implicite en Tailwind v4 (scan automatique du contenu).

**Tous les layouts** chargent `tailwind.css` : `<link rel="stylesheet" href="/static/tailwind.css">`.

---

## JavaScript Forge

`static/js/app.js` est un point d'entrée minimal :

```javascript
// Forge application JavaScript entrypoint.
// Add project-specific JavaScript here.
```

Il **n'impose pas** HTMX ni Alpine. Chargé dans tous les layouts avec `defer`.

---

## HTMX

**Statut :** optionnel, installé via `forge js:init htmx`.

**Implémentation dans `forge_cli/front.py` :**
- Dépendance npm : `htmx.org@^2.0.0` (paquet officiel)
- Source : `node_modules/htmx.org/dist/htmx.min.js`
- Cible : `static/vendor/htmx/htmx.min.js`
- Commande idempotente : ne modifie pas les versions déjà déclarées

**Workflow :**
1. `forge js:init htmx` → ajoute `htmx.org` dans `package.json`
2. `npm install`
3. `forge js:init htmx` → copie le fichier vendor
4. Charger dans un layout via `{% block scripts %}`

**`static/vendor/htmx/htmx.min.js` non commité** — présent seulement après `npm install`.

---

## Alpine.js

**Statut :** optionnel, installé via `forge js:init alpine`.

**Implémentation dans `forge_cli/front.py` :**
- Dépendance npm : `alpinejs@^3.14.0`
- Source : `node_modules/alpinejs/dist/cdn.min.js`
- Cible : `static/vendor/alpine/alpine.min.js`
- Commande idempotente

**Rôle :** états locaux côté client (menu, modale, accordéon, confirmation, onglets). Alpine **ne transforme pas** Forge en SPA.

---

## HTMX + Alpine

`forge js:init htmx-alpine` exécute séquentiellement `init_htmx()` + `init_alpine()` et retourne :

```python
{"htmx": bool, "alpine": bool}
```

Les deux coexistent sans conflit.

---

## Templates Jinja

### Layouts standard

Trois layouts principaux dans `mvc/views/layouts/` :

| Layout | Utilisation | `tailwind.css` | `{% block scripts %}` | Auto-HTMX | Auto-Alpine |
|---|---|---|---|---|---|
| `base.html` | Héritage général | ✅ | ✅ | ✗ | ✗ |
| `admin.html` | Interface d'administration | ✅ | ✅ | ✗ | ✗ |
| `public.html` | Pages publiques | ✅ | ✅ | ✗ | ✗ |

**Principe clair :** HTMX et Alpine ne sont **jamais injectés automatiquement**. L'utilisateur les charge explicitement via `{% block scripts %}` dans les layouts enfants.

### Composants Jinja

`mvc/views/components/` contient 6 composants réutilisables :
- `alert.html`, `badge.html`, `button.html`, `form_field.html`, `pagination.html`, `table.html`

`mvc/views/partials/` contient 4 partials :
- `csrf.html`, `flash.html`, `form_errors.html`, `pagination.html`

---

## Layouts publics

`public.html` — structure épurée pour les pages publiques génériques (`make:public-page`, `make:public-list`, etc.) :
- Charge Tailwind
- Expose `{% block scripts %}`
- N'impose aucun layout admin

---

## CRUD HTMX

Le CRUD généré par `make_crud.py` utilise HTMX comme **amélioration progressive** :

| Fonctionnalité | Attribut HTMX | Fallback HTML |
|---|---|---|
| Pagination | `hx-get`, `hx-target`, `hx-push-url` | Liens `<a>` standard |
| Recherche | `hx-get`, `hx-target`, `hx-swap` | Formulaire `<form>` standard |
| Suppression | `hx-post`, `hx-target`, `hx-confirm` | Formulaire `<form method="post">` |

**`hx-delete` absent par choix** : `hx-post` est utilisé à la place pour la suppression, afin d'éviter les incompatibilités de compatibilité navigateur et de simplifier la gestion CSRF.

Le CRUD classique reste utilisable sans HTMX (les formulaires fonctionnent avec soumission HTML standard).

---

## i18n dans les templates

La fonction `trans()` est exposée globalement dans l'environnement Jinja2 (`integrations/jinja2/renderer.py`). Elle est utilisée dans tous les générateurs de pages publiques :
- `public_page.py` : `trans('public.page.generated')`
- `public_form.py` : `trans('public.form.submit')`
- `public_list.py` : `trans('public.list.*')`
- `public_contact.py` : `trans('public.contact.*')`
- `make_crud.py` : `trans('common.search')`, `trans('crud.confirm_delete')`

---

## Documentation front

`docs/front.md` (~960 lignes) couvre exhaustivement :

| Section | Lignes |
|---|---|
| Position officielle | 3–13 |
| Pourquoi Tailwind | 14–26 |
| Fichiers utilisés | 27–78 |
| Layouts standard | 79–122 |
| Templates publics | 123–183 |
| Compatibilité i18n | 184–215 |
| Composants Jinja | 304–511 |
| Recompiler le CSS | 512–526 |
| Node.js et npm | 527–538 |
| Initialiser HTMX | 539–577 |
| Initialiser Alpine.js | 578–617 |
| Initialiser HTMX + Alpine | 618–645 |
| Utiliser HTMX avec Forge | 646–821 |
| Utiliser Alpine.js avec Forge | 822–933 |
| Remplacer Tailwind manuellement | 934–945 |
| Ce que Forge ne maintient pas | 946–959 |

---

## Séparation Forge Design

- `forge_cli/front.py` ne référence pas Forge Design
- `docs/front.md` ne promet pas d'éditeur graphique
- Les profils n'imposent aucune dépendance Forge Design
- `docs/forge-design-roadmap.md` existe et n'a pas été modifié
- Les layouts et templates Forge sont indépendants de tout outil Forge Design

---

## Points cohérents

1. **Philosophie respectée** : HTML serveur, Tailwind officiel, HTMX/Alpine optionnels.
2. **Optionnalité explicite** : les vendors ne sont jamais commités, jamais chargés automatiquement.
3. **Bloc `{% block scripts %}`** : mécanisme d'extension propre pour les layouts.
4. **CRUD HTMX progressif** : les formulaires classiques fonctionnent sans JavaScript.
5. **`hx-delete` absent** : décision de compatibilité correcte, `hx-post` utilisé.
6. **Idempotence de `js:init`** : les commandes peuvent être relancées sans effets de bord.
7. **i18n natif** : `trans()` disponible dans tous les templates sans configuration supplémentaire.
8. **Tests robustes** : 52 tests existants + 47 nouveaux = 99+ tests couvrant le front.
9. **Aucun bundler lourd** : pas de webpack, pas de vite dans `package.json`.
10. **Anti-SPA documenté** : `docs/front.md` mentionne explicitement le refus du modèle SPA.

---

## Incohérences détectées

### 1. `js:init` absent de `docs/reference.md` — **mineure**

Les commandes `js:init htmx`, `js:init alpine`, `js:init htmx-alpine` sont documentées dans `docs/front.md` mais ne sont pas listées dans `docs/reference.md`.

**Impact :** utilisateur consultant uniquement `docs/reference.md` peut ne pas trouver les commandes JS.
**Action recommandée :** ticket `CONSOLIDATION-DOC-FRONT-001` — ajouter `js:init` dans `docs/reference.md`.

### 2. Tailwind v4 sans `tailwind.config.js` — **acceptable**

Tailwind v4 utilise une configuration implicite (scan automatique). L'absence de `tailwind.config.js` peut surprendre les développeurs familiers avec Tailwind v3.

**Impact :** documentation de `docs/front.md` couvre ce point ("Recompiler le CSS").
**Action recommandée :** aucune pour Forge 2.0.

---

## Risques restants

| Risque | Niveau | Commentaire |
|---|---|---|
| `js:init` absent de `reference.md` | Faible | Documenté dans `front.md` |
| Tailwind v4 sans config explicite | Faible | Documenté, comportement stable |
| Vendor files non versionnés | Acceptable | Comportement normal npm |

---

## Recommandations

1. **Ticket `CONSOLIDATION-DOC-FRONT-001`** : ajouter `js:init htmx/alpine/htmx-alpine` dans `docs/reference.md`.
2. **Aucune modification fonctionnelle** requise avant Forge 2.0.

---

## Tickets futurs proposés

| Ticket | Sujet |
|---|---|
| `CONSOLIDATION-DOC-FRONT-001` | Ajouter les commandes `js:init` dans `docs/reference.md` |
| `FRONT-PROFILE-001` | Différencier les squelettes front selon les profils (dynamic/multilingual) |

---

## Verdict final

**Le socle front Forge est suffisamment cohérent pour Forge 2.0.**

Tailwind est le CSS officiel, HTMX et Alpine sont optionnels et bien encadrés, les layouts sont propres, le CRUD HTMX est progressif, et l'i18n est natif. La philosophie "HTML serveur d'abord" est respectée dans le code, les tests et la documentation.

Une seule incohérence mineure détectée : les commandes `js:init` absentes de `docs/reference.md` — non bloquant pour Forge 2.0.

**Résultat :** CONSOLIDATION-FRONT-001 — **VALIDÉ**
