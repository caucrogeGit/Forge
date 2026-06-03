# ADR-018 — Extraction du traitement d'image hors du core : `forge-mvc-images`

## Statut

Proposé — Forge 1.0.0-beta.x (ticket `IMAGES-EXTRACT-RENAME-001`).

> Décision validée sur le principe (option « B — renommer + rapatrier »).
> Périmètre figé ci-dessous ; exécution par étapes.

---

## Date

2026-06-03

---

## Contexte

Forge distribue un opt-in `forge-mvc-media` dont la responsabilité réelle, à ce
jour, est **la gestion applicative des médias** : un repository SQL
(`attach_media_to_entity`, `create_media_record`, rôles, positions, `alt_text`)
et des helpers de galerie/couverture (`get_media_gallery`, `get_cover_media`,
`media_url`). Le **traitement d'image** proprement dit (génération de variantes
et de miniatures, `save_image`, vérification de contenu, garde anti-bombe de
décompression, constantes `ALLOWED_IMAGE_*`/`IMAGE_VARIANT_SIZES`) vit lui dans
le **core**, à `core/uploads/image.py`, et **Pillow** est une dépendance runtime
du core.

Depuis l'arrivée de `forge-mvc-video` (qui possède toute la chaîne vidéo :
ingest, stockage, transcodage, lecture), le nom « media » est devenu **trompeur**
— un développeur attend de `forge-mvc-media` qu'il gère aussi la vidéo, ce qui
n'est pas le cas. Par ailleurs, embarquer Pillow et le traitement d'image dans
le core contredit le principe de **noyau minimal** (charte principe 8, ADR-004) :
le core devrait fournir l'upload brut sûr, pas le pipeline d'images.

### Couplage existant à dénouer

- `core/uploads/manager.py` : `save_upload(category="images", variants=True)`
  appelle `verify_image_content`, `generate_image_variants`,
  `image_variant_relative_paths` — le chemin d'upload **générique** du core
  porte donc un comportement **spécifique aux images**.
- `core/uploads/__init__.py` réexporte l'API image.
- `forge_mvc_media/media_gallery.py` dépend de `core.uploads.image`
  (`ALLOWED_IMAGE_EXTENSIONS`, `image_variant_relative_paths`).
- `make:crud` **génère** `from forge_mvc_media import ...`
  (`forge_cli/entities/crud/controller_builder.py`), idem `forge_cli/public_list.py`
  et le catalogue opt-in `forge_cli/optins/catalog.py` (entrée « media »).
- CI (`.github/workflows/tests.yml`), README, `docs/reference/api.md`,
  `docs/install/core-dev.md`, CONTRIBUTING.
- Garde-fous qui **imposent** Pillow dans le core : `tests/meta/test_packaging.py`
  (`test_pillow_dans_pyproject`, `test_pillow_dans_requirements_txt`),
  `tests/release/test_release_compat.py`, `tests/meta/test_app_default_no_mfa_001.py`.

---

## Décision

Créer un opt-in **`forge-mvc-images`** (`forge_mvc_images`) qui **remplace**
`forge-mvc-media` et devient **l'unique propriétaire de tout l'image** :

1. **Traitement d'image** (déplacé du core) : `save_image`, génération de
   variantes/miniatures, `verify_image_content`, garde anti-bombe, constantes
   `ALLOWED_IMAGE_*` / `IMAGE_VARIANT_SIZES`, `MediaRecord`. **Pillow** devient
   dépendance de `forge-mvc-images`, **retirée du core**.
2. **Couche applicative** (déplacée de `forge-mvc-media`) : repository SQL,
   galerie, couverture, `alt_text`.

Le **core** ne garde que l'**upload brut générique** : `save_upload` (sans
le cas particulier `images`), `save_bytes`, validation générique, storage,
rate-limit, exceptions. `save_upload` devient purement générique ;
`forge-mvc-images` fournit le chemin d'upload **image-aware** (validation de
contenu + écriture + variantes).

