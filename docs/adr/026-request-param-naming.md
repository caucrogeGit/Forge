# ADR-026 — Nommer les accesseurs de Request par leur source : query et route

## Statut

Accepté — Forge 1.0.0-beta.15 (ticket `HTTP-REQUEST-PARAM-RENAME-001`).

---

## Date

2026-06-07

---

## Contexte

`core.http.request.Request` expose une famille d'accesseurs de données, nommés
**par leur source** :

| Méthode | Source |
|---|---|
| `param(key)` | query string (`?clé=`) |
| `route_param(key)` | chemin de l'URL (`/article/{id}`) |
| `form(key)` | corps de formulaire |
| `json(key)` | corps JSON |
| `header(name)` | en-tête HTTP |
| `file(key)` | fichier téléversé |

Deux noms dénotent par rapport au reste de la famille :

1. **`param` ne nomme pas sa source.** C'est le seul membre dont le nom est
   générique : il ne dit pas que la valeur vient de la query string. Tous les
   autres nomment un lieu précis.
2. **`route_param` est asymétrique** avec `param` (suffixe `_param` que les
   autres lecteurs n'ont pas) et un peu imprécis : une *route* est l'objet
   complet (méthode + motif + handler), alors que la valeur vient du *chemin*.

### Contraintes établies

- `request.path` **existe déjà** comme attribut (la chaîne du chemin,
  `request.py`), convention quasi universelle (Flask, Django, Express). Une
  méthode `path()` entrerait en collision : le nom nu `path` est donc exclu.
- `request.query` et `request.route` sont **libres** (aucun attribut ni méthode
  existant). « route » est déjà le vocabulaire de Forge (`route_param`,
  `router.group`, starters `*-route`).
- Phase bêta pré-1.0 : une rupture interne de l'API se fait **sans alias ni
  dépréciation** (convention de `CLAUDE.md`). C'est la fenêtre idéale ; après le
  tag 1.0 stable, ce renommage serait beaucoup plus coûteux.

---

## Décision

1. **D1** : `Request.param` est renommé **`Request.query`** (lit la query
   string).
2. **D2** : `Request.route_param` est renommé **`Request.route`** (lit un
   paramètre du chemin de route dynamique).
3. **D3** : les autres accesseurs (`form`, `json`, `header`, `file`) sont déjà
   nommés par leur source et **ne changent pas**.
4. **D4** : pas d'alias de compatibilité (rupture franche, pré-1.0). Tous les
   appels sont migrés dans le même chantier : core, starters, tutoriel
   welcome-forge, tests, faux objets de test, contrat public 1.0, doc HTTP.

La paire obtenue est nue, brève, symétrique et nomme la source :
`query` / `route` / `form` / `json` / `header` / `file`.

---

## Conséquences

### Positives

- Chaque accesseur nomme d'où vient la donnée (charte §3 : refuser la magie
  cachée ; §11 : une seule façon claire). `request.query("name")` et
  `request.route("id")` se lisent sans connaître de convention implicite.
- Symétrie de la famille restaurée, sans collision avec `request.path`.

### Limites / Risques

- Rupture de l'API publique du core : tout appel `request.param(...)` /
  `request.route_param(...)` doit être migré (aucun alias).
- Les attributs internes `self.params` (dict query) et `self.route_params`
  (dict chemin), ainsi que les clés `"params"` / `"route_params"` de
  `request.data` (visibles via `Response.debug`), **restent inchangés** : hors
  périmètre de ce renommage de méthodes.

---

## Alternatives écartées

### A — `query_param` / `path_param`

Terminologie HTTP standard et symétrique, mais suffixée alors que le reste de la
famille est nu (`form`, `json`, `header`, `file`). Plus verbeuse sans gain de
clarté décisif. `query` / `route` est plus léger et cohérent avec le vocabulaire
Forge.

### B — `query` / `path`

Le plus court, mais **`path` entre en collision** avec l'attribut existant
`request.path` (la chaîne du chemin). Libérer `path()` exigerait de renommer cet
attribut conventionnel, rupture plus large et sémantiquement trouble (« path »
le chemin vs « path('id') » un paramètre). Écarté.

### C — `query` / `dynamic`

`dynamic` est libre et fait écho au starter « dynamic-route », mais il nomme une
*caractéristique* (le segment est variable), pas une *source* (le chemin),
contredisant le critère retenu. Écarté.

---

## Hors périmètre de cet ADR

- Les attributs `self.params` / `self.route_params` et les clés de
  `request.data` (`"params"`, `"route_params"`).
- Les autres accesseurs (`form`, `json`, `header`, `file`), déjà conformes.

---

## Référence

- Ticket d'implémentation : `HTTP-REQUEST-PARAM-RENAME-001`.
- Code concerné : `core/http/request.py` (`query`, `route`), tous les appelants
  (starters, `docs/starters/welcome-forge/`, tests, `tests/fake_request.py`),
  `docs/reference/http.md`, `docs/reference/public-contract-1.0.md`.
- ADR-003 Convention de langue (API en anglais) : `docs/adr/003-language-convention.md`.
- Charte : `CHARTE_DOC.md` (principes 3, 10, 11).
