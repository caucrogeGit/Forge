# Audit CRUD-BULK-ACTIONS-AUDIT-001 — Actions groupées CRUD

## Objectif

Auditer la faisabilité d'actions groupées dans les CRUD générés par Forge :
supprimer plusieurs enregistrements, changer un statut, activer / désactiver,
appliquer une action métier simple.

Ce ticket est un **audit**. Aucune implémentation n'est produite ici.

---

## État actuel du CRUD

### Routes générées

Le générateur `forge make:crud` produit 7 routes par entité :

```
GET    /{plural}              → index   (liste + filtres + pagination + tri)
GET    /{plural}/new          → new     (formulaire de création)
POST   /{plural}              → create  (traitement création)
GET    /{plural}/{id}         → show    (détail)
GET    /{plural}/{id}/edit    → edit    (formulaire de modification)
POST   /{plural}/{id}         → update  (traitement modification)
POST   /{plural}/{id}/delete  → destroy (suppression unitaire)
```

**Aucune route groupée n'existe.** L'ajout d'une action groupée nécessite une
route dédiée, par exemple `POST /{plural}/bulk-delete`.

### Suppression unitaire existante

La suppression unitaire (`destroy`) est déjà protégée :

- **CSRF** : `<input type="hidden" name="csrf_token" value="{{ csrf_token }}">` dans chaque formulaire de suppression.
- **RBAC** : le contrôleur vérifie `@require_permission('{entity}.delete')` si une permission est déclarée.
- **Confirmation** : double confirmation — `onsubmit="return confirm(...)"` côté navigateur, `hx-confirm` côté HTMX.
- **Redirection** : vers la liste avec conservation de `q`, `sort`, `direction`, `filters` et `page` via query string.

### Templates et table

Le partial `_table.html` généré :

- contient une `<table>` avec `<thead>` (colonnes triables) et `<tbody>` (lignes `{% for entity in entities %}`).
- **aucune colonne de case à cocher** n'est générée.
- **aucun formulaire englobant la table** n'existe — chaque suppression a son propre `<form>`.
- la pagination est dans un partial séparé `_pagination.html`, inclus après la table via `_results.html`.

### Filtres, tri et pagination

- Les paramètres `q`, `sort`, `direction` et `filters` sont conservés dans tous les liens de tri et de pagination via des boucles Jinja2 (`pagination.filters.items()`).
- Ces paramètres transitent par query string (GET). Une action groupée en POST doit les propager différemment (champs cachés ou redirection avec query string).

### HTMX

- La liste entière est dans `<div id="crud-results">`.
- Le formulaire de filtres et les liens de pagination ont des attributs `hx-get`, `hx-target="#crud-results"`, `hx-swap="innerHTML"`, `hx-push-url="true"`.
- La suppression unitaire utilise `hx-post` + `hx-target="#crud-results"`.
- Une action groupée POST vers `/bulk-delete` **ne peut pas réutiliser ce mécanisme sans adaptation** : le formulaire multi-cases doit lui-même cibler `#crud-results` ou rediriger classiquement.

### CSRF

Le middleware CSRF de Forge vérifie le token sur toutes les routes POST non exclues.
Toute route `POST /{plural}/bulk-delete` serait protégée **automatiquement** si le groupe de routes n'est pas déclaré avec `csrf=False`.

### RBAC

La permission `{entity}.delete` est déjà déclarée et vérifiée pour la suppression unitaire.
Une suppression groupée peut réutiliser cette même permission côté serveur.
Le bouton d'action groupée doit être conditionné par `{% if can('{entity}.delete') %}` en template.

---

## Besoin fonctionnel

Scénario minimal ciblé (non implémenté dans ce ticket) :

```
liste CRUD
→ cases à cocher par ligne
→ bouton "Supprimer la sélection"
→ POST vers /{plural}/bulk-delete
→ CSRF vérifié automatiquement
→ RBAC vérifié côté serveur
→ IDs validés (entiers, non vides, existants, sans injection)
→ suppressions individuelles avec contrôle
→ redirection vers /{plural} avec filtres conservés
```

---

## Scénarios possibles

| Scénario | Description | Complexité |
|---|---|---|
| A — Suppression groupée minimale | Cases à cocher + POST /bulk-delete, CSRF/RBAC, pas de JS | Faible |
| B — Actions groupées génériques | Plusieurs actions (suppr., statut, activation) via `<select>` | Moyenne |
| C — Sélection totale cross-pages | "Tout sélectionner" across pagination | Élevée |
| D — Actions HTMX sans rechargement | Remplacement partiel via hx-post | Élevée |

