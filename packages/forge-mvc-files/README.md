# forge-mvc-files

Module **opt-in** propriétaire de l'**upload générique** dans Forge MVC :
écriture disque sécurisée, storage anti-traversal, service de fichiers
(streaming HTTP Range), suppression et rate-limit d'upload.

## Statut : squelette — `FILES-PKG-SCAFFOLD-001`

À ce stade, `forge-mvc-files` est un **squelette source-only** : le
`pyproject.toml` déclare la dépendance `forge-mvc` et
`forge_mvc_files/__init__.py` expose `__version__`, mais **aucune logique n'a
encore été déplacée**. Le pipeline d'upload vit toujours dans `core/uploads/` ;
il sera rapatrié par les tickets suivants (voir ADR-019).

Ce paquet **n'est pas encore publié sur PyPI**.

## Pourquoi ce module (ADR-019)

Après l'extraction du traitement d'image (ADR-018), l'upload **générique** reste
le dernier gros bloc applicatif logé dans le noyau. Un framework web peut
exister sans upload de fichiers : c'est une brique applicative, pas un
fondement. `forge-mvc-files` devient l'**unique** propriétaire de l'upload
générique (principes 8 « noyau minimal » et 11 « une seule façon officielle »).

### Ce qui sera déplacé du core

- `manager` — `save_upload`, `SavedUpload`, `serve_media_file`, `delete_upload`,
  `delete_media_file`, `get_upload_path`, `upload_root`, `_read_upload` ;
- `storage` — écriture/anti-traversal (`normalize_media_path`,
  `media_path_to_storage_path`, `is_safe_media_path`, `save_bytes`, `delete_file`) ;
- `rate_limit` d'upload (`is_upload_rate_limited`, `record_upload_attempt`).

### Ce qui reste dans le core (définitif)

- Les **validators purs** (`validate_extension`, `validate_mime_type`,
  `validate_size`) et la hiérarchie d'exceptions `UploadError` : `core/forms`
  (`FileField`) en dépend, et le core ne peut pas dépendre d'un opt-in (ADR-004).
  Ce sont des contrôles purs sans I/O. `forge-mvc-files` les réutilise.

## Plan d'exécution (ADR-019)

| Ticket | Description | État |
|---|---|---|
| `FILES-PKG-SCAFFOLD-001` | Squelette du paquet + enregistrement opt-in | livré |
| `FILES-VALIDATORS-KEEP-001` | Relocaliser validators + exceptions dans le core | à venir |
| `FILES-MOVE-PIPELINE-001` | Déplacer manager + storage + rate_limit | à venir |
| `FILES-IMAGES-REPOINT-001` | forge-mvc-images dépend de forge-mvc-files | à venir |
| `FILES-CLI-RENAME-001` | Générateurs + forge_cli/uploads + starter | à venir |
| `FILES-DOCS-PERIMETER-001` | Docs + ADR-004 + CLAUDE.md §3 | à venir |
| `CORE-DROP-UPLOADS-001` | Suppression de `core/uploads/` | à venir |

## Installation (mode éditable, depuis les sources)

```bash
git clone https://github.com/caucrogeGit/Forge.git
cd Forge
pip install -e packages/forge-mvc-files/
```

## Référence

- `docs/adr/019-upload-extraction.md` — décision et périmètre figés.
- Charte principes 8 (noyau minimal), 11 (une seule façon officielle).
