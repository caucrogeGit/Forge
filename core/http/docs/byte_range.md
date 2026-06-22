# L'en-tête Range dans Forge

Ce document décrit le parsing de l'en-tête HTTP `Range`, utilisé pour la lecture partielle (streaming, seek).

Le fichier de code correspondant est `core/http/byte_range.py`.

## 1. À quoi sert ce module ?

Quand un client veut une **portion** d'un fichier (par exemple un lecteur vidéo qui avance dans la piste), il envoie un en-tête `Range: bytes=...`.
Ce module parse cet en-tête en un intervalle d'octets exploitable.

C'est la brique sur laquelle `Response.file` s'appuie pour servir du contenu en streaming avec seek.

## 2. L'API

```python
from core.http.byte_range import parse_byte_range

spec = parse_byte_range(request.header("Range"), file_size)
```

| Élément | Rôle |
|---|---|
| `parse_byte_range(range_header, file_size)` | parse l'en-tête `Range` ; retourne un `RangeSpec`, ou `None` si absent |
| `RangeSpec(satisfiable, start, end)` | l'intervalle résolu : bornes `start`/`end` et drapeau `satisfiable` |

Un `RangeSpec` non `satisfiable` signale une plage hors limites (le serveur répond alors `416`).

## 3. Contextes d'utilisation

- **Service de fichiers** : sous-jacent à `Response.file` pour le streaming et le seek.
- **Lecture média** : vidéo, audio (lecture partielle).

## 4. Voir aussi

- [L'objet Response](response.md) : `Response.file` consomme ce parsing.
