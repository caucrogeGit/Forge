# Audit — MEDIA-CORE-BOUNDARY-AUDIT-001

## Objectif

Auditer la frontière entre le code média générique du core et le code applicatif
qui doit migrer vers le module opt-in `forge-mvc-media`.

Cet audit ne déplace aucun code, ne crée aucun paquet, ne modifie aucun runtime.
Il établit la carte précise de ce qui doit bouger et pourquoi.

---

## Méthode

Commandes exécutées :

```bash
ls core/uploads/
wc -l core/uploads/*.py
grep -n "from core.database\|import database\|core\.database" core/uploads/*.py
grep -n "from core.uploads\|import core.uploads" forge_cli/entities/crud/controller_builder.py
grep -n "from core.uploads\|import core.uploads" forge_cli/public_list.py
grep -rn "media_repository\|media_gallery" forge_cli/
grep -rn "from core.uploads" tests/ | wc -l
cat core/uploads/media_repository.py
cat core/uploads/media_gallery.py
cat core/uploads/__init__.py
cat mvc/entities/media/media.sql
```

Lecture directe des 8 fichiers sources de `core/uploads/` et des générateurs
CLI concernés.

---

## Synthèse

`core/uploads/` contient actuellement **deux natures de code distinctes** :

| Nature | Fichiers | Destination |
|---|---|---|
| Générique — utilitaires filesystem, validation, image | 6 fichiers | **Reste dans core** |
| Applicatif — SQL sur table `media`, couplé à `core.database` | 2 fichiers | **Vers `forge-mvc-media`** |

La frontière est nette. Le code générique n'importe jamais `core.database`.
Le code applicatif fait des requêtes SQL contre une table `media` dont le schéma
est défini dans `mvc/entities/media/media.sql`.

---

## Carte actuelle du média

### `core/uploads/` — 8 fichiers

| Fichier | Lignes | Nature | Raison |
|---|---|---|---|
| `exceptions.py` | 11 | CORE_GÉNÉRIQUE | Hiérarchie d'exceptions UploadError, sans import externe |
| `validators.py` | 67 | CORE_GÉNÉRIQUE | `validate_upload_metadata`, `validate_extension`, `validate_mime_type`, `validate_size` — aucun accès BDD |
| `storage.py` | 101 | CORE_GÉNÉRIQUE | `save_bytes`, `delete_file`, `normalize_media_path`, `is_safe_media_path` — pur filesystem avec protection anti-traversal |
| `manager.py` | 90 | CORE_GÉNÉRIQUE | `SavedUpload`, `save_upload`, `serve_media_file`, `delete_media_file` — compose validators + storage |
| `image.py` | 110 | CORE_GÉNÉRIQUE | `save_image`, `generate_image_variants`, `image_variant_paths` — utilise Pillow (dep runtime déclarée) |
| `rate_limit.py` | 41 | CORE_GÉNÉRIQUE | `is_upload_rate_limited`, `record_upload_attempt` — dict en mémoire, thread-safe |
| `media_repository.py` | ~110 | OPTIN_MEDIA | SQL sur table `media`, import tardif `core.database` |
| `media_gallery.py` | ~45 | OPTIN_MEDIA | `get_media_gallery`, `get_cover_media` — dépend de `media_repository` |

### Autres fichiers liés au média

| Fichier | Nature |
|---|---|
| `mvc/entities/media/media.sql` | OPTIN_MEDIA — définit la table `media` avec `EntityName`, `EntityId` |
| `mvc/entities/media/media_base.py` | OPTIN_MEDIA — classe générée par le générateur d'entités |
| `mvc/entities/media/media.py` | OPTIN_MEDIA — classe applicative héritant de MediaBase |
| `forge_cli/uploads.py` | CORE_GÉNÉRIQUE — commandes `upload:init` et `media:init`, pas de SQL |

---

## Éléments à conserver dans le core

### `core/uploads/exceptions.py`

Hiérarchie `UploadError` → `UploadTooLargeError`, `UploadInvalidExtensionError`,
`UploadInvalidMimeTypeError`, `UploadStorageError`. Aucune dépendance. Doit rester
dans core pour que les handlers d'erreur HTTP puissent être déclarés sans le module opt-in.

### `core/uploads/validators.py`

`validate_upload_metadata(file, config)` — vérifie extension, MIME type, taille
contre une config applicative. Pure Python, sans BDD ni filesystem.

### `core/uploads/storage.py`

Protection anti-path-traversal robuste (`posixpath.normpath`, `os.path.commonpath`,
blocage des schémas URI). `save_bytes`, `delete_file`, `normalize_media_path`.
Aucune connaissance de la table `media`.

### `core/uploads/manager.py`

`save_upload(file, category, config, *, entity_name, entity_id)` — orchestre
validators + storage, retourne un `SavedUpload` dataclass (sans SQL).
`serve_media_file(path, media_root)` — lit et sert un fichier via `Response`.

