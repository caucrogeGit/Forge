# L'inspection de debug dans Forge

Ce document décrit le rendu HTML lisible d'un objet, utilisé par `Response.debug`.

Le fichier de code correspondant est `core/http/debug_dumper.py`.

## 1. À quoi sert ce module ?

En développement, on veut inspecter un objet (souvent la requête) sous une forme lisible.
Ce module produit une **vue HTML** d'un objet quelconque, employée par `Response.debug(obj)`.

## 2. L'API

```python
from core.http.debug_dumper import render_debug_html

html = render_debug_html(obj)
```

| Fonction | Rôle |
|---|---|
| `render_debug_html(obj)` | retourne une représentation HTML lisible de `obj` |

## 3. Sécurité

L'inspection est destinée au **développement**. Côté requête, les valeurs sensibles sont masquées en amont (voir `request.data`) avant d'arriver ici : le dumper rend ce qu'on lui donne.

## 4. Contextes d'utilisation

- **Debug** : `Response.debug(request)` dans une vue, en développement.

## 5. Voir aussi

- [L'objet Request](request.md) : `request.data`, la vue sûre inspectée.
- [L'objet Response](response.md) : `Response.debug` qui appelle ce rendu.
