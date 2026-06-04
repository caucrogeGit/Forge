# ADR-019 — Extraction de l'upload générique hors du core : `forge-mvc-files`

## Statut

Proposé — Forge 1.0.0-beta.x.

> Décision validée sur le principe (« sortir complètement l'upload du core »).
> Périmètre figé ci-dessous ; exécution par étapes (chantier multi-tickets).

---

## Date

2026-06-04

---

## Contexte

Le core de Forge embarque aujourd'hui tout le pipeline d'**upload générique** dans
`core/uploads/` :

- `manager.py` — `save_upload`, `SavedUpload`, `serve_media_file`,
  `delete_upload`, `delete_media_file`, `get_upload_path`, `upload_root`,
  `_read_upload` ;
- `storage.py` — écriture disque uuid/horodatée, anti-traversal
  (`normalize_media_path`, `media_path_to_storage_path`, `is_safe_media_path`,
  `save_bytes`, `delete_file`) ;
- `validators.py` — `validate_upload_metadata`, `validate_extension`,
  `validate_mime_type`, `validate_size` ;
- `exceptions.py` — hiérarchie `UploadError` ;
- `rate_limit.py` — `is_upload_rate_limited`, `record_upload_attempt`.

Après l'extraction du traitement d'image (ADR-018), l'upload **générique** reste
le dernier gros bloc applicatif logé dans le noyau. Un framework web peut
parfaitement exister sans upload de fichiers : c'est une **brique applicative**,
pas un fondement. Le garder dans le core contredit le principe de **noyau
minimal** (charte principe 8, ADR-004) et laisse deux façons d'aborder les
fichiers (core + opt-ins médias), en tension avec le principe 11 (« une seule
façon officielle »).

### Couplage existant à dénouer

- **`core/forms/fields.py` (dans le core)** importe `core.uploads.exceptions`
  (`UploadError`) et `core.uploads.validators` (`validate_extension`,
  `validate_mime_type`, `validate_size`) pour valider `FileField`/`ImageField`.
  ⚠️ Le core **ne peut pas dépendre d'un opt-in** (ADR-004) — voir la décision.
- **`forge-mvc-images`** dépend de `core.uploads` (`save_upload`, `_read_upload`,
  `validate_upload_metadata`, `SavedUpload`, `storage`) → dépendra de
  `forge-mvc-files` (**inversion de dépendance**).
- **Générateurs** `make:crud` / pages publiques :
  `forge_cli/entities/crud/controller_builder.py` émet
  `from core.uploads import save_upload` (fichiers documents).
- `forge_cli/uploads.py` (`init_upload_storage`) et `forge_cli/help_dispatch.py`.
- Starter `forge_cli/starters/data/file-upload/…` (contrôleur d'exemple).
- **~34 fichiers de tests** importent `core.uploads`.
- Docs : `docs/reference/api.md`, `reference.md`, `reference-schema.md`,
  `features/media.md`, `deployment/production-limits.md`,
  `deployment/production-security.md`, `philosophy/security.md`,
  `starters/welcome-forge/avance/file-upload.md`, `ADR-004`, `CLAUDE.md` (§3).
- `forge-mvc-audio` (livré) possède son **propre** stockage — **non impacté**.
- `rate_limit` d'upload est **upload-spécifique** (l'auth/MFA a son propre
  rate-limit dans `core.security.hashing`) → part sans accroc.

---

## Décision

Créer un opt-in **`forge-mvc-files`** (`forge_mvc_files`) qui devient l'**unique
propriétaire de l'upload générique**. Le **pipeline d'I/O** quitte le core :

1. **Déplacé vers `forge-mvc-files`** : `manager` (`save_upload`, `SavedUpload`,
   `serve_media_file`, `delete_upload`, `delete_media_file`, `get_upload_path`,
   `upload_root`, `_read_upload`), `storage` (écriture/anti-traversal),
   `rate_limit` d'upload.
2. **Reste dans le core** (relocalisé hors de `core/uploads/`, vers
   `core/forms/` ou un util de validation générique) : les **validators
   purs** (`validate_extension`, `validate_mime_type`, `validate_size`) et la
   **hiérarchie d'exceptions** `UploadError`, **uniquement** parce que
   `core/forms/fields.py` (`FileField`) en dépend et que le core ne peut pas
   dépendre d'un opt-in (ADR-004). Ce sont des contrôles **purs** (chaîne/entier),
   sans I/O — ils ne contredisent pas le noyau minimal. `forge-mvc-files`
   **réutilise** ces validators du core.

Le **core** ne fait donc plus **aucune écriture/lecture de fichier uploadé** :
`save_upload`, `serve_media_file`, le storage et le rate-limit d'upload
disparaissent du noyau. `FileField` continue de **valider** (métadonnées) mais
l'**écriture** d'un fichier devient l'affaire de `forge-mvc-files`.

Conformément à la **convention pré-1.0**, l'extraction se fait **sans alias
déprécié** : les imports `core.uploads` du pipeline sont supprimés ; importer
depuis `forge_mvc_files`.

### Hors périmètre

- Aucune nouvelle fonctionnalité d'upload : on déplace le comportement existant.
- `forge-mvc-images`, `forge-mvc-audio`, `forge-mvc-video` ne changent pas de
  comportement (seule la dépendance d'images vers `core.uploads` est repointée).
- Les validators génériques + exceptions **restent dans le core** (voir décision).

---

## Conséquences

### Positives

- **Noyau minimal réel** (principe 8, ADR-004) : le core n'écrit plus de fichier
  uploadé.
- **Une seule façon officielle** (principe 11) : `forge-mvc-files` détient
  l'upload générique ; les modules médias (images/audio/vidéo) se branchent
  au-dessus ou à côté, sans doublon avec le core.
- Cohérence avec ADR-018 (extraction image) : même trajectoire d'extraction.

### Coûts / ruptures

- **Toute application qui uploade un fichier devra installer `forge-mvc-files`**
  (changement de contrat — assumé, philosophie opt-in explicite).
- **Inversion de dépendance** : `forge-mvc-images` dépendra de `forge-mvc-files`.
- `make:crud` génère désormais `from forge_mvc_files import save_upload` pour les
  champs fichier ; tests de génération à mettre à jour.
- ~34 fichiers de tests + ~10 docs à repointer ; `CLAUDE.md` (§3) et `ADR-004`
  (périmètre) à amender (mainteneur — fichiers protégés par le hook).
- Garde-fous packaging/perimètre à inverser (le core ne contient plus d'upload).

---

## Plan d'exécution (tickets)

1. `FILES-PKG-SCAFFOLD-001` — squelette `packages/forge-mvc-files`
   (`pyproject` + `forge_mvc_files/__init__`), enregistrement opt-in (catalogue,
   classifier, CI, release-policy, contrats de tests).
2. `FILES-VALIDATORS-KEEP-001` — relocaliser les validators purs + exceptions
   `UploadError` hors de `core/uploads/` (vers `core/forms/` ou `core/validation`),
   repointer `core/forms/fields.py`. Le core garde la validation, pas l'I/O.
3. `FILES-MOVE-PIPELINE-001` — déplacer `manager` + `storage` + `rate_limit`
   d'upload vers `forge_mvc_files` ; le core ne réexporte plus l'upload.
4. `FILES-IMAGES-REPOINT-001` — `forge-mvc-images` dépend de `forge-mvc-files`
   (imports `core.uploads` → `forge_mvc_files`).
5. `FILES-CLI-RENAME-001` — générateurs `make:crud`/pages publiques +
   `forge_cli/uploads.py` + starter `file-upload` → `forge_mvc_files`.
6. `FILES-DOCS-PERIMETER-001` — docs (`api.md`, `production-*`, `security.md`,
   `file-upload.md`…), **ADR-004 et CLAUDE.md §3** (mainteneur).
7. `CORE-DROP-UPLOADS-001` — suppression de `core/uploads/`, inversion des
   garde-fous périmètre + test d'absence.

L'ordre garantit que la suppression de `core/uploads/` (étape 7) vient **après**
le repointage de tous les importeurs, pour ne jamais casser la collecte.

---

## Alternatives écartées

- **Upload extrait mais `serve_media_file` gardé dans le core** : compromis
  rejeté — laisse deux endroits pour les fichiers (principe 11 moins net) et
  garde de l'I/O fichier dans le noyau.
- **Couche `forge-mvc-files` par-dessus `core.uploads`** : rejeté — laisserait
  **deux façons** d'uploader (core + opt-in), exactement ce que le principe 11
  proscrit.
- **Statu quo** : rejeté — l'upload reste un bloc applicatif dans le noyau.

---

## Références

- Charte principes 8 (noyau minimal), 11 (une seule façon officielle).
- ADR-004 (périmètre du core minimal strict) — **à amender**.
- ADR-005 (packaging hybride monorepo + multi-distributions PyPI).
- ADR-018 (extraction du traitement d'image — même trajectoire).
