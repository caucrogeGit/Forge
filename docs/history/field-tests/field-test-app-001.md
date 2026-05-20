# Rapport — Field Test App 001

**Ticket** : FIELD-TEST-APP-001
**Date** : 2026-05-20
**Objectif** : Valider le flux complet Forge sur une application réelle minimaliste (Article ↔ Tag many-to-many avec champs pivot).

---

## 1. Contexte

Première application de terrain Forge créée en dehors du dépôt framework.
Dossier : `/home/roger/Projets/forge-field-test-app/`

Entités déclarées :
- **Article** : title, slug, content, published, created_at
- **Tag** : name, slug
- **Relation** : many_to_many Article ↔ Tag, pivot `article_tag` avec champs `position` (integer) et `note` (string, nullable)

RBAC : rôles `admin` (CRUD complet) et `reader` (list + show).

---

## 2. Séquence exécutée

| Commande | Résultat |
|---|---|
| `schema:list` | OK |
| `schema:doctor` | OK |
| `entity:validate` | OK (après correction, voir frictions) |
| `build:model` | OK (après corrections, voir frictions) |
| `make:crud Article` | OK (après correction `position nullable`, voir frictions) |
| `make:crud Tag` | OK |
| `make:pivot-crud Article tags --dry-run` | OK |
| `make:pivot-crud Article tags` | OK |
| `rbac:validate` | OK |
| `rbac:audit` | OK |

---

## 3. Frictions observées

### F-001 — Clé `"name"` vs `"entity"` dans les JSON d'entité

**Symptôme** : `entity:validate` échoue avec `'name' is a required property` et
`Additional properties are not allowed ('entity' was unexpected)`.

**Cause** : Documentation interne non synchronisée avec `entity.schema.json`.
La clé attendue est `"name"`, pas `"entity"`.

**Résolution** : Correction manuelle dans `Article.json` et `Tag.json`.

**Suggestion** : Ajouter un exemple canonique dans `docs/entities/` ou dans le
message d'erreur d'`entity:validate`.

---

### F-002 — Structure de dossiers implicite pour `build:model`

**Symptôme** : `build:model` échoue avec
`mvc/entities/media/media.json: fichier JSON d'entite introuvable`
suite à la création involontaire d'un sous-dossier `media/`.

**Cause** : `build:model` scanne tous les sous-dossiers de `mvc/entities/`
(sauf ceux débutant par `__`) et attend `<nom_dossier>/<nom_dossier>.json`.
Un sous-dossier vide ou orphelin déclenche l'erreur.

**Second symptôme** : Les fichiers JSON d'entité étaient initialement placés
directement dans `mvc/entities/` (`Article.json`). `build:model` ignore ces
fichiers racine — seuls les sous-dossiers sont scannés.

**Résolution** :
- Renommage `media/` → `__media/` (ignoré par le scanner)
- Déplacement `Article.json` → `mvc/entities/article/article.json`
- Les noms de dossier doivent être en minuscule (snake_case) pour correspondre
  à la convention `name.lower()` attendue par le validateur.

**Suggestion** : Documenter la structure attendue dans `docs/entities/`
(sous-dossier obligatoire, nom en minuscule). Améliorer le message d'erreur
pour indiquer que les fichiers JSON à la racine sont ignorés.

---

### F-003 — Garde `make:crud` se déclenche sur les deux côtés de la relation

**Symptôme** : `make:crud Article` ET `make:crud Tag` échouent tous les deux
avec : `le pivot article_tag contient des champs obligatoires non gérés par le
CRUD simple : position`.

**Cause** : Le garde est déclenché sur toute entité impliquée dans la relation
(côté `from` ET côté `to`), même si l'entité `Tag` n'est pas le propriétaire
de la création du pivot.

**Comportement attendu** : Le garde est correct du côté `Article` (qui crée le
pivot). Côté `Tag`, le lien inverse `articles` n'implique pas de gestion du
pivot par le CRUD Tag — le blocage est donc conservateur.

**Résolution** : `position` rendu `nullable: true` pour les besoins du test.

**Suggestion** : Évaluer si le garde doit s'appliquer uniquement côté `from`
de la relation many-to-many, ou si le comportement symétrique est intentionnel
(documentation à compléter).

---

## 4. Fichiers générés

### `build:model`
```
mvc/entities/article/article.sql
mvc/entities/article/article_base.py
mvc/entities/article/article.py  (créé)
mvc/entities/article/__init__.py  (créé)
mvc/entities/tag/tag.sql
mvc/entities/tag/tag_base.py
mvc/entities/tag/tag.py  (créé)
mvc/entities/tag/__init__.py  (créé)
mvc/entities/relations.sql
```

### `make:crud Article`
```
mvc/controllers/article_controller.py
mvc/models/article_model.py
mvc/forms/__init__.py
mvc/forms/article_form.py
mvc/views/layouts/app.html
mvc/views/partials/form_errors.html
mvc/views/article/{index,show,form,bulk_delete_confirm}.html
mvc/views/article/{_table,_pagination,_results}.html
```

### `make:crud Tag`
```
mvc/controllers/tag_controller.py
mvc/models/tag_model.py
mvc/forms/tag_form.py
mvc/views/tag/{index,show,form,bulk_delete_confirm}.html
mvc/views/tag/{_table,_pagination,_results}.html
(layouts/app.html et forms/__init__.py : PRÉSERVÉS — write-if-new respecté)
```

### `make:pivot-crud Article tags`
```
mvc/controllers/pivot/article_tags_pivot_controller.py
mvc/templates/pivot/article_tags/index.html
mvc/templates/pivot/article_tags/form.html
```

---

## 5. Points de validation positifs

- **write-if-new respecté** : `app.html` et `forms/__init__.py` préservés lors
  de `make:crud Tag` après `make:crud Article`.
- **rbac:validate + rbac:audit** : 2 rôles, 2 entités, 0 avertissement.
- **make:pivot-crud --dry-run** : liste correcte des 3 fichiers cibles avant
  génération.
- **relations.sql** généré automatiquement par `build:model` (table pivot
  `article_tag` avec clés étrangères, champs `position` et `note`).

---

## 6. Verdict

**FIELD TEST OK** — Le flux complet Forge (déclaration → modèle → CRUD → pivot
→ RBAC) fonctionne de bout en bout. Trois frictions documentées, aucune
bloquante au fond. F-001 et F-002 relèvent de la documentation ; F-003 mérite
évaluation.

---

## 7. Corrections documentaires — FIELD-FIX-001

Les frictions F-001 et F-002 ont été traitées dans le ticket FIELD-FIX-001.

- **F-001** : la documentation rappelle désormais que la clé canonique racine
  est `"name"`, pas `"entity"`. Les pages `entity_architecture.md`,
  `15-minutes.md` et `app-complete-tutorial.md` ont été corrigées ou signalées.
- **F-002** : la page `docs/entities/json-canonique.md` décrit explicitement
  la structure `mvc/entities/<nom>/<nom>.json`, l'emplacement de
  `mvc/entities/relations.json`, et le comportement de `build:model` vis-à-vis
  des sous-dossiers.

**F-003** reste ouvert et sera traité par FIELD-AUDIT-M2M-GUARD-001.
