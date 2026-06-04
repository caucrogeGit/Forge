# forge-mvc-images

Module **opt-in** propriétaire de tout l'image dans Forge MVC : traitement
(variantes, miniatures, validation de contenu — Pillow) **et** couche médias
applicative (repository, galerie, couverture).

## Statut : squelette — `IMAGES-PKG-SCAFFOLD-001`

À ce stade, `forge-mvc-images` est un **squelette source-only** : le
`pyproject.toml` déclare la dépendance Pillow et `forge_mvc_images/__init__.py`
expose `__version__`, mais **aucune logique n'a encore été déplacée**. Le
traitement d'image vit toujours dans `core/uploads/image.py` et la couche
applicative dans `forge-mvc-media` ; ils seront rapatriés par les tickets
suivants (voir ADR-018).

Ce paquet **n'est pas encore publié sur PyPI**.

## Pourquoi ce module (ADR-018)

`forge-mvc-images` **remplace** `forge-mvc-media`. Le nom « media » était
trompeur depuis l'arrivée de `forge-mvc-video` (un développeur attendait que
`forge-mvc-media` gère aussi la vidéo). Par ailleurs, embarquer Pillow et le
traitement d'image dans le core contredit le principe de **noyau minimal**
(charte principe 8, ADR-004).

Décision (option B — « renommer + rapatrier ») :

- le **core** ne garde que l'**upload brut générique** (`save_upload` sans le
  cas `images`, `save_bytes`, validation, storage, rate-limit) ;
- `forge-mvc-images` devient l'**unique** propriétaire de tout l'image —
  traitement **et** couche applicative.

Conformément à la **convention pré-1.0** (pas d'utilisateurs externes), le
renommage se fait **sans alias déprécié ni guide de migration** : `forge-mvc-media`
sera supprimé une fois le rapatriement terminé.

## Plan d'exécution (ADR-018)

| Ticket | Description | État |
|---|---|---|
| `IMAGES-PKG-SCAFFOLD-001` | Squelette du paquet (`pyproject.toml` + Pillow, `__init__`) | livré |
| `IMAGES-MOVE-PROCESSING-001` | Déplacer le traitement image du core ; rendre `save_upload` générique | à venir |
| `IMAGES-MOVE-APPLICATIVE-001` | Déplacer repository + galerie depuis `forge-mvc-media` | à venir |
| `CORE-DROP-PILLOW-001` | Retrait de Pillow du core, inversion des garde-fous packaging | à venir |
| `CLI-CRUD-IMAGES-RENAME-001` | Générateurs CLI → `forge_mvc_images` | à venir |
| `CI-DOCS-IMAGES-RENAME-001` | CI, README racine, docs, CONTRIBUTING | à venir |
| `REMOVE-MEDIA-PKG-001` | Suppression de `packages/forge-mvc-media` | à venir |

## Installation (mode éditable, depuis les sources)

```bash
git clone https://github.com/caucrogeGit/Forge.git
cd Forge
pip install -e packages/forge-mvc-images/
```

## Référence

- `docs/adr/018-image-module-extraction.md` — décision et périmètre figés.
- Charte principes 8 (noyau minimal), 11 (une seule façon officielle).