### `core/uploads/image.py`

`save_image`, `generate_image_variants` (Pillow), `MediaRecord` dataclass.
`MediaRecord` est générique : ses champs (`filename`, `path`, `category`, `size`,
`mime_type`, `entity_name`, `entity_id`, `usage`, `position`, `is_main`) sont des
métadonnées de transfert — pas un objet persistant avec SQL.

### `core/uploads/rate_limit.py`

Rate limiting en mémoire par IP. Générique, sans BDD.

---

## Éléments à extraire vers forge-mvc-media

### `core/uploads/media_repository.py`

**Raison** : importe `core.database` (import tardif à la ligne ~4 de chaque
fonction), exécute des requêtes SQL directes sur la table `media`.

Fonctions concernées :
- `create_media_record(record: MediaRecord) -> int`
- `attach_media_to_entity(media_id, entity_name, entity_id)`
- `get_media_record(media_id) -> dict | None`
- `list_media_for_entity(entity_name, entity_id, *, role) -> list[dict]`
- `update_media_alt_text(media_id, alt_text)`
- `update_media_position(media_id, position)`
- `delete_media_record(media_id)`
- `delete_media(media_id, media_root) -> bool`

Ces fonctions supposent l'existence de la table `media` avec les colonnes
`Id, EntityName, EntityId, Path, OriginalName, MimeType, Size, Role, Position,
AltText, CreatedAt`.

### `core/uploads/media_gallery.py`

**Raison** : dépend entièrement de `media_repository.list_media_for_entity`.
Ne peut pas fonctionner sans la table `media`.

Fonctions concernées :
- `media_url(path) -> str` — calcule l'URL `/media/{path}`
- `get_media_gallery(entity_name, entity_id, *, role="gallery") -> list[dict]`
- `get_cover_media(entity_name, entity_id, *, role="cover", fallback_to_gallery) -> dict | None`

Note : `media_url` est conceptuellement générique mais est couplée aux chemins
définis par `media_repository` — son déplacement avec la gallerie est cohérent.

---

## Usages dans les générateurs

Deux générateurs CLI produisent du code qui importe des fonctions opt-in depuis
`core.uploads`. Ils devront être mis à jour lors de l'extraction (ticket 11.4).

### `forge_cli/entities/crud/controller_builder.py`

Ligne ~98 (template `--media`) :

```python
from core.uploads import (
    attach_media_to_entity, delete_media, get_cover_media,
    list_media_for_entity, save_upload, update_media_alt_text,
    update_media_position,
)
```

Après extraction, les fonctions `attach_media_to_entity`, `delete_media`,
`get_cover_media`, `list_media_for_entity`, `update_media_alt_text`,
`update_media_position` viendront de `forge_mvc_media.uploads` (ou équivalent).
`save_upload` restera dans `core.uploads`.

### `forge_cli/public_list.py`

Génère des lignes comme :

```python
from core.uploads import get_cover_media
from core.uploads import list_media_for_entity
```

Devra émettre `from forge_mvc_media.uploads import ...` pour les fonctions opt-in.

---

## Usages dans les starters

Le starter `communes-sejours` contient une déclaration de champ média dans
`hebergement.json` :

```json
"media": [
  {"field": "image", "role": "cover"},
  {"field": "image", "role": "gallery"}
]
```

Ce starter génère du code CRUD avec les imports opt-in. Après extraction,
le starter devra soit dépendre de `forge-mvc-media`, soit être conditionnel.

---

## Usages dans les tests

Plus de 20 fichiers de test importent depuis `core.uploads`, incluant des
fonctions applicatives (OPTIN_MEDIA) :

| Catégorie | Fichiers représentatifs |
|---|---|
| Tests repository/gallery (OPTIN) | `test_media_repository.py`, `test_media_gallery.py`, `test_media_attach.py`, `test_media_delete.py` |
| Tests intégration (OPTIN) | `test_media_integration.py`, `test_media_route.py`, `test_media_entity.py` |
| Tests CRUD générateur (OPTIN) | `test_make_crud_media.py`, `test_make_crud_media_alt.py`, `test_make_crud_media_context.py`, `test_make_crud_media_destroy.py`, `test_make_crud_media_gallery_*.py`, `test_make_crud_media_runtime.py` |
| Tests upload generique (CORE) | `test_uploads.py`, `test_uploads_image.py` |
| Tests sécurité (CORE) | `test_security_upload_rate_limit.py`, `test_security_uploads_audit.py` |
| Tests E2E/form (mixtes) | `test_e2e_upload_http.py`, `test_forms_image_field.py`, `test_forms_from_request_files.py` |

Lors de l'extraction, les tests OPTIN devront être déplacés ou adaptés pour
importer depuis le module `forge-mvc-media`.

---

## Documentation concernée

