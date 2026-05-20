# Audit — Garde make:crud many-to-many avec pivot.fields[]

**Ticket** : FIELD-AUDIT-M2M-GUARD-001
**Date** : 2026-05-20
**Friction d'origine** : F-003 (FIELD-TEST-APP-001)

---

## 1. Résumé

Le garde `make:crud` qui refuse la génération si un pivot possède des
`pivot.fields[]` non-nullable se déclenche sur **les deux côtés** de la
relation many-to-many, alors qu'il ne devrait s'appliquer qu'au côté `from`
(l'entité source qui possède la relation).

Ce comportement est un **bug** — le `raise ValueError` est placé avant
le filtre d'entité courante dans `relations_loader.py`.

**Décision recommandée** : correction dans **FIELD-FIX-M2M-GUARD-001**.

---

## 2. Contexte

Durant FIELD-TEST-APP-001 :

- Entités : `Article` et `Tag`
- Relation : `many_to_many` Article → Tag, pivot `article_tag`
- Champs pivot : `position` (`nullable: false`), `note` (`nullable: true`)

Observation : `make:crud Article` ET `make:crud Tag` ont refusé la génération
avec le même message d'erreur, alors que Tag n'est pas propriétaire du pivot.

---

## 3. Méthode d'audit

- Lecture de `forge_cli/entities/crud/relations_loader.py`
- Lecture de `forge_cli/entities/make_crud.py`
- Exécution de `tests/test_make_crud_pivot_fields_guard.py` (29 tests — OK)
- Exécution de `tests/test_make_crud_many_to_many.py` (passe)
- Exécution de `tests/test_make_crud_many_to_many_canonical.py` (passe)
- Exécution de `tests/test_make_pivot_crud.py` + `test_pivot_advanced_e2e.py`
- Lecture de `docs/entities/pivot-advanced.md` et `docs/entities/pivots-many-to-many.md`

---

## 4. Comportement observé

| Cas | Résultat |
|---|---|
| `make:crud Article` (position nullable: false) | BLOQUÉ — attendu |
| `make:crud Tag` (position nullable: false) | BLOQUÉ — inattendu |
| `make:crud Article` (tous champs nullable: true) | OK |
| `make:crud Tag` (tous champs nullable: true) | OK |
| `make:pivot-crud Article tags` | OK dans tous les cas |

---

## 5. Implémentation actuelle

Fichier : `forge_cli/entities/crud/relations_loader.py`
Fonction : `_load_crud_many_to_many_relations`

```python
for relation in validated_relations:
    if isinstance(relation, ValidatedCanonicalManyToManyRelation):
        incompatible = [pf.name for pf in relation.pivot_fields if not pf.nullable]
        if incompatible:
            field_list = ", ".join(incompatible)
            raise ValueError(           # ← RAISE ICI (ligne ~117)
                f"Relation many_to_many incompatible avec make:crud : "
                f"{relation.from_entity} → {relation.to_entity} "
                f"(pivot {relation.pivot_table}).\n"
                f"Le pivot {relation.pivot_table} contient des champs obligatoires "
                f"non gérés par le CRUD simple : {field_list}.\n"
                f"make:crud synchronise uniquement les identifiants.\n"
                f"Rendez ces champs nullable ou utilisez un module/CRUD pivot dédié."
            )

    m2m_source = relation.from_entity
    # ...
    if m2m_source.lower() not in current_names:   # ← FILTRE ICI (ligne ~135)
        continue
```

**Le `raise ValueError` est exécuté avant le filtre `current_names`.**

Conséquence : pour toute entité impliquée dans une relation `many_to_many`
dont le pivot contient un champ non-nullable, `_load_crud_many_to_many_relations`
lève l'erreur — qu'elle soit côté `from` ou côté `to`.

---

## 6. Cas Article ↔ Tag

Lors de `make:crud Tag` :

1. `current_entity = "Tag"` (`definition["entity"]`)
2. `current_names = {"tag", "tags", "tag"}`
3. Itération sur les relations — trouve `Article → Tag`
4. `isinstance(relation, ValidatedCanonicalManyToManyRelation)` → `True`
5. `incompatible = ["position"]` (non-nullable)
6. **`raise ValueError("Article → Tag ...")`** — avant tout filtre

Le contrôle n'atteint jamais la ligne :
```python
if m2m_source.lower() not in current_names:  # "article" not in {"tag", "tags"}
    continue  # ne sera jamais exécuté
```

---

## 7. Options étudiées

| Option | Description | Avantage | Risque |
|---|---|---|---|
| **A** | Garder le blocage des deux côtés | Évite toute génération CRUD sur des entités liées à un pivot avancé | Trop strict — Tag n'est pas responsable du pivot |
| **B** | Bloquer seulement le côté `from` | Sémantiquement correct — seul Article "possède" le pivot | Nul — Tag ne gère pas le pivot, son CRUD reste cohérent |
| **C** | Ne bloquer aucun côté | `make:crud` reste simple partout | Risque : CRUD Article genère un `<select>` d'IDs sans les attributs pivot — silencieux |
| **D** | Warning non bloquant | Moins restrictif | Risque de masquer une perte fonctionnelle côté `from` |
| **E** | Garder le blocage mais améliorer le message | Stable, plus clair | Ne résout pas le problème côté `to` |

---

## 8. Analyse

### Garde sur le côté `from`

Le garde côté `from` est **intentionnel et correct**. `make:crud Article`
avec un pivot `position` (non-nullable) ne peut pas synchroniser ce champ —
il ne génère que des paires d'IDs. Bloquer la génération évite un CRUD
silencieusement incomplet.

### Garde sur le côté `to`

Le garde côté `to` (Tag dans cet exemple) est un **bug d'implémentation**.

- `make:crud Tag` ne génère aucun formulaire lié au pivot article_tag.
- Tag ne possède pas la relation — il n'a pas à gérer `position`.
- Le CRUD Tag généré ne comporterait aucune référence au pivot.
- Le blocage n'a donc aucune justification fonctionnelle.

### Message d'erreur

Le message est **partiellement clair** :

- Il identifie correctement la relation (`Article → Tag`)
- Il nomme le champ problématique (`position`)
- Il mentionne `make:crud` et le "CRUD simple"
- **Manque** : le nom `make:pivot-crud` n'est pas cité explicitement
- **Manque** : aucune indication sur quel côté est concerné

### Documentation

`pivot-advanced.md` décrit le garde comme s'appliquant quand
"make:crud est bloqué par le garde-fou" — le tableau implique que c'est
l'entité possédant le pivot qui est bloquée, pas le côté inverse.
La documentation ne dit pas que le blocage affecte les deux côtés.

---

## 9. Décision recommandée

**Option B — Bloquer seulement le côté `from`.**

Le correctif est minimal et ciblé :
déplacer le bloc `if incompatible: raise ValueError(...)` à l'intérieur
du filtre `if m2m_source.lower() in current_names:` dans
`_load_crud_many_to_many_relations`.

Structure cible :

```python
for relation in validated_relations:
    if isinstance(relation, ValidatedCanonicalManyToManyRelation):
        m2m_source = relation.from_entity
        m2m_target = relation.to_entity
        # ...
        if m2m_source.lower() not in current_names:
            continue
        # Garde seulement pour le côté source
        incompatible = [pf.name for pf in relation.pivot_fields if not pf.nullable]
        if incompatible:
            raise ValueError(...)
```

Amélioration complémentaire du message : citer `make:pivot-crud` explicitement.

---

## 10. Ticket suivant proposé

**FIELD-FIX-M2M-GUARD-001** — Corriger le garde make:crud pour ne bloquer que
le côté `from` d'une relation many-to-many avec pivot.fields[] non-nullable.

Périmètre :

- Modifier `forge_cli/entities/crud/relations_loader.py`
- Déplacer le garde après le filtre `current_names`
- Améliorer le message d'erreur (citer `make:pivot-crud`)
- Ajouter un test `make:crud Tag` qui vérifie qu'il passe malgré un pivot `from=Article` non-nullable
- Mettre à jour `pivot-advanced.md` pour documenter que seul le côté `from` est concerné

---

## 11. Aucun runtime modifié

Ce ticket est un audit. Aucun fichier de code n'a été modifié.

- Runtime : NON modifié
- make:crud : NON modifié
- Schémas : NON modifiés
- PyPI : NON publié
- Tag : NON créé

---

## 12. Correction — FIELD-FIX-M2M-GUARD-001

Le bug confirmé dans cet audit a été corrigé dans le ticket FIELD-FIX-M2M-GUARD-001.

Le garde `make:crud` lié aux `pivot.fields[]` est désormais appliqué uniquement
après filtrage du côté source de la relation (`if m2m_source.lower() not in current_names: continue`).

État final :

- `make:crud Article` reste bloqué si `Article.tags` contient des champs pivot
  incompatibles avec le CRUD simple (`nullable: false` ou `required: true`) ;
- `make:crud Tag` n'est plus bloqué par la relation inverse — le CRUD Tag se
  génère normalement ;
- `make:pivot-crud Article tags` reste la commande dédiée pour le sous-CRUD pivot ;
- `make:crud` reste neutre vis-à-vis du Pivot advanced généré côté `to`.

Fichier modifié : `forge_cli/entities/crud/relations_loader.py`
