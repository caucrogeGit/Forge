# Slugs

Un **slug** est un identifiant URL-safe lisible (`/articles/premier-contact`
plutôt que `/articles/42`). Forge en fait un **type de champ de premier rang**,
généré depuis un champ source, avec une colonne `VARCHAR(180) UNIQUE` et une
validation officielle. Décision : [ADR-017](../adr/017-slug-type.md).

---

## Déclarer un champ slug

Dans le JSON canonique de l'entité, un slug **auto-généré** depuis un champ
source :

```json
{
  "name": "Article",
  "table": "article",
  "fields": [
    { "name": "titre", "type": "string", "max_length": 200, "required": true },
    { "name": "slug",  "type": "slug",   "unique": true, "source": "titre" }
  ]
}
```

| Clé | Rôle |
|---|---|
| `"type": "slug"` | colonne `VARCHAR(180)`, widget de formulaire `SlugField` |
| `"unique": true` | contrainte SQL `UNIQUE` (recommandé) — garantit l'absence de doublon |
| `"source": "titre"` | le slug est **généré depuis ce champ** (doit exister dans l'entité) |

---

## Comportement généré (`forge make:crud`)

Avec un `source`, le slug est **auto-généré** — l'utilisateur ne le saisit
jamais :

- **Formulaire** : le champ slug est **absent** (on saisit `titre`).
- **Création** : le contrôleur calcule `slug = slugify(titre)` via le module
  canonique `core.http.slug` (accents translittérés, espaces → tirets,
  minuscules) : « Écrire avec Forge ! » → `ecrire-avec-forge`.
- **Édition** : le slug est **stable** — il n'est pas régénéré quand le titre
  change (les URLs publiques ne se cassent pas). Il est exclu de l'`UPDATE`.
- **Unicité** : la contrainte `UNIQUE` garantit qu'aucun doublon n'est stocké.

### Sans `source` (saisie manuelle)

Un champ `{"type": "slug"}` **sans** `source` est saisi à la main dans le
formulaire et validé par `SlugField` (`core.http.slug.is_valid_slug` :
minuscules, chiffres, tirets internes, path-safe).

---

## Routing public par slug

Le modèle généré expose un lookup `get_<entité>_by_<slug>()`. La route reste
**écrite explicitement** par vous (philosophie Forge — pas de magie cachée) :

```python
# mvc/routes.py
with router.group("", public=True) as public:
    public.add("GET", "/articles/{slug}", ArticleController.show_public, name="article_public")
```

```python
# mvc/controllers/article_controller.py
slug = request.route_params.get("slug")
article = get_article_by_slug(slug)
```

---

## Limites (b13)

Reportées **après 1.0** (voir ADR-017) :

- pas de **suffixe automatique** (`mon-article-2`) en cas de collision — un
  doublon est rejeté ; choisissez un titre différent ;
- pas d'**historique des slugs** (`slug_history`) ni de **redirection 301** ;
- pas de slugs multilingues, ni de sitemap.

---

## Voir aussi

- [Types Forge → MariaDB](types-forge-mariadb.md)
- [ADR-017 — Type slug et module URL-slug canonique](../adr/017-slug-type.md)
- Module runtime : `core.http.slug.slugify` / `core.http.slug.is_valid_slug`.
