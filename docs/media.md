# Module média Forge

[Accueil](index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

!!! info "Statut : Alpha — préparé pour publication future"
    `forge-mvc-media` n'est **pas publié sur PyPI dans la vague `{{forge_version}}`**.
    Le module est en statut `3 - Alpha` depuis `MEDIA-PYPI-READY-002`.
    L'installation via `pip install forge-mvc-media` reste impossible pour l'instant.

    Publication PyPI prévue dans une prochaine release (ticket dédié requis).

Forge sépare les primitives génériques d'upload (`core/uploads/`) des helpers applicatifs médias (`forge_mvc_media`). Le core est installé avec Forge ; les helpers applicatifs sont fournis par le module opt-in `forge-mvc-media` (non publié sur PyPI en `{{forge_version}}`, publication prévue dans une prochaine release).

## Frontière core / opt-in média

**`core.uploads` — primitives génériques** (toujours disponibles) :

- `save_upload` — sauvegarde sécurisée d'un fichier
- `save_image`, `generate_image_variants` — traitement Pillow
- `serve_media_file` — route `/media/...` sécurisée
- `delete_media_file` — suppression physique d'un fichier
- exceptions (`UploadError`, `UploadStorageError`…)
- validation MIME, stockage contrôlé, protection path traversal
- rate limiting upload

**`forge_mvc_media` — helpers applicatifs** (opt-in `forge-mvc-media`) :

- `attach_media_to_entity`, `create_media_record`, `get_media_record`
- `list_media_for_entity`, `update_media_alt_text`, `update_media_position`
- `delete_media`, `delete_media_record`
- `get_media_gallery`, `get_cover_media`, `media_url`

Les anciens imports `from core.uploads import attach_media_to_entity` ne sont plus supportés depuis `MEDIA-SHIMS-REMOVE-001`. Les fichiers `core/uploads/media_repository.py` et `core/uploads/media_gallery.py` ont été supprimés. Utiliser `from forge_mvc_media import ...`.

## Installation depuis les sources

`forge-mvc-media` n'étant pas sur PyPI, l'installation se fait depuis le dépôt Forge :

```bash
git clone https://github.com/caucrogeGit/Forge.git
cd Forge
pip install -e packages/forge-mvc-media/
```

L'option `-e` permet des modifications locales sans réinstallation.

La dépendance `forge-mvc=={{forge_version}}` doit être satisfaite. Si vous travaillez depuis
le dépôt Forge directement (sans venv isolé), le core est déjà disponible via `PYTHONPATH`.

---

**Ce que Média v2 sait faire** : déclaration dans `entity.json`, génération CRUD complète (formulaires multipart, upload à la création, remplacement et suppression explicite à l'édition, suppression des médias liés à la suppression de l'entité, preview dans `show` et `edit`), galerie `multiple=true` (affichage, ajout, multi-upload, suppression individuelle, réorganisation par position, alt_text), stockage dans la table `media`, route `/media/...`.

**Ce que Média v2 ne fait pas encore** : back-office média, permissions média avancées, détection MIME fiable côté serveur, aperçu JavaScript avant upload, alt_text individuel par fichier lors d'un multi-upload simultané.

---

## Initialiser le stockage

```bash
forge media:init
```

Crée les dossiers nécessaires dans `storage/uploads/` :

```
storage/uploads/
  images/
    thumbnail/    ← réservé aux miniatures (non disponible)
    medium/       ← réservé aux versions redimensionnées (non disponible)
  documents/
  tmp/
```

La commande est idempotente : elle peut être relancée sans risque.

!!! note "Forge installé avec pipx"
    `forge media:init` utilise la version du paquet installée dans l'environnement pipx.
    Après une modification locale du framework, reconstruire et réinstaller la roue avant de lancer la commande :

    ```bash
    python -m build
    pipx install dist/forge_mvc-1.3.0-py3-none-any.whl --force
    hash -r
    ```

---

## Uploader une image

```python
from core.uploads.image import save_image

media = save_image(
    request.files["photo"],
    entity_name="Article",
    entity_id=42,
    usage="cover",
    is_main=True,
)
```

`save_image` retourne un `MediaRecord` :

| Attribut | Type | Description |
|---|---|---|
| `filename` | `str` | Nom sécurisé avec UUID (ex: `photo-a1b2c3.jpg`) |
| `original_name` | `str` | Nom d'origine soumis par l'utilisateur |
| `path` | `str` | Chemin relatif dans `storage/uploads/` |
| `category` | `str` | Sous-dossier de stockage (défaut : `images`) |
| `size` | `int` | Taille en octets |
| `mime_type` | `str \| None` | Type MIME déclaré par le navigateur |
| `entity_name` | `str \| None` | Nom de l'entité liée (ex: `"Article"`) |
| `entity_id` | `int \| None` | Identifiant de l'entité |
| `usage` | `str` | Rôle de l'image (`"main"`, `"cover"`, `"gallery"`…) |
| `position` | `int` | Ordre d'affichage |
| `is_main` | `bool` | Image principale de l'entité |

---

## Extensions et MIME acceptés

`save_image` et `ImageField` valident contre ces ensembles par défaut :

- **Extensions** : `jpg`, `jpeg`, `png`, `webp`
- **MIME** : `image/jpeg`, `image/png`, `image/webp`

**GIF refusé par défaut** : le format GIF n'est pas supporté. `ImageField` rejette les fichiers `.gif` / `image/gif` à la validation. Cette limite est intentionnelle — le pipeline de variantes n'est pas conçu pour les GIF animés.

La taille maximale est lue depuis `UPLOAD_MAX_SIZE` (défaut : 5 Mo).

**Dépendance** : Pillow (`>=10.0,<13`) est requis pour la génération des variantes d'images. Il est déclaré dans `requirements.txt` et `pyproject.toml`.

---

## Variantes d'images

Le service prévoit trois variantes par image :

| Variante | Chemin | Disponibilité |
|---|---|---|
| `original` | `images/<fichier>` | Généré |
| `thumbnail` | `images/thumbnail/<fichier>` | Généré |
| `medium` | `images/medium/<fichier>` | Généré |

Générer les variantes :

```python
from core.uploads.image import generate_image_variants

variants = generate_image_variants(media.path)
# variants["original"]  → "images/photo.png"
# variants["thumbnail"] → "images/thumbnail/photo.png"
# variants["medium"]    → "images/medium/photo.png"
```

Les variantes conservent les proportions :

- `thumbnail` : maximum `300 x 300`
- `medium` : maximum `1280 x 1280`

`save_upload` peut aussi déclencher ces variantes explicitement pour la
catégorie `images` :

```python
from core.uploads import save_upload

saved = save_upload(request.files["photo"], category="images", variants=True)

saved.path
# "images/photo.png"

saved.variants
# {
#     "medium": "images/medium/photo.png",
#     "thumbnail": "images/thumbnail/photo.png",
# }
```

Par défaut, `save_upload(file, category="images")` ne génère pas de variantes.
`saved.path` reste toujours le chemin relatif de l'original. `variants=True`
est refusé pour les catégories non-images.

---

## Supprimer un média

Pour supprimer un fichier média stocké sous `storage/uploads/`, utiliser
`delete_media_file` avec un chemin relatif :

```python
from core.uploads import delete_media_file

delete_media_file("images/photo.png")
# {"images/photo.png": True}
```

Par défaut, seule la cible est supprimée. Pour supprimer aussi `medium` et
`thumbnail`, activer explicitement `variants=True` :

```python
delete_media_file("images/photo.png", variants=True)
# {
#     "images/photo.png": True,
#     "images/medium/photo.png": True,
#     "images/thumbnail/photo.png": True,
# }
```

Si une variante manque, la suppression continue et retourne `False` pour ce
chemin. Les chemins absolus, URL et traversals (`..`) sont refusés. Cette API
ne supprime pas encore l'enregistrement SQL de l'entité `Media`.

---

## Servir un média

Forge expose une route média minimale :

```text
/media/<chemin-relatif>
```

Le fichier reste stocké sous `storage/uploads/`. Par exemple :

```text
Media.path = "images/photo.png"
URL publique locale = "/media/images/photo.png"

Variante medium = "images/medium/photo.png"
URL publique locale = "/media/images/medium/photo.png"
```

La route sert uniquement des chemins relatifs sûrs. Les chemins absolus, URL,
traversals (`..`), dossiers et symlinks sortant de `storage/uploads/` sont
refusés. Un fichier absent retourne `404`.

Cette route ne fournit pas encore de galerie, contrôleur CRUD média,
permissions média ou règles métier.

---

## Métadonnées SQL

L'entité `Media` fournit une table générique `media` pour relier un fichier
stocké à une entité applicative. Elle ne contient pas de logique métier :
`entity_name` indique le type d'entité liée, `entity_id` son identifiant.

```python
from forge_mvc_media import create_media_record, list_media_for_entity

media_id = create_media_record(
    entity_name="hebergement",
    entity_id=12,
    path="images/photo.png",
    original_name="photo.png",
    mime_type="image/png",
    role="gallery",
    position=1,
)

medias = list_media_for_entity("hebergement", 12)
```

`Media.path` reste un chemin relatif normalisé sous `storage/uploads/`. Le
champ `role` permet de distinguer des usages génériques comme `default`,
`cover` ou `gallery`. Le champ `position` permet un tri stable par
`position ASC`, puis `id ASC`.

La suppression des métadonnées SQL est volontairement séparée de la suppression
des fichiers :

```python
from forge_mvc_media import delete_media, delete_media_record
from core.uploads import delete_media_file

delete_media_record(media_id)          # supprime seulement la ligne SQL
delete_media_file("images/photo.png")  # supprime seulement le fichier
```

Pour supprimer les deux explicitement :

```python
result = delete_media(
    media_id,
    delete_files=True,
    variants=True,
)
```

Par défaut, `delete_media(media_id)` ne supprime pas les fichiers physiques
(`delete_files=False`) afin d'éviter une suppression accidentelle. Avec
`delete_files=True`, l'original est supprimé, et les variantes `medium` /
`thumbnail` le sont aussi si `variants=True`.

Pour relier un fichier déjà uploadé à une entité, utiliser
`attach_media_to_entity` :

```python
from core.uploads import save_upload
from forge_mvc_media import attach_media_to_entity

saved = save_upload(file, category="images", variants=True)

media_id = attach_media_to_entity(
    saved,
    entity_name="hebergement",
    entity_id=12,
    role="gallery",
    position=1,
    alt_text="Vue extérieure",
)
```

`save_upload()` stocke le fichier et ses variantes éventuelles.
`attach_media_to_entity()` crée seulement la ligne `Media` correspondante. Elle
ne crée pas de fichier, ne supprime rien et ne modifie pas les variantes.

---

## Texte alternatif

Chaque média peut porter un `alt_text` optionnel (`VARCHAR(255) NULL`). Il sert à l'accessibilité, au référencement et à l'affichage public.

Dans le CRUD généré par `make:crud`, Forge expose automatiquement ce champ :

- **Création** : un champ texte `_media_alt_{name}` (média unique) ou `_media_alt_{name}_new` (galerie) permet de renseigner l'alt_text lors de l'ajout d'un fichier.
- **Modification — média unique** : si un nouveau fichier est fourni, l'alt_text saisi accompagne l'attachement ; sinon, il est mis à jour sur le média existant via `update_media_alt_text`.
- **Modification — galerie** : chaque item existant dispose d'un champ `_media_alt_{name}_{id}` ; les valeurs sont mises à jour individuellement. Un nouveau fichier uploadé reçoit l'alt_text du champ `_media_alt_{name}_new`.
- Une chaîne vide est traitée comme absence de texte alternatif (`None`).

Pour les usages manuels, passer `alt_text` explicitement à `attach_media_to_entity` ou appeler `update_media_alt_text` directement.

```python
media_id = create_media_record(
    entity_name="hebergement",
    entity_id=12,
    path="images/facade.png",
    alt_text="Façade principale de l'hébergement",
)
```

`attach_media_to_entity` accepte le même paramètre :

```python
attach_media_to_entity(
    saved,
    entity_name="hebergement",
    entity_id=12,
    role="cover",
    alt_text="Vue extérieure",
)
```

`alt_text` est inclus dans tous les dictionnaires retournés par `get_media_record`, `list_media_for_entity`, `get_media_gallery` et `get_cover_media`. Sa valeur est `None` quand il n'a pas été renseigné.

---

## Galerie ordonnée

Une galerie est une liste de médias liés à une entité avec `role="gallery"`.
Forge ne génère pas de galerie HTML dans cette étape : l'API retourne des
dictionnaires simples, prêts à être utilisés par l'application.

```python
from forge_mvc_media import get_media_gallery

gallery = get_media_gallery("hebergement", 12)
```

Les éléments sont triés par `position ASC`, puis `id ASC`. `path` reste le
chemin relatif stocké, tandis que `url` est l'URL locale `/media/...`.

Les galeries `multiple=true` acceptent l'ajout de plusieurs fichiers en une seule soumission via un champ file HTML `multiple`. Le comportement reste append-only : Forge ajoute les nouveaux médias à la galerie sans supprimer, remplacer ni réordonner automatiquement les médias existants. Le drag-and-drop et les aperçus JavaScript restent hors périmètre.

Exemple :

```python
[
    {
        "path": "images/photo.png",
        "url": "/media/images/photo.png",
        "medium_url": "/media/images/medium/photo.png",
        "thumbnail_url": "/media/images/thumbnail/photo.png",
        "alt_text": "Vue extérieure",
        "position": 1,
    }
]
```

Pour les images, Forge expose aussi `medium_path`, `medium_url`,
`thumbnail_path` et `thumbnail_url`. Pour les documents non-image, ces valeurs
restent à `None`.

---

## Image de couverture

L'image principale d'une entité utilise la convention générique `role="cover"`.
Elle sert de couverture pour une carte, une fiche ou une future page publique,
sans imposer de logique métier.

```python
from forge_mvc_media import get_cover_media

cover = get_cover_media("hebergement", 12)

cover["url"]
# "/media/images/cover.png"

cover["medium_url"]
# "/media/images/medium/cover.png"

cover["thumbnail_url"]
# "/media/images/thumbnail/cover.png"
```

S'il n'existe aucun média `cover`, la fonction retourne `None`. Le tri suit la
même règle que les galeries : `position ASC`, puis `id ASC`.

Un fallback explicite peut utiliser la première image de galerie :

```python
cover = get_cover_media(
    "hebergement",
    12,
    fallback_to_gallery=True,
)
```

Le fallback est désactivé par défaut. Il ignore les documents non-image et ne
crée ni ne modifie aucun enregistrement. Comme pour la galerie, aucun HTML,
contrôleur média ou upload CRUD n'est généré dans cette étape.

---

## Upload générique (documents, etc.)

Pour les fichiers non-images, utiliser `save_upload` :

```python
from core.uploads import save_upload

saved = save_upload(request.files["document"], category="documents")
```

La configuration (extensions, MIME, taille) est lue depuis `env/dev`.
Les chemins retournés sont relatifs à `storage/uploads/`.

---

## Déclarer des médias dans une entité

La clé optionnelle `"media"` dans un fichier `entity.json` déclare les médias liés à l'entité. Elle n'ajoute aucune colonne SQL et ne modifie pas `_base.py`. `make:crud` utilise cette déclaration pour générer automatiquement les champs de formulaire et l'upload à la création et à l'édition.

Les médias sont stockés dans la table `media` séparée, liés à l'entité via `media.entity_name` et `media.entity_id`. La table métier ne contient aucun champ média.

```json
{
  "format_version": 1,
  "entity": "Hebergement",
  "table": "hebergement",
  "fields": [
    { "name": "id", "sql_type": "INT", "primary_key": true, "auto_increment": true },
    { "name": "nom", "sql_type": "VARCHAR(120)" }
  ],
  "media": [
    {
      "name": "cover",
      "field": "image",
      "role": "cover",
      "variants": true,
      "multiple": false,
      "required": false,
      "label": "Image principale"
    },
    {
      "name": "brochure",
      "field": "file",
      "role": "brochure",
      "variants": false,
      "label": "Brochure PDF"
    }
  ]
}
```

### Propriétés d'une entrée `media`

| Clé | Obligatoire | Type | Défaut | Description |
|---|---|---|---|---|
| `name` | oui | `str` | — | Identifiant unique dans l'entité |
| `field` | oui | `"image"` ou `"file"` | — | Type de média |
| `role` | oui | `str` | — | Rôle sémantique (ex. `"cover"`, `"brochure"`) |
| `variants` | non | `bool` | `false` | Génère des variantes image (`thumbnail`, `medium`) |
| `multiple` | non | `bool` | `false` | `false` : média unique, remplacement à l'édition. `true` : galerie append-only, multi-upload, suppression individuelle, réorganisation par position |
| `required` | non | `bool` | `false` | Média obligatoire pour la saisie |
| `label` | non | `str` | — | Libellé affiché dans les formulaires générés |

### Règles de validation

- `name` et `role` doivent être uniques dans la liste `media` d'une même entité.
- `variants=true` n'est autorisé qu'avec `field="image"`.
- `variants=true` est refusé avec `field="file"`.
- Les booléens `variants`, `multiple` et `required` ne peuvent pas être de simples entiers.

### Convention de rôles

| Rôle | Signification | État |
|---|---|---|
| `cover` | Image principale de l'entité | Géré par `make:crud` |
| `gallery` | Galerie d'images | Réservé — non géré comme galerie CRUD |
| `brochure` | Document PDF ou fichier joint | Géré par `make:crud` |

D'autres rôles peuvent être définis librement. Le rôle est une chaîne non vide, unique dans l'entité. `gallery` est réservé par convention à un usage futur de galerie multiple ; `make:crud` traite tout rôle de la même façon pour `multiple=false`.

### Champs SQL vs médias

Les `fields` d'une entité correspondent à des colonnes SQL dans la table métier (`hebergement.nom`, etc.). Les entrées `media` ne correspondent à **aucune colonne** — elles sont stockées dans la table `media` séparée, liées à l'entité via `entity_name`/`entity_id`. Cette séparation permet d'attacher plusieurs médias à un même enregistrement sans modifier le schéma métier.

### Ce que cette déclaration ne fait pas

- Elle n'ajoute aucune colonne à la table métier.
- Elle ne génère pas de route dédiée à la gestion des médias.

### Galerie en lecture (multiple=true)

Depuis Forge 1.3.0, les médias déclarés `multiple=true` peuvent être affichés en galerie et recevoir de nouveaux médias depuis le CRUD généré.

**Lecture :** `make:crud` appelle `list_media_for_entity(entity_name, entity_id, role=...)` dans `show()`, `edit()` et `update()` invalide, et transmet la liste sous la variable de contexte `{name}_media_list`. Les templates `show.html` et `form.html` affichent cette liste en lecture seule (miniatures ou liens).

**Ajout (append-only, multi-upload) :** le formulaire `form.html` inclut un `<input type="file" multiple>` pour chaque champ `multiple=true`. Plusieurs fichiers peuvent être sélectionnés en une seule soumission. En `create()` et `update()` valides, chaque fichier soumis est validé individuellement (extension, taille, MIME) avant toute opération en base — un seul fichier invalide bloque la soumission complète. Les fichiers valides sont sauvegardés et attachés à la galerie. Le comportement est **append-only** : Forge ajoute les nouveaux médias sans remplacer ni réordonner les médias existants.

**Suppression individuelle :** le formulaire `form.html` affiche les miniatures existantes avec une checkbox par item (`name="_delete_media_{name}"`, `value="{{ _m.id }}"`). En `update()` valide, Forge supprime chaque média coché avant l'éventuel ajout. La suppression est irréversible (`delete_files=True`). Les médias non cochés ne sont pas touchés. En cas de formulaire invalide, aucune suppression n'est effectuée.

```python
# Flux généré dans update() pour un champ multiple=true :
# 1. Validation préalable (chaque fichier avant toute opération DB)
_photos_files_raw = request.files.get("photos", [])
_photos_files = _photos_files_raw if isinstance(_photos_files_raw, list) else ([_photos_files_raw] if _photos_files_raw else [])
for _photos_f in _photos_files:
    if getattr(_photos_f, "filename", ""):
        try:
            form.fields["photos"].validate(_photos_f)
        except Exception as _photos_exc:
            form.add_error("photos", getattr(_photos_exc, "messages", [str(_photos_exc)]))
            return BaseController.validation_error(...)
# 2. Suppressions cochées
_photos_del_ids = request.body.get("_delete_media_photos", [])
for _did in _photos_del_ids:
    delete_media(int(_did), delete_files=True, variants=True)
# 3. Upload de chaque fichier soumis
for _photos_f in _photos_files:
    if getattr(_photos_f, "filename", ""):
        _saved_photos = save_upload(_photos_f, "images", variants=False)
        attach_media_to_entity(_saved_photos, entity_name="article", entity_id=id,
                               role="gallery", position=0)
```

Les galeries `multiple=true` peuvent être affichées, enrichies (multi-upload), nettoyées par suppression individuelle et réordonnées par position numérique depuis le CRUD généré. L'ordre d'affichage repose sur `Position ASC` puis `Id ASC`. Le drag-and-drop reste un ticket séparé.

### Position des médias

Les médias peuvent porter une position numérique optionnelle. Elle sert à stabiliser l'ordre d'affichage des galeries. Forge ne fournit pas encore d'interface de réorganisation dans ce ticket : le drag-and-drop et la modification manuelle de l'ordre seront traités séparément.

La colonne `Position INT NOT NULL DEFAULT 0` est présente dans la table `media`. `list_media_for_entity` trie systématiquement par `Position ASC, Id ASC`. `attach_media_to_entity` accepte `position=None` (traité comme `0`) et `position=<entier>` ; les appels sans argument continuent de fonctionner.

### Intégration dans make:crud

Quand une entité déclare des médias, `make:crud` génère automatiquement :

- Un `ImageField` ou `FileField` dans le formulaire pour chaque entrée `media`.
- L'attribut `enctype="multipart/form-data"` sur la balise `<form>` du template.
- Un `<input type="file">` avec `accept="image/*"` pour les images dans la vue.
- Dans le contrôleur `create` : `save_upload()` puis `attach_media_to_entity()` si un fichier est soumis.
- Dans le contrôleur `update` (pour `multiple=false`) :
  - Si un nouveau fichier est soumis : l'ancien média est supprimé (`delete_media(..., delete_files=True)`) puis le nouveau est attaché.
  - Si la case `_delete_media_<name>` est cochée sans nouveau fichier : l'ancien média est supprimé.
  - Si ni nouveau fichier ni suppression cochée : le média existant est conservé.
  - `_delete_media_*` est lu depuis `request.body` ; ces clés ne sont jamais écrites dans la table métier.
- Dans les contrôleurs `show` et `edit` (pour `multiple=false`) : `get_cover_media(entity_name, entity_id, role=...)` est appelé pour chaque entrée et passé au contexte du template.
- Dans `show.html` : chaque image est affichée avec `thumbnail_url or url` ; chaque fichier avec un lien.
- Dans `form.html` : le média existant est affiché avant le champ upload avec une case à cocher "Supprimer le média actuel" ; cocher remplace ou supprime selon qu'un nouveau fichier est aussi soumis.

Les champs média sont toujours exclus des données SQL métier (ni à la création ni à l'édition).

### Flux complet Média v2

Avec l'entité ci-dessous, `make:crud` génère la chaîne complète.

```json
{
  "format_version": 1,
  "entity": "Hebergement",
  "table": "hebergement",
  "fields": [
    { "name": "id", "sql_type": "INT", "primary_key": true, "auto_increment": true },
    { "name": "nom", "sql_type": "VARCHAR(120)", "constraints": { "not_empty": true } }
  ],
  "media": [
    {
      "name": "cover",
      "field": "image",
      "role": "cover",
      "variants": true,
      "multiple": false,
      "required": false,
      "label": "Image principale"
    },
    {
      "name": "brochure",
      "field": "file",
      "role": "brochure",
      "variants": false,
      "multiple": false,
      "required": false,
      "label": "Brochure PDF"
    }
  ]
}
```

**Formulaire généré** :
- `ImageField` pour `cover`, `FileField` pour `brochure`.
- `enctype="multipart/form-data"` sur le `<form>`.
- `accept="image/*"` sur l'input `cover`.

**Contrôleur `create`** :
- Exclut `cover` et `brochure` de l'insert SQL.
- Capture `cursor.lastrowid` pour obtenir l'id créé.
- Si `cover` soumis : `save_upload(file, "images", variants=True)` → `attach_media_to_entity(saved, entity_name="hebergement", entity_id=id, role="cover", position=0)`.
- Si `brochure` soumis : `save_upload(file, "documents", variants=False)` → `attach_media_to_entity(...)`.

**Contrôleur `edit/update`** :
- Charge `cover_media = get_cover_media("hebergement", id, role="cover")` et `brochure_media = get_cover_media("hebergement", id, role="brochure")`.
- Affiche chaque média dans le formulaire avec miniature (image) ou lien (fichier).
- Case à cocher `_delete_media_cover` / `_delete_media_brochure` si un média existe.
- Si case cochée ou nouveau fichier → supprime l'ancien via `delete_media`.
- Si nouveau fichier → attache le nouveau.

**Vue `show`** :
- `cover_media.thumbnail_url or cover_media.url` dans une `<img>`.
- `brochure_media.url` dans un `<a>`.

**Stockage** :
- Fichiers dans `storage/uploads/images/` (+ variantes `thumbnail/`, `medium/`) et `storage/uploads/documents/`.
- Ligne dans la table `media` avec `entity_name="hebergement"`, `entity_id`, `role`, `path`.

---

## État de Média v2

### Ce qui fonctionne

- Déclaration `media` dans `entity.json` validée et normalisée.
- Génération CRUD complète : formulaire, contrôleur, vues.
- Upload à la création avec `save_upload` + `attach_media_to_entity`.
- Remplacement à l'édition avec `list_media_for_entity` + `delete_media`.
- Suppression explicite via checkbox `_delete_media_<name>`.
- Suppression des médias liés lors du destroy de l'entité (Forge 1.3.0+).
- Preview dans `show.html` et `form.html` avec `get_cover_media`.
- Variantes `thumbnail`/`medium` pour les images si `variants=true`.
- Route `/media/<chemin>` pour servir les fichiers.

### Limites actuelles

- `multiple=true` : ajout append-only (multi-upload), suppression individuelle et réorganisation par position supportés (Forge 1.3.0+).
- Les médias existants ne sont pas pré-remplis dans le champ upload (comportement normal des navigateurs).
- Pas de back-office média intégré.
- La détection MIME repose sur le `Content-Type` déclaré par le navigateur (`python-magic` non inclus).
- Aucune permission média : tout fichier servi via `/media/...` est accessible sans authentification.

---

## Garanties de sécurité

Les garanties suivantes sont assurées par `core/uploads/storage.py` et s'appliquent
à l'ensemble du module `forge-mvc-media` qui délègue toutes les opérations sur les chemins à ce core.

| Menace | Garantie | Mécanisme |
|---|---|---|
| **Path traversal** (`../`) | Bloqué | `posixpath.normpath` + rejet des composants `..` |
| **Chemins absolus Unix** (`/...`) | Bloqué | Rejet si le chemin commence par `/` après nettoyage |
| **Chemins Windows** (`\...`, `C:\`) | Normalisé puis bloqué | `\\` → `/`, puis règle chemins absolus |
| **URI schemes** (`file://`, `http://`) | Bloqué | Expression régulière sur les schémas URI |
| **Null bytes** (`\x00`) | Bloqué | Rejet explicite avant toute opération |
| **Chemins relatifs hors racine** | Bloqué | `os.path.commonpath` vérifie que la cible reste sous `storage/uploads/` |
| **Stockage absolu** | Impossible | `normalize_media_path` retourne toujours un chemin relatif |
| **Suppression accidentelle** | Opt-in uniquement | `delete_media(id, delete_files=False)` par défaut — la suppression fichier est explicite |
| **Validation MIME/extension** | Présente | `core/uploads/validators.py` valide contre des listes d'extensions et MIME autorisées |
| **Exposition hors racine** | Impossible | La route `/media/...` refuse tout chemin sortant de `storage/uploads/` |
| **Double slash / normpath** | Nettoyé | `//` réduits avant normalisation |

Ces garanties couvrent le code source audité en `{{forge_version}}`. Elles ne couvrent pas la
détection MIME côté serveur (repose sur le `Content-Type` déclaré par le navigateur ;
`python-magic` est hors périmètre) ni les permissions d'accès aux médias servis.

## Conditions avant publication PyPI

Ces conditions doivent toutes être remplies avant de retirer le classifier
`"Private :: Do Not Upload"` et de publier sur PyPI :

| Condition | Ticket | État |
|---|---|---|
| Documentation publique du module | `MEDIA-DOCS-MIGRATION-001` | livré |
| Suppression des shims `core/uploads/media_repository.py` et `media_gallery.py` | `MEDIA-SHIMS-REMOVE-001` | livré |
| Passage à `Development Status :: 3 - Alpha` minimum | `MEDIA-PYPI-READY-002` | livré |
| Classifier `"Private :: Do Not Upload"` retiré | `MEDIA-PYPI-READY-002` | livré |

Tant que ces conditions ne sont pas toutes validées, **ne pas relancer**
`PYPI-PUBLISH-B7-MEDIA-001` ni aucune variante de publication PyPI pour ce module.

La publication PyPI sera traitée dans `PYPI-PUBLISH-MEDIA-001`
(ou `PYPI-PUBLISH-B8-MEDIA-001` selon la version cible au moment de la publication).

## Roadmap

- `MEDIA-SHIMS-REMOVE-001` — shims de compatibilité supprimés de `core/uploads/` (livré).
- `MEDIA-PYPI-READY-002` — requalifier en Alpha, retirer le classifier, préparer la publication PyPI.
- Détection MIME fiable via `python-magic`.
- Permissions et accès contrôlés aux médias.