**Recommandation : commencer par le Scénario A.**

---

## Sélection des lignes

### Placement de la checkbox

La checkbox doit être dans la première colonne du `<tbody>`, avant les colonnes de données :

```html
<td class="px-4 py-3">
    <input type="checkbox" name="ids" value="{{ contact.Id }}">
</td>
```

Et un `<th>` correspondant dans le `<thead>`.

### Checkbox "tout sélectionner"

- **Sans JavaScript** : impossible de façon native. La case globale nécessite du JS.
- **Recommandation** : ne pas inclure la case "tout sélectionner" dans la première version. Rester 100 % accessible sans JS.
- **Risque** : une case "tout sélectionner" sans limitation de portée peut provoquer des suppressions sur des éléments hors page visible (autres pages de pagination).

### Formulaire englobant la table

La table doit être enveloppée dans un `<form method="post" action="/{plural}/bulk-delete">` avec le token CSRF. Ce `<form>` **remplace** les formulaires de suppression unitaire par ligne — les deux coexistent difficilement dans le même template. La suppression unitaire doit rester dans un formulaire séparé (formulaire imbriqué interdit en HTML).

**Solution la plus simple** : garder la suppression unitaire hors du formulaire groupé, et placer le formulaire groupé autour d'un bouton flottant ou d'un en-tête de tableau.

---

## Routes possibles

### Option 1 — Route par action

```
POST /{plural}/bulk-delete
```

Avantages : nommage explicite, permission claire, testable unitairement.

### Option 2 — Route générique

```
POST /{plural}/bulk
```

Avec un champ `action=delete` dans le formulaire.

Inconvénient : la permission à vérifier dépend du champ `action`, ce qui complexifie le RBAC côté serveur.

**Recommandation : Option 1 — route par action nommée.**

### Comportement sans sélection

