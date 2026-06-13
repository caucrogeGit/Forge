# ADR-032 : Périmètre de la configuration upload (seul `upload_max_size` est du core)

## Statut

Acceptée (mise en œuvre à suivre, ticket `UPLOAD-CONFIG-DECOUPLE-001`).

Complète [ADR-031](031-mail-core-decoupling.md) (même patron de découplage),
prolonge [ADR-019](019-upload-extraction.md) / [ADR-020](020-files-media-storage-primitives.md)
(extraction de l'upload) et renforce [ADR-004](004-core-perimeter.md) ainsi que
le principe 8 (noyau minimal, briques opt-in).

---

## Contexte

Le squelette nu (`env/example`) porte un bloc upload de quatre variables, et le
registre `core.forge` déclare une cinquième clé :

```text
UPLOAD_MAX_SIZE, UPLOAD_ROOT, UPLOAD_ALLOWED_EXTENSIONS, UPLOAD_ALLOWED_MIME_TYPES
(+ upload_max_image_pixels, défaut codé en dur dans core/forge.py, hors env)
```

Examen précis des consommateurs réels :

| Clé | Lue par | Le core la consomme ? |
|---|---|---|
| `upload_max_size` | `core/http/request.py` (borne le corps multipart) | **oui** |
| `upload_root` | `forge-mvc-files` uniquement | non |
| `upload_allowed_extensions` | `forge-mvc-files` uniquement | non |
| `upload_allowed_mime_types` | `forge-mvc-files` uniquement | non |
| `upload_max_image_pixels` | `forge-mvc-images` uniquement | non |

Point décisif : le `FileField` du core (`core/forms/fields.py`) prend
`allowed_extensions`, `max_size`, `allowed_mime_types` **en paramètres**
(défaut `None`) et ne valide que si on les lui passe. Il **ne lit jamais** le
registre. La validation par champ est donc explicite côté application, et les
clés `upload_allowed_*` du registre ne servent qu'au flux de sauvegarde de
`forge-mvc-files`.

Conséquence : dans un projet **nu** (sans opt-in), quatre des cinq variables ne
sont lues par rien. Leur présence dans `env/example` laisse croire que l'upload
est géré et configuré, alors que le **stockage/service** relève de
`forge-mvc-files` (ADR-019/020) et la **validation par champ** est explicite.
C'est de la connaissance d'opt-in qui fuite dans le noyau et le squelette nu.

`upload_max_size` est différent : le noyau lit cette valeur pour décider combien
d'octets il accepte sur une requête multipart, **avant tout opt-in**. C'est un
contrôle anti-DoS intrinsèque à la couche HTTP. On ne peut pas rendre le core
ignorant d'une limite de corps multipart, puisque c'est lui qui lit les octets.

---

## Décision

**Seul `upload_max_size` reste un réglage du core. Les quatre autres clés upload
quittent le noyau et le squelette nu, vers les opt-ins qui les consomment.**

| Clé | Avant | Après |
|---|---|---|
| `upload_max_size` | core registre + `env/example` | **inchangé** (contrôle HTTP du noyau) |
| `upload_root` | core registre + `env/example` | lu par `forge-mvc-files` via `os.getenv` (défaut `storage/uploads`) |
| `upload_allowed_extensions` | core registre + `env/example` | idem `forge-mvc-files` (défaut sobre) |
| `upload_allowed_mime_types` | core registre + `env/example` | idem `forge-mvc-files` |
| `upload_max_image_pixels` | core registre (hors env) | lu par `forge-mvc-images` via `os.getenv("UPLOAD_MAX_IMAGE_PIXELS")` (défaut `24000000`) |

`forge-mvc-files` continue de lire `upload_max_size` depuis `core.forge.get`
(valeur légitimement détenue par le noyau), mais lit ses propres clés
(`upload_root`, extensions, MIME) depuis l'environnement.

---

## Conséquences

**Positives :**

- Le noyau ne déclare plus de config de stockage/validation d'upload qu'il ne
  consomme pas ; il ne garde que la limite de corps multipart, qui lui revient.
- Le projet nu ne porte plus de variables trompeuses suggérant un upload
  « géré » alors qu'aucun opt-in n'est installé.
- `forge-mvc-files` et `forge-mvc-images` possèdent leur configuration.
- `upload_max_image_pixels` devient **réellement configurable** via
  l'environnement (aujourd'hui la docstring le prétend, à tort : aucune variable
  d'env n'existe).

