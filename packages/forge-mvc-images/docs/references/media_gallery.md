# La galerie de médias dans Forge

Ce document décrit les helpers de lecture pour afficher la couverture et la galerie d'une entité.

Le fichier de code correspondant est `forge_mvc_images/media_gallery.py`.

## 1. À quoi sert ce module ?

Là où le [dépôt](media_repository.md) écrit et liste les médias, la **galerie** offre des lectures prêtes pour l'affichage : l'image de couverture d'une entité, sa galerie ordonnée, et l'URL publique d'un média.

C'est la couche que les vues consomment.

## 2. L'API

| Fonction | Rôle |
|---|---|
| `get_cover_media(entity_name, entity_id, *, role="cover", fallback_to_gallery=False)` | le média de couverture d'une entité, ou `None` |
| `get_media_gallery(entity_name, entity_id, *, role="gallery")` | la galerie ordonnée d'une entité |
| `media_url(path)` | l'URL publique d'un chemin media |

`get_cover_media` peut **retomber sur la galerie** (`fallback_to_gallery=True`) quand aucune couverture explicite n'est définie : on affiche alors la première image disponible.

## 3. Usage dans une vue

```python
cover = get_cover_media("article", article_id, fallback_to_gallery=True)
gallery = get_media_gallery("article", article_id)
```

```html
{% if cover %}<img src="{{ media_url(cover.path) }}" alt="{{ cover.alt_text }}">{% endif %}
```

## 4. Contextes d'utilisation

- **Vignette de liste** : `get_cover_media(..., fallback_to_gallery=True)`.
- **Page de détail** : `get_media_gallery(...)` pour la galerie complète.
- **Lien d'image** : `media_url(path)` dans le gabarit.

## 5. Voir aussi

- [Le dépôt de médias](media_repository.md) : la source des données lues ici.
- [Le traitement d'image](processing.md) : génération des variantes affichées.