Si aucune case n'est cochée, la liste `ids` est vide. Le contrôleur doit :
1. détecter que `ids` est absent ou vide ;
2. rediriger vers la liste avec un message flash informatif (pas d'erreur 500).

---

## CSRF

- Le token CSRF doit être présent dans le formulaire groupé : `<input type="hidden" name="csrf_token" value="{{ csrf_token }}">`
- Le middleware Forge vérifie automatiquement le token sur POST — **pas de configuration supplémentaire** si la route est dans un groupe protégé.
- Sans token ou avec token invalide : réponse 403 automatique.
- Compatible avec `SECURITY-CSRF-AUDIT-001`.

---

## RBAC

- La permission existante `{entity}.delete` est réutilisable pour la suppression groupée.
- Vérification côté serveur obligatoire (`@require_permission` ou équivalent dans le contrôleur `bulk_delete`).
- Bouton visible uniquement si `{% if can('{entity}.delete') %}`.
- **Pas de nouvelle permission spécifique** nécessaire pour le Scénario A.

---

## Validation des IDs

Risques identifiés et protections nécessaires :

| Cas | Protection attendue |
|---|---|
| IDs absents | Redirection silencieuse vers liste |
| IDs vides (`""`) | Ignorer silencieusement |
| IDs non entiers | `ValueError` → 400 Bad Request |
| IDs dupliqués | Dédupliquer avant traitement |
| IDs inexistants | Ignorer (pas d'erreur, on supprime ce qui existe) |
| Trop grand nombre d'IDs | Limite configurable (ex. 100 max) |
| Injection SQL via IDs | **Aucune concaténation directe** — utiliser `IN (?, ?, ?)` avec placeholders |

**Règle absolue** : les IDs ne doivent jamais être concaténés dans une requête SQL.
Utiliser une clause `WHERE id IN (` + `, `.join(["?"] * len(ids)) + `)` avec `params = ids`.

---

## SQL et sécurité

Le modèle généré utilise déjà des requêtes paramétrées pour les filtres (`_ALLOWED_FILTERS` whitelist + `col = ?`). La même discipline s'applique aux IDs groupés :

```python
placeholders = ", ".join(["?"] * len(ids))
cursor.execute(f"DELETE FROM {table} WHERE id IN ({placeholders})", ids)
```

**Pas de risque d'injection SQL si cette règle est respectée.**

---

## Pagination, filtres et tri

### Problème de scope

La sélection par cases à cocher ne porte que sur la **page visible**. Si l'utilisateur est page 2 avec 10 lignes, seules ces 10 lignes peuvent être sélectionnées.

- Une case "tout sélectionner" affichée sur la page 2 ne sélectionne **pas** les pages 1 et 3.
- Ce comportement doit être clairement documenté dans l'UX (label du bouton : "Supprimer les éléments sélectionnés sur cette page").

### Conservation après action

Après suppression groupée, la redirection doit conserver `q`, `sort`, `direction` et `filters` :

```python
redirect_url = f"/{plural}?page=1"
if q: redirect_url += f"&q={q}"
# ... etc.
```

Les paramètres sont disponibles dans la requête POST (champs cachés dans le formulaire) ou dans le Referer.

---

## HTMX

### Première version : sans HTMX

Recommandation : **ne pas inclure HTMX** dans la première version des actions groupées.
Le formulaire POST classique avec redirection est suffisant, plus robuste, et plus simple à tester.

### HTMX éventuel (version suivante)

Si HTMX est ajouté ultérieurement :

- Le formulaire groupé peut avoir `hx-post="/{plural}/bulk-delete"` avec `hx-target="#crud-results"`.
- Le contrôleur bulk_delete doit retourner le partial `_results.html` si la requête est HTMX, ou faire une redirection 302 sinon.
- La détection HTMX se fait via `request.headers.get("HX-Request")`.

**Ne pas complexifier la première version avec HTMX.**

---

## UX

### Confirmation

Sans JavaScript : la suppression groupée se fait sans dialog de confirmation natif.
Options :

1. Page de confirmation intermédiaire (GET → affiche la liste des éléments sélectionnés → POST pour confirmer). Plus sûr, sans JS.
2. Simple formulaire POST direct. Plus rapide, risque de suppression accidentelle.

**Recommandation : page de confirmation intermédiaire pour la première version.**

### Message si aucune sélection

Redirection vers la liste avec un message flash : "Aucun élément sélectionné."

### Retour vers la liste filtrée

La redirection après action groupée doit conserver les paramètres de la liste courante.

---

## Risques identifiés

| Risque | Sévérité | Mitigation |
|---|---|---|
| Suppression accidentelle massive | Élevée | Page de confirmation intermédiaire |
| Contournement RBAC | Critique | Vérification permission côté serveur obligatoire |
| Absence CSRF | Critique | Token CSRF dans le formulaire groupé |
| IDs forgés (hors périmètre utilisateur) | Élevée | Valider que les IDs appartiennent à l'entité (pas de filtre tenant ici, mais validation existence) |
| Injection SQL via IDs | Critique | Placeholders SQL obligatoires |
| Sélection cross-pages non intentionnelle | Moyenne | Documenter la portée (page visible uniquement) |
| Imbrication de formulaires HTML | Élevée | Formulaire groupé séparé du formulaire de filtre |
| Complexité HTMX prématurée | Faible | Première version sans HTMX |
| Casse des tests existants | Faible | Les templates existants ne sont pas modifiés |

---

## Recommandation

**Ne pas implémenter toutes les actions groupées d'un coup.**

Commencer par une **suppression groupée minimale** :

- cases à cocher par ligne dans `_table.html` ;
- formulaire POST vers `/{plural}/bulk-delete` avec CSRF ;
- permission `{entity}.delete` vérifiée côté serveur ;
- IDs validés (entiers, dédupliqués, pas de concaténation SQL) ;
- page de confirmation intermédiaire pour éviter les suppressions accidentelles ;
- redirection vers la liste avec filtres conservés ;
- **pas de JavaScript personnalisé** ;
- **pas de case "tout sélectionner"** dans la première version ;
- **pas de HTMX** dans la première version.

---

## Tickets suivants proposés

### Ticket suivant immédiat

**`CRUD-BULK-DELETE-001` — Ajouter une suppression groupée CRUD minimale**

Périmètre :
- cases à cocher dans `_table.html` ;
- route `POST /{plural}/bulk-delete` ;
- contrôleur `bulk_delete` avec CSRF + RBAC + validation IDs ;
- page de confirmation intermédiaire (template `_bulk_confirm.html`) ;
- redirection avec conservation des filtres ;
- tests (unitaires contrôleur + template) ;
- documentation.

### Tickets suivants possibles

| Ticket | Sujet |
|---|---|
| `CRUD-BULK-STATUS-001` | Action groupée "changer le statut" |
| `CRUD-BULK-ACTIVATE-001` | Action groupée activation / désactivation |
| `CRUD-BULK-ACTIONS-GENERIC-001` | Refactoring vers un mécanisme d'actions génériques |
| `CRUD-BULK-HTMX-001` | Ajout HTMX progressif aux actions groupées |
| `CRUD-BULK-SELECT-ALL-001` | Case "tout sélectionner" avec JS optionnel |
