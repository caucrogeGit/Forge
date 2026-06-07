# Héritage de gabarit

Objectif : factoriser l'enveloppe HTML commune (en-tête, pied, `<head>`) dans un
**gabarit** partagé, au lieu de la répéter dans chaque page.

**Ce que vous allez apprendre :** une page peut **hériter** d'un gabarit avec
`{% extends %}` et n'y injecter que son contenu via des `{% block %}`. C'est le
principe DRY appliqué aux templates Jinja.

Palier 4 du **niveau intermédiaire** de la
[progression officielle des starters](../../index.md#progression-recommandee),
après [Paginer une liste](pagination.md).

## Ce que ce starter montre

- un **gabarit** `layouts/starter_layout.html` avec des `{% block %}` ;
- une page qui l'`{% extends %}` et ne définit que son contenu ;
- la fin des documents HTML complets dupliqués page après page.

Aucune base de données. Aucune écriture.

## Classes Forge utilisées

| Classe | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `Request` | Reçue par la méthode du contrôleur. | [Request](../../../reference/http.md#3-request-reference) |
| `Response` | Produite via `render(...)`. | [Response](../../../reference/http.md#4-response-reference) |
| `BaseController` | Fournit `render(...)`. | [BaseController](../../../reference/api.md#coremvccontroller) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/layout-template` → la page affiche son contenu
**dans** l'en-tête et le pied définis par le gabarit partagé.

## Le gabarit

```html
<!-- mvc/views/layouts/starter_layout.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{% block title %}Forge{% endblock %}</title>
</head>
<body>
  <header><strong>Mon application Forge</strong></header>
  <main>
    {% block content %}{% endblock %}
  </main>
  <footer><small>Pied de page commun à toutes les pages.</small></footer>
</body>
</html>
```

## La page

```html
<!-- mvc/views/layout_template/index.html -->
{% extends "layouts/starter_layout.html" %}

{% block title %}{{ titre }} - Forge{% endblock %}

{% block content %}
<h1>{{ titre }}</h1>
<p>Cette page ne contient que son contenu propre.</p>
{% endblock %}
```

### Comprendre ce code

- `{% extends "layouts/starter_layout.html" %}` déclare que la page **hérite**
  du gabarit ; elle n'écrit plus `<html>`, `<head>` ni `<body>`.
- Chaque `{% block X %}…{% endblock %}` de la page **remplit** le bloc de même
  nom déclaré dans le gabarit (`title`, `content`).
- Le gabarit reste **un seul fichier** : modifier l'en-tête ou le pied le
  change pour toutes les pages qui en héritent.

## À retenir

- `{% extends %}` + `{% block %}` = factoriser l'enveloppe HTML.
- Le gabarit définit la structure et des blocs ; la page remplit les blocs.
- Une seule source pour l'en-tête/pied → cohérence et maintenance simples.

## Après ce starter

Passez au palier suivant : **Modifier un enregistrement**, éditer une ligne
existante via un formulaire pré-rempli.

[Continuer avec Modifier un enregistrement](update-record.md)
