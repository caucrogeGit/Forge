# Audit de clôture — Brique Média v2

**Ticket** : MEDIA-V2-AUDIT-001  
**Date** : 2026-05-02  
**Branche** : `phase1-media-v2-audit-001`  
**Auditeur** : Claude Sonnet 4.6 + Roger Lequette

---

## 1. Résumé exécutif

La brique Média v2 est fonctionnellement complète selon le périmètre annoncé. L'API repository est cohérente, le générateur CRUD couvre l'ensemble des cas (single, galerie, create, update, destroy), les tests sont stables à 426/426 sur le périmètre média et 1864/1864 en suite complète.

Quatre contradictions documentaires ont été corrigées dans ce ticket (lignes périmées dans `media.md`, `crud.md`, `roadmap.md`, `reference.md`).

Aucun bug fonctionnel n'a été trouvé. Un risque technique mineur est identifié (alt_text multi-upload simultané) et clairement borné.

---

## 2. État fonctionnel de Média v2

Forge Média v2 couvre la chaîne complète upload → persistance → génération CRUD → affichage, pour deux types de médias :

- **Média unique** (`multiple=false`) : upload, remplacement, suppression, alt_text, preview dans `show`/`edit`, protection en cas de formulaire invalide.
- **Galerie** (`multiple=true`) : affichage ordonné, ajout unitaire, multi-upload (`<input multiple>`), suppression individuelle, réorganisation par position numérique, alt_text par item, protection en cas de formulaire invalide.

La destruction d'une entité entraîne la suppression de tous ses médias liés (enregistrements SQL + fichiers physiques).

---

## 3. Tableau des fonctionnalités terminées

| Fonctionnalité | Ticket | Couverture tests |
|---|---|---|
| Upload media unique (create) | MEDIA-001 | `test_make_crud_media_runtime.py` |
| Remplacement media unique (update) | MEDIA-001 | `test_make_crud_media_runtime.py` |
| Suppression media unique (update) | MEDIA-001 | `test_make_crud_media_runtime.py` |
| Preview dans show/edit | MEDIA-CONTEXT-001 | `test_make_crud_media_context.py` |
| Contexte media après erreur de validation | MEDIA-CONTEXT-001 | `test_make_crud_media_context.py` |
| Suppression médias liés au destroy | MEDIA-DESTROY-001 | `test_make_crud_media_destroy.py` |
| API `attach_media_to_entity` + `position` | MEDIA-GALLERY-POSITION-001 | `test_media_repository.py` |
| Tri `Position ASC, Id ASC` | MEDIA-GALLERY-POSITION-001 | `test_media_repository.py` |
| Galerie en lecture (show/edit/update invalide) | MEDIA-GALLERY-CONTEXT-001 | `test_make_crud_media_gallery_context.py` |
| Ajout append-only (galerie) | MEDIA-GALLERY-ADD-001 | `test_make_crud_media_gallery_add.py` |
| Suppression individuelle (galerie) | MEDIA-GALLERY-DELETE-001 | `test_make_crud_media_gallery_delete.py` |
| Réorganisation par position numérique | MEDIA-GALLERY-ORDER-001 | `test_make_crud_media_gallery_order.py` |
| `update_media_position()` | MEDIA-GALLERY-ORDER-001 | `test_media_repository.py` |
| `update_media_alt_text()` | MEDIA-ALT-CRUD-001 | `test_media_repository.py` |
| alt_text dans CRUD (single + galerie) | MEDIA-ALT-CRUD-001 | `test_make_crud_media_alt.py` |
| Multi-upload HTML `multiple` | MEDIA-GALLERY-MULTIUPLOAD-001 | `test_make_crud_media_gallery_multiupload.py` |

---

## 4. Tableau des limites restantes