**À assumer :**

- Rupture interne pré-1.0 de `core.forge.configure` (retrait des kwargs
  `upload_root`, `upload_allowed_extensions`, `upload_allowed_mime_types`,
  `upload_max_image_pixels`). Pas d'alias, à signaler au `CHANGELOG.md`.
- `forge doctor` : le check `check_prod_security` lit `UPLOAD_ALLOWED_EXTENSIONS`
  pour avertir d'uploads non restreints. Dans un projet nu sans `forge-mvc-files`,
  ce contrôle perd son sens et doit être **conditionné à la présence de l'opt-in**.
- Provisioning : le bloc d'upload de `forge-mvc-files` (et la variable image de
  `forge-mvc-images`) est documenté **par l'opt-in**, ajouté à `env/dev` à
  l'installation, jamais écrit silencieusement (principe 9).

---

## Mise en œuvre (ticket `UPLOAD-CONFIG-DECOUPLE-001`)

1. Gardes d'abord : `upload_root` / `upload_allowed_*` / `upload_max_image_pixels`
   absents de `core/forge.py` ; projet nu sans ces variables ; `upload_max_size`
   conservé partout.
2. `forge-mvc-files` : lecture `os.getenv` pour `upload_root`,
   `upload_allowed_extensions`, `upload_allowed_mime_types` (défauts propres) ;
   continue de lire `upload_max_size` depuis le core.
3. `forge-mvc-images` : `os.getenv("UPLOAD_MAX_IMAGE_PIXELS", "24000000")` ;
   idem le starter `image-safety`.
4. Core : retirer les quatre slots de `core/forge.py` (garder `upload_max_size`)
   et `upload_root` de `_PATH_KEYS` ; retirer le threading correspondant de
   `core/app/app_factory.py` (garder `upload_max_size`).
5. Squelette nu + dogfood racine : retirer `UPLOAD_ROOT`,
   `UPLOAD_ALLOWED_EXTENSIONS`, `UPLOAD_ALLOWED_MIME_TYPES` de `env/example`,
   `config.py`, `app.py` (garder `UPLOAD_MAX_SIZE`).
6. `forge doctor` : conditionner le check upload-restreint à la présence de
   `forge-mvc-files`.
7. Documentation : `docs/features/media.md` / doc files et images documentent le
   bloc env à ajouter ; mise à jour des parcours welcome concernés.

**Validations :**

```bash
python -m pytest -x -q
python -m compileall -q .
ruff check .
mkdocs build --strict
git diff --check
```

---

## Alternatives rejetées

**Découpler aussi `upload_max_size`.** Rejetée : le noyau lit cette valeur dans
`core/http/request.py` pour borner le corps d'une requête multipart, avant tout
opt-in. C'est le parseur du core qui lit les octets, il doit donc connaître le
plafond. Un opt-in ne peut pas s'injecter dans le parsing. Le seul découplage
possible serait un renommage cosmétique (`max_multipart_body_size`), sans gain
réel et au prix de la lisibilité de `UPLOAD_MAX_SIZE`.

**Conserver les cinq clés dans le core comme un « contrat upload ».** Rejetée :
c'est le même argument « le core déclare, l'opt-in applique » écarté pour le mail
(ADR-031). Quatre des cinq clés n'ont aucun consommateur dans le core.

---

## Charte appliquée

Principe 3 (refuser la magie cachée), principe 4 / ADR-004 (périmètre du core),
principe 8 (noyau minimal), principe 9 (provisioning sans écriture invisible),
principe 10 (API publique claire).
