# Les slugs d'URL dans Forge

Ce document décrit le module canonique de génération et de validation de slugs d'URL.

Le fichier de code correspondant est `core/http/slug.py`.

## 1. À quoi sert ce module ?

Un slug est la forme d'un texte adaptée à une URL : minuscules, sans accent, mots séparés par des tirets.
Ce module est le point **canonique** de Forge pour produire et valider un slug (ADR-017).

## 2. L'API

```python
from core.http.slug import slugify, is_valid_slug

slugify("Bonjour le Monde !")   # "bonjour-le-monde"
is_valid_slug("bonjour-le-monde")   # True
```

| Fonction | Rôle |
|---|---|
| `slugify(text, *, max_length=180)` | dérive un slug d'URL depuis un texte libre |
| `is_valid_slug(value, *, max_length=180)` | indique si `value` est un slug valide |

## 3. Le contrat

`slugify` est **idempotent** : `slugify(slugify(x)) == slugify(x)`.
La longueur est bornée par `max_length` ; le type `slug` des entités s'appuie sur ce module (ADR-017).

## 4. Contextes d'utilisation

- **Type `slug` d'entité** : génération automatique depuis un champ source.
- **Routes lisibles** : produire un segment d'URL propre.

## 5. Voir aussi

- [Le routeur](router.md) : les motifs de route qui consomment les slugs.