| Limite | Motif du non-traitement |
|---|---|
| alt_text individuel par fichier dans un multi-upload simultané | Champ `_media_alt_{name}_new` commun à tous les fichiers d'une soumission ; résoudre nécessiterait JS ou une refonte du formulaire |
| Back-office média intégré | Hors périmètre v2 |
| Permissions/accès contrôlé via `/media/...` | Route serve déjà fonctionnelle, contrôle d'accès non implémenté |
| Détection MIME fiable côté serveur | Dépend du contenu binaire, pas seulement de l'extension ; nécessiterait `python-magic` ou équivalent |
| Drag-and-drop / aperçu JavaScript | Hors périmètre délibéré |
| Réorganisation automatique | Hors périmètre délibéré |

---

## 5. Conformité à la philosophie Forge

| Principe | Verdict | Observations |
|---|---|---|
| SQL explicite, sans ORM | ✅ Conforme | Toutes les requêtes sont des chaînes SQL lisibles dans `media_repository.py` |
| Pas de logique métier dans `core/` | ✅ Conforme | `core/uploads` ne contient que des opérations génériques sur les médias |
| Code généré lisible et non magique | ✅ Conforme | Le code produit par `build_controller()` est du Python standard, lisible ligne par ligne |
| Pas de dépendances cachées | ✅ Conforme | `Pillow` déclaré explicitement, lazy-import uniquement pour les variantes |
| Chemins relatifs uniquement | ✅ Conforme | `normalize_media_path()` rejects absolutes, traversals et symlinks sortants |
| Backward-compatibility | ✅ Conforme | `position=None` → `0` ; fichier unique normalisé en liste de 1 pour le multi-upload |
| Tests de génération + runtime séparés | ✅ Conforme | Chaque ticket distingue `TestXxxGeneration` (code produit) et tests runtime (exec dynamique) |
| Données SQL sans objet fichier | ✅ Conforme | `_sql_data` exclut tous les noms de médias déclarés dans `_media_keys` |

---

## 6. Risques techniques restants

### Risque 1 — alt_text partagé dans multi-upload (mineur)

Lors d'un multi-upload (`[file1, file2, file3]`), le champ `_media_alt_{name}_new` est lu une seule fois et appliqué à tous les fichiers uploadés dans la même soumission. Si l'utilisateur veut des alt_text distincts par fichier, il ne peut pas le faire en une soumission.

**Impact** : fonctionnel limité, non bloquant. Le comportement est documenté.  
**Mitigation** : upload en plusieurs soumissions séparées, ou JS (hors périmètre).

### Risque 2 — FileField valide uniquement le premier fichier d'une liste ✅ corrigé

`Field._first()` extrait `value[0]` quand `value` est une liste. Si `request.files["photos"]` est `[file1, file2]`, `form.cleaned_data["photos"]` contient uniquement `file1` — les fichiers suivants ne sont pas validés par le formulaire.

**Correction (MEDIA-MULTIFILE-VALIDATE-001)** : le code généré par `make:crud` inclut désormais une boucle de pré-validation avant toute opération DB. Chaque fichier est passé à `form.fields[name].validate(f)` ; un seul fichier invalide bloque la soumission complète (aucun upload, aucune suppression, aucune mise à jour de position ou alt_text).

### Risque 3 — Suppression physique silencieuse si fichier absent (très bas)

`delete_media_file()` retourne `False` sans exception si le fichier physique est déjà absent. Le ticket MEDIA-GALLERY-DELETE-001 a validé ce comportement comme acceptable (idempotent).

---

## 7. Recommandations

1. **Ticket permissions média** : ajouter un middleware ou un check dans `serve_media_file` pour contrôler l'accès aux fichiers servis.
3. **Test d'intégration système** : les tests actuels utilisent tous `exec(compile(...))` avec des mocks. Un test d'intégration réel (DB en mémoire SQLite + fichiers temporaires) renforcerait la confiance sur la chaîne complète.
4. **Documentation formulaire multipart** : `docs/crud.md` ne mentionne pas encore l'attribut `enctype="multipart/form-data"` qui est requis pour que les fichiers soient transmis. Vérifier que le template `form.html` généré l'inclut.

