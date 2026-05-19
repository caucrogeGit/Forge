# Décision — Intégration RBAC dans make:crud

**Date** : 2026-05-20
**Ticket** : RBAC-CONTRACT-004-DECIDE-MAKECRUD-RBAC-INTEGRATION
**Statut** : Décision rendue — Option A retenue

---

## 1. Résumé

`make:crud` ne lira **pas** `mvc/security/rbac.json` dans ce cycle de tickets.
Le mécanisme RBAC interne existant (clé `rbac` dans la définition d'entité interne)
reste la seule source de génération de guards CRUD. Le contrat `mvc/security/rbac.json`
sert à la validation du référentiel de rôles/permissions, pas à la génération de code.

---

## 2. Contexte

Les tickets RBAC-CONTRACT-001 à 003 ont :

- décidé que `rbac` est hors de `entity.schema.json` ;
- créé `schemas/rbac.schema.json` pour valider `mvc/security/rbac.json` ;
- ajouté la commande `forge rbac:validate`.

La question ouverte : `make:crud` doit-il lire `mvc/security/rbac.json` ?

---

## 3. Méthode d'audit

**Commandes exécutées** :

```bash
python forge.py schema:list          # 6 schémas OK dont rbac
python forge.py schema:doctor        # OK — ref rbac → common vérifiée
python forge.py rbac:validate --json # valid: true, exists: false (fichier absent)
python forge.py entity:validate      # 2 fichiers valides, 0 erreur
pytest tests/test_make_crud_rbac.py  # 34 tests passent
pytest tests/test_crud_rbac_ui.py    # 22 tests passent
```

**Zones auditées** :

- `forge_cli/entities/make_crud.py` — mécanisme RBAC actuel
- `forge_cli/entities/crud/controller_builder.py` — génération de guards
- `forge_cli/entities/crud/views_builder.py` — guards templates
- `forge_cli/entities/validation.py` — `ALLOWED_ROOT_KEYS`, `_validate_rbac_structure`
- `schemas/rbac.schema.json` — contrat séparé
- `forge_cli/rbac_validate.py` — validation du contrat
- `tests/test_make_crud_rbac.py` — tests internes RBAC
- `tests/test_crud_rbac_ui.py` — tests guards UI

---

## 4. État actuel du contrat RBAC

### 4.1 Deux mécanismes RBAC coexistent

**Mécanisme A — RBAC interne à la définition d'entité** (actif, testé) :

- Clé `rbac` dans le format interne (avec `entity`, `sql_type`...) via `validation.py`
- `make_crud.py` lit `definition.get("rbac")` (ligne 242)
- Passe `rbac` aux builders : `build_index_view`, `build_table_partial`, `build_show_view`
- `controller_builder.py` génère `@require_permission("article.list")` si `rbac` présent
- Testé par 56 tests (`test_make_crud_rbac.py` et `test_crud_rbac_ui.py`)
- **Ce mécanisme fonctionne aujourd'hui**

**Mécanisme B — Contrat RBAC séparé** (créé, non branché) :

- Fichier `mvc/security/rbac.json` validable avec `rbac.schema.json`
- Commande `forge rbac:validate` disponible
- Structure : `schema_version`, `entities.*.permissions`, `roles.*`
- **Ce mécanisme est validable mais n'est pas lu par make:crud**

### 4.2 Différence structurelle

Le contrat `mvc/security/rbac.json` couvre des préoccupations différentes de la
clé `rbac` dans les entités :

| Aspect | Clé `rbac` interne | `mvc/security/rbac.json` |
|---|---|---|
| Niveau | Par entité | Global projet |
| Contenu | Actions → permissions | Rôles → permissions + entités → permissions |
| Usage actuel | Génération guards CRUD | Validation contractuelle |
| Runtime | Guards `@require_permission` | Référentiel d'autorisation |
| Format | Format interne entité | Fichier autonome |

---

## 5. Usages RBAC dans make:crud

`make_crud.py` lit `rbac` uniquement depuis la définition interne normalisée.
Aucune lecture de `mvc/security/rbac.json` n'est présente ni prévue.

Le pipeline est :
```
entity.json (interne, avec "rbac")
  → validate_entity_definition()
  → make_crud() → definition.get("rbac")
  → build_controller(rbac=rbac)
  → @require_permission("article.list")
```

Un branchement de `mvc/security/rbac.json` nécessiterait :
1. Détecter l'entité dans `mvc/security/rbac.json` par correspondance de nom
2. Extraire ses permissions
3. Les passer aux builders sous le même format que la clé `rbac` interne
4. Gérer les conflits (entité avec `rbac` interne ET entrée dans `rbac.json`)

---

## 6. Options étudiées

### Option A — Ne pas brancher make:crud (recommandée)

`make:crud` ignore `mvc/security/rbac.json`. Le RBAC interne existant fonctionne.
Le contrat séparé reste un référentiel de validation.

**Avantages** :
- Zéro risque de régression sur 56 tests existants
- Séparation claire : contrat = validation runtime, entité interne = génération CRUD
- `mvc/security/rbac.json` peut évoluer sans casser la génération
- Cohérence avec le principe 8 — noyau minimal

**Inconvénient** :
- Le contrat `mvc/security/rbac.json` n'influence pas la génération de code

### Option B — Génération de métadonnées ou commentaires

`make:crud` lit `mvc/security/rbac.json` et génère des commentaires dans les
contrôleurs, listant les permissions attendues.

**Avantages** : utile pour la documentation développeur.

**Inconvénients** :
- Couplage make:crud ↔ fichier RBAC optionnel
- N'apporte pas de sécurité réelle
- Commentaires stales si le contrat évolue

**Verdict** : valeur faible, couplage injustifié.

### Option C — Génération de guards dans les contrôleurs

`make:crud` lit les permissions depuis `mvc/security/rbac.json` et génère des
guards `@require_permission(...)` dans les contrôleurs générés.

**Avantages** : sécurité applicative concrète dès la génération.

**Inconvénients** :
- Fort couplage core CRUD ↔ module RBAC opt-in
- Risque de casser les projets sans `forge-mvc-rbac`
- Duplique le mécanisme interne existant
- Nécessite une correspondance entité-nom entre `rbac.json` et les entités générées
- Conflits potentiels avec le mécanisme A existant

**Verdict** : périmètre trop large pour ce ticket ; peut être RBAC-CRUD-001.

### Option D — Module opt-in RBAC enrichit les contrôleurs

`make:crud` core reste neutre. Un module ou une commande dédiée (`rbac:apply` ?)
injecte les guards dans les contrôleurs existants en lisant `mvc/security/rbac.json`.

**Avantages** :
- CRUD core simple
- RBAC vraiment optionnel
- Injection différée, non-destructive

**Inconvénient** :
- Plus complexe à construire et à utiliser
- Nécessite une commande dédiée

**Verdict** : meilleur design à long terme, mais hors périmètre actuel.

---

## 7. Risques du branchement prématuré

1. **Couplage core/RBAC** : si `make:crud` lit `mvc/security/rbac.json`, il dépend
   implicitement de `forge-mvc-rbac`. Forge Core devient lié à un module opt-in.

2. **Double mécanisme** : le mécanisme A (clé `rbac` interne) et le mécanisme B
   (contrat séparé) pourraient entrer en conflit. Lequel prime ?

3. **Régression** : 56 tests utilisent le mécanisme A avec des entités internes.
   Un branchement au mécanisme B devrait les adapter ou les préserver.

4. **write-if-new** : `make:crud` ne surécrit pas les fichiers existants. Si des
   guards sont générés depuis le contrat, les contrôleurs existants ne seraient pas
   mis à jour automatiquement. Risque d'incohérence silencieuse.

---

## 8. Décision recommandée

**Option A retenue : ne pas brancher `make:crud` à `mvc/security/rbac.json`.**

**Justification** :

1. **Mécanisme existant fonctionnel** : le mécanisme A (clé `rbac` interne) génère
   déjà des guards. Il est stable, testé, et ne nécessite pas de modification.

2. **Séparation des responsabilités** : `mvc/security/rbac.json` est un référentiel
   d'autorisation RUNTIME (qui peut quoi), pas un contrat de génération de code.
   `make:crud` génère du code à partir des définitions d'entités.

3. **Principe 4 — Préserver le code utilisateur** : les contrôleurs générés sont
   sous contrôle utilisateur. Les modifier en lisant un fichier externe serait
   une écriture invisible.

4. **Principe 8 — Noyau minimal** : le RBAC est opt-in. Core ne doit pas en dépendre.

5. **Pas de couplage prématuré** : faire dépendre `make:crud` de `mvc/security/rbac.json`
   créerait un couplage dont la valeur n'est pas encore démontrée.

---

## 9. État final après RBAC-CONTRACT-004

| Élément | État |
|---|---|
| `make:crud` lit `mvc/security/rbac.json` | NON |
| Mécanisme RBAC interne (clé `rbac`) | Actif, non modifié |
| Runtime RBAC branché | NON |
| `mvc/security/rbac.json` validable | OUI (via `rbac:validate`) |
| `rbac.schema.json` | Actif, 6 schémas au registre |

---

## 10. Tickets futurs proposés

| Ticket | Objectif | Priorité |
|---|---|---|
| `RBAC-CRUD-001` | Brancher `make:crud` au contrat via Option C ou D | Faible (optionnel) |
| `RBAC-CLOSE-001` | Clôturer le bloc contractuel RBAC sans branchement CRUD | Recommandé si blocage résolu |

**Recommandation** : poursuivre avec `RBAC-CLOSE-001` — documenter la clôture du
bloc RBAC contractuel et proposer un chemin vers l'intégration CRUD dans un ticket
futur explicite.