Conformément à la **convention pré-1.0** (pas d'utilisateurs externes), le
renommage se fait **sans alias déprécié ni guide de migration** : `forge-mvc-media`
est supprimé, les réexports image du core sont retirés.

### Hors périmètre

- La vidéo (`forge-mvc-video`) reste inchangée.
- Aucune nouvelle fonctionnalité image n'est ajoutée dans les tickets
  d'**extraction** (1 à 7) : ils déplacent le comportement existant tel quel.
  L'**extension** (ci-dessous) fait l'objet de tickets `IMAGES-FEATURE-*`
  ultérieurs, sur la base propre obtenue après extraction.

---

## Fonctionnalités cibles (ambition « étendre »)

### Existant déplacé tel quel (figé, non configurable)

- **Deux variantes en dur** : `medium` (1280×1280 max), `thumbnail` (300×300
  max), + `original` conservé. `IMAGE_VARIANT_SIZES` non extensible sans éditer
  le code.
- **Redimensionnement** : ratio préservé, réduction seule (jamais d'agrandissement),
  rééchantillonnage LANCZOS.
- **Formats** : `jpg, jpeg, png, webp` ; la variante garde le format de l'original.
- **Rangement** : `<dossier>/medium/…`, `<dossier>/thumbnail/…`.
- **Sécurité** : `verify_image_content`, garde anti-bombe de décompression.
- **Galerie** : `url`, `medium_url`, `thumbnail_url` par média.

### Cibles d'extension (tickets `IMAGES-FEATURE-*`)

| Capacité | Aujourd'hui | Cible |
|---|---|---|
| **Profils de variantes** | 2 tailles en dur | profils **configurables** (noms + dimensions arbitraires) via la config `forge_mvc_images` |
| **Conversion de format** | format = celui de l'original | générer une variante dans un format choisi (ex. **WebP**) tout en conservant l'original |
| **Recadrage** | réduction « fit » seule | mode **crop** (ratio fixe : carré avatar, bannière) avec point focal optionnel |
| **Qualité / compression** | défaut Pillow | **qualité réglable** par variante (poids vs. netteté) |
| **Dimensions sémantiques** | medium / thumbnail | profils nommés **cover / og-image** prêts pour les métadonnées sociales |
| **Idempotence / régénération** | génération à l'upload | commande/CLI pour **régénérer** les variantes après changement de profil |

Ces capacités restent **opt-in et explicites** (pas de magie cachée, charte
principe 3) : un profil non déclaré n'est pas produit ; aucune conversion n'a
lieu sans demande. Chaque capacité = un ticket `IMAGES-FEATURE-*` séparé
(charte principe 2 : une responsabilité par ticket).

---

## Conséquences

### Positives

- Nom **honnête** et responsabilité nette : `forge-mvc-images` = tout l'image,
  `forge-mvc-video` = toute la vidéo, `core/uploads` = upload brut sûr.
- **Core minimal** : Pillow quitte le runtime du core (principe 8, ADR-004).
- Une seule façon officielle de traiter une image (principe 11).

### Coûts / ruptures

- Renommage d'un paquet **publié** (PyPI `forge-mvc-media` 1.0.0b13) → nouveau
  paquet `forge-mvc-images`. Acceptable en bêta pré-1.0.
- Les garde-fous « Pillow dans le core » s'**inversent** (Pillow absent du core,
  présent dans `forge-mvc-images`).
- `make:crud` génère désormais `from forge_mvc_images import ...` ; tests de
  snapshot de génération à mettre à jour.
- **Deux fichiers protégés par le hook** doivent être modifiés par le mainteneur,
  pas par un agent : `pyproject.toml` racine (retrait de Pillow) et `CLAUDE.md`
  (§1, §3, §9 décrivant `forge-mvc-media`).

---

## Plan d'exécution (tickets)

1. `IMAGES-PKG-SCAFFOLD-001` — squelette `packages/forge-mvc-images`
   (`pyproject.toml` avec Pillow, `forge_mvc_images/__init__.py`).
2. `IMAGES-MOVE-PROCESSING-001` — déplacer le traitement image du core vers
   `forge_mvc_images` ; rendre `core/uploads/save_upload` générique ; exposer un
   chemin image-aware dans le module.
3. `IMAGES-MOVE-APPLICATIVE-001` — déplacer repository + galerie depuis
   `forge-mvc-media` vers `forge_mvc_images`.
4. `CORE-DROP-PILLOW-001` — retrait de Pillow du core (**pyproject racine :
   mainteneur**), `requirements.txt`, inversion des garde-fous packaging.
5. `CLI-CRUD-IMAGES-RENAME-001` — `controller_builder`, `public_list`,
   `optins/catalog` → `forge_mvc_images` ; mise à jour des tests de génération.
6. `CI-DOCS-IMAGES-RENAME-001` — matrice CI, README, `docs/reference/api.md`,
   `docs/install/core-dev.md`, CONTRIBUTING ; **CLAUDE.md : mainteneur**.
7. `REMOVE-MEDIA-PKG-001` — suppression de `packages/forge-mvc-media` ; entrée
   CHANGELOG.
8. `IMAGES-FEATURE-*` (ultérieur) — extension des fonctionnalités image.

---

## Alternatives écartées

- **A — renommer seulement** : `media → images` sans bouger le traitement. Rejeté :
  le nom « images » resterait un abus de langage tant que le traitement vit dans
  le core, et le couplage `save_upload`/Pillow/core subsisterait.
- **C — statu quo** : garder `forge-mvc-media` comme couche générique
  d'attachement multi-type. Rejeté : ambiguïté persistante vis-à-vis de
  `forge-mvc-video`, et Pillow reste dans le core.

---

## Références

- Charte principes 8 (noyau minimal), 11 (une seule façon officielle).
- ADR-004 (périmètre du core minimal strict).
- ADR-005 (packaging hybride monorepo + multi-distributions PyPI).