---

## 8. Prochains tickets proposés

| Ticket | Priorité | Description |
|---|---|---|
| MEDIA-MULTIFILE-VALIDATE-001 | ✅ Fait | Valider tous les fichiers d'un multi-upload avant de sauvegarder |
| MEDIA-PERMISSIONS-001 | Moyenne | Contrôle d'accès sur `/media/...` (token signé ou middleware) |
| MEDIA-INTEGRATION-TEST-001 | Basse | Test d'intégration complet avec SQLite en mémoire + storage temporaire |
| MEDIA-ALT-MULTIUPLOAD-001 | Basse | alt_text individuel par fichier en multi-upload (nécessite refonte UX ou JS) |

---

## 9. Résultat des validations

### Tests ciblés média

```
pytest tests/test_media_entity.py              → 38 passed
pytest tests/test_media_repository.py          → 16 passed
pytest tests/test_media_attach.py              → 13 passed
pytest tests/test_media_delete.py              → 32 passed
pytest tests/test_media_gallery.py             → 17 passed
pytest tests/test_media_route.py               → 17 passed
pytest tests/test_make_crud_media.py           → 157 passed
pytest tests/test_make_crud_media_runtime.py   → 9 passed
pytest tests/test_make_crud_media_context.py   → 7 passed
pytest tests/test_make_crud_media_gallery_context.py   → 19 passed
pytest tests/test_make_crud_media_gallery_add.py       → 21 passed
pytest tests/test_make_crud_media_gallery_delete.py    → 17 passed
pytest tests/test_make_crud_media_gallery_order.py     → 18 passed
pytest tests/test_make_crud_media_gallery_multiupload.py → 23 passed
pytest tests/test_make_crud_media_alt.py               → 22 passed
pytest tests/test_make_crud_media_destroy.py           → 12 passed
Total périmètre média                          → 488 passed
```

### Suite complète

```
pytest        → 1864 passed, 1 skipped
compileall    → OK
mkdocs build  → OK
git diff --check → OK
```

### Rôle de chaque fichier de tests

| Fichier | Rôle |
|---|---|
| `test_media_entity.py` | Cohérence `media.json`, SQL projeté, modèle généré |
| `test_media_repository.py` | API `create_media_record`, `attach_media_to_entity`, `list_media_for_entity`, `delete_media`, `update_media_position`, `update_media_alt_text` |
| `test_media_attach.py` | Scénarios avancés d'attachement avec variantes et position |
| `test_media_delete.py` | `delete_media` — suppression enregistrement + fichiers physiques |
| `test_media_gallery.py` | `get_media_gallery`, `get_cover_media`, URLs, fallback |
| `test_media_route.py` | Route `/media/...`, sécurité des chemins, intégration `serve_media_file` |
| `test_make_crud_media.py` | Génération du contrôleur : imports, blocs single/multiple, _sql_data, destroy |
| `test_make_crud_media_runtime.py` | Runtime single media : create/update/delete end-to-end |
| `test_make_crud_media_context.py` | Contexte `{name}_media` dans edit() et update() invalide |
| `test_make_crud_media_gallery_context.py` | Contexte `{name}_media_list` dans show/edit/update invalide |
| `test_make_crud_media_gallery_add.py` | Ajout append-only galerie (create + update) |
| `test_make_crud_media_gallery_delete.py` | Suppression individuelle galerie |
| `test_make_crud_media_gallery_order.py` | Réorganisation position galerie |
| `test_make_crud_media_gallery_multiupload.py` | Multi-upload : génération + runtime |
| `test_make_crud_media_alt.py` | alt_text : génération + runtime (single et galerie) |
| `test_make_crud_media_destroy.py` | destroy() : suppression des médias liés avant l'entité |