| Fichier | Contenu relatif au média |
|---|---|
| `docs/media.md` | Documentation publique : `forge media:init`, `save_image`, CRUD media, route `/media/...`. Mélange API générique et applicative sans distinction. |
| `docs/reference/api.md` | Section `core.uploads` ligne ~1081 : `save_upload`, `delete_media_file`, `serve_media_file`, `attach_media_to_entity`, `create_media_record`, `get_media_record`. Ligne 2907 : métadonnée `media`. |
| `docs/index.html` / `mvc/views/landing/` | Mention "Médias" dans les briques core — à distinguer (upload générique vs module opt-in). |

---

## Risques d'extraction

### R1 — Régression des imports dans le code applicatif existant

Tout code applicatif qui importe `attach_media_to_entity`, `list_media_for_entity`,
etc. depuis `core.uploads` sera cassé si on retire ces symboles sans shim.

**Mitigation** : conserver dans `core/uploads/__init__.py` des re-exports
dépréciés le temps d'un cycle de migration (ticket 11.3 définit la stratégie).

### R2 — Tests qui échouent à l'import

Les 15+ fichiers de test OPTIN importent depuis `core.uploads`. Après extraction,
ces tests devront importer depuis `forge_mvc_media` — ou le package devra être
installé en mode développement.

**Mitigation** : le scaffold `forge-mvc-media` (ticket 11.2) doit être installable
via `pip install -e packages/forge-mvc-media/` pour que les tests CI continuent.

### R3 — Générateurs produisent du mauvais code

`controller_builder.py` et `public_list.py` génèrent des imports hardcodés vers
`core.uploads`. Après extraction, le code généré sera invalide si le générateur
n'est pas mis à jour.

**Mitigation** : ticket 11.4 met à jour les générateurs.

### R4 — `core/uploads/__init__.py` exporte 56 symboles mélangés

L'`__init__.py` actuel re-exporte indifféremment CORE et OPTIN. La refonte devra
réduire les re-exports core aux seuls symboles CORE_GÉNÉRIQUE.

**Mitigation** : ticket 11.3 nettoie `__init__.py` et documente les symboles retirés.

### R5 — Pillow reste une dépendance runtime du core

`core/uploads/image.py` utilise `PIL`. Ce fichier reste dans le core, donc Pillow
reste une dépendance runtime de `forge-mvc`. C'est intentionnel (cf. `pyproject.toml`
actuel) mais à documenter explicitement.

---

## Décisions proposées

| Décision | Justification |
|---|---|
| `media_repository.py` et `media_gallery.py` migrent vers `forge-mvc-media` | Couplage SQL / `core.database` — incompatible avec le core minimal |
| Les 6 autres fichiers de `core/uploads/` restent dans le core | Aucun import SQL, aucune dépendance à la table `media` |
| `media_url()` suit `media_gallery.py` dans `forge-mvc-media` | Fonctionnellement liée à la galerie, même si la logique est simple |
| Le schéma SQL (`media.sql`) et les classes d'entité restent applicatifs | Ils définissent la table `media`, qui est un choix d'implémentation |
| Pas de shim `core.uploads` → `forge_mvc_media` dans ce ticket | La stratégie de compatibilité est définie en 11.3 |
| Pillow reste une dépendance runtime du core | `image.py` reste dans le core, Pillow est déjà déclaré dans `pyproject.toml` |

---

## Tickets futurs suggérés

| Ticket | Description |
|---|---|
| `MEDIA-EXTRACT-PACKAGE-SCAFFOLD-001` (11.2) | Créer `packages/forge-mvc-media/` avec `pyproject.toml`, `__init__.py`, layout minimal |
| `MEDIA-REPOSITORY-MOVE-001` (11.3) | Déplacer `media_repository.py` + `media_gallery.py` vers `forge-mvc-media`, nettoyer `core/uploads/__init__.py` |
| `MEDIA-CRUD-INTEGRATION-001` (11.4) | Mettre à jour `controller_builder.py` et `public_list.py` pour émettre les imports depuis `forge-mvc-media` |
| `MEDIA-DOCS-UPDATE-001` (11.5) | Mettre à jour `docs/media.md` et `docs/reference/api.md` pour distinguer core générique et module opt-in |

---

## Conclusion

La frontière core/opt-in dans le sous-système média est **architecturalement
claire et peu ambiguë**. Les 6 fichiers génériques de `core/uploads/` (exceptions,
validators, storage, manager, image, rate_limit) n'ont aucune connaissance de la
table `media`. Les 2 fichiers applicatifs (`media_repository.py`, `media_gallery.py`)
dépendent de `core.database` et d'un schéma SQL spécifique.

L'extraction est faisable en 4 tickets séquentiels (11.2 → 11.3 → 11.4 → 11.5).
Le principal risque est la mise à jour des générateurs CLI (R3) et des tests (R2).
Aucune rupture d'API publique n'est introduite dans ce ticket d'audit.
