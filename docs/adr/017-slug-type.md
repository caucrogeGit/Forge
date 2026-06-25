# ADR-017 : Type `slug` et module URL-slug canonique

## Statut

Acceptée

> Décision-cadre de la Phase 2 de la [roadmap beta.13](../roadmap/beta13-roadmap.md).
> Implémentée par `SLUG-CORE-001` (module), `SLUG-VALIDATION-001`,
> `SLUG-SQL-CRUD-001`, `SLUG-ROUTING-001`.

---

## Contexte

Les URLs publiques générées par Forge restent faibles sans slug
(`/articles/42` plutôt que `/articles/premier-contact`). Le slug est
nécessaire pour les pages publiques, catalogues, blogs : URLs lisibles,
partageables, SEO-friendly.

L'audit de l'existant (`BETA13-EXISTING-AUDIT-001`) révèle un terrain
**partiellement défriché mais incohérent** :

- **`cli/public_page._slugify`**, un **validateur strict** (kebab-case,
  `[a-z0-9-]`) qui **rejette les accents** (`ValueError` sur « Écrire ») ; ce
  n'est **pas** un générateur. 1 seul usage.
- **`cli/entities/migrations.slugify_migration_name`**, un
  **transformeur snake_case** (`_`) pour les **noms de fichiers de
  migration** : concept **différent** d'une URL slug (format et finalité
  distincts).
- **type `slug`** déjà reconnu dans le contrat d'entité
  (`cli/entities/validation.py`) + `SlugField` dans le CRUD, **sans
  logique de génération**.

Trois objets « slug » coexistent donc, avec des contrats divergents, risque
de duplication (charte §11) si on ajoute naïvement une 4ᵉ fonction.

---

## Décision

### D1 : Deux concepts distincts, nommés clairement

- **URL slug** (kebab-case `-`, pour les URLs publiques) → **un seul module
  canonique `core/http/slug.py`**.
- **Nom de fichier de migration** (snake_case `_`) → reste
  `slugify_migration_name`, **séparé**. Ce **n'est pas** une URL slug ; un
  commentaire le précise pour éviter toute fusion future.

### D2 : Module canonique `core/http/slug.py` (runtime, stdlib seul)

Deux fonctions publiques, **dépendances stdlib uniquement** (`unicodedata`,
`re`), respect du runtime minimal (charte) :

```python
def slugify(text: str, *, max_length: int = 180) -> str
def is_valid_slug(value: str, *, max_length: int = 180) -> bool
```

- **`slugify`** *transforme* n'importe quel texte en URL slug : translittération
  des accents via `unicodedata.normalize("NFKD", …)` (« Écrire avec Forge ! »
  → `ecrire-avec-forge`), minuscules, tout caractère non `[a-z0-9]` → `-`,
  tirets compactés, bordures retirées, longueur bornée. Ne lève **que** si le
  résultat est vide (entrée sans aucun caractère exploitable).
- **`is_valid_slug`** *valide* un slug existant : **path-safe** (rejette `/`,
  `\`, `..`), correspond à `[a-z0-9]+(?:-[a-z0-9]+)*`, longueur ≤ `max_length`.

Le runtime (contrôleurs/modèles générés) et le CLI (codegen) importent ce même
module. `cli/public_page._slugify` est **remplacé** par `core.http.slug`
(§11 : une seule implémentation URL-slug).

### D3 : Le type `slug` dans le contrat d'entité

`slug` est un type de champ de **premier rang** du contrat d'entité JSON
(au même titre que `string`, `email`…), validé par le contrat (ADR-013) :

```json
{ "name": "slug", "type": "slug", "required": true, "unique": true }
```

Sémantique : identifiant URL-safe d'une ressource. La génération SQL produit
`VARCHAR(180)` + contrainte `UNIQUE` visible (charte « SQL visible »).

### D4 : Unicité : rejet des doublons (pas de suffixe auto en b13)

Le CRUD généré refuse un slug en doublon avec une **erreur claire**. Le
suffixe automatique (`mon-article-2`) introduit une complexité de
concurrence (race sur insert) non justifiée en dernière beta → **reporté
après 1.0**.

### D5 : Périmètre b13

Inclus : module canonique, validation, type d'entité, génération SQL/CRUD,
routing public par slug (`SLUG-ROUTING-001`).
**Exclus (post-1.0)** : suffixe auto, `slug_history`, redirections 301,
sitemap, slugs multilingues.

---

## Conséquences

- `public_page._slugify` change de comportement : il **translittère** les
  accents au lieu de les rejeter (plus utile), ses tests sont ajustés.
- `slugify_migration_name` est **inchangé** mais documenté comme distinct.
- Le contrat d'entité gagne un type de premier rang `slug` → garde-fou de
  complétude (§10) : SQL, validation, CRUD, doc cohérents.
- Nouveau module runtime `core/http/slug.py` testé indépendamment.

---

## Alternatives considérées

**Fusionner les 3 « slug » en une fonction.** Écarté : `slugify_migration_name`
produit du snake_case pour des **noms de fichiers**, pas des URLs, fusionner
casserait les migrations. Les deux concepts restent séparés (D1).

**Option « slug » comme simple drapeau sur un champ `string`**
(`{"type": "string", "slug": true}`). Écarté au profit d'un **type dédié**
(D3) : plus explicite pour les générateurs, les tests et la doc, conforme à
« une seule façon » (§11).

**Dépendance externe (`python-slugify`, `unidecode`).** Écarté :
`unicodedata` (stdlib) suffit pour la translittération NFKD ; le runtime
minimal de Forge n'accueille pas de dépendance pour ça.

**Suffixe automatique `-2/-3` dès b13.** Écarté : race conditions sur insert
concurrent, complexité non justifiée en dernière beta (D4).

---

## Liens

- Charte : §10 (contrat de complétude), §11 (une seule façon), « SQL visible »,
  runtime minimal.
- [ADR-013](013-nullable-required-contract-policy.md), politique du contrat
  d'entité (nullable/required).
- [Roadmap beta.13](../roadmap/beta13-roadmap.md), Phase 2.
